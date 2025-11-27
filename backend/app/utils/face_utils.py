"""人脸工具模块 - 实现人脸检测、特征提取、特征比对等核心功能"""
import math
import numpy as np
from PIL import Image
from mtcnn import MTCNN
from facenet_pytorch import InceptionResnetV1
import torch
import torch.nn as nn
import torch.nn.functional as F
import cv2


# 初始化MTCNN人脸检测器 - 优化参数以提高检测率并修复区域选择错误
mtcnn = MTCNN(
    min_face_size=15,  # 降低最小人脸大小以检测更远距离或更小的人脸
    steps_threshold=[0.6, 0.7, 0.75],  # 调整阈值以提高准确性，减少误判
    scale_factor=0.7  # 调整缩放因子以更好地处理不同大小的人脸，提高区域选择精度
)


# 初始化FaceNet特征提取模型（预训练模型）
# 加载预训练的InceptionResnetV1模型，设置为评估模式
resnet = InceptionResnetV1(pretrained='vggface2').eval()


#------------------------------------------------------------------------------
#  MODNet Basic Modules
#------------------------------------------------------------------------------

class IBNorm(nn.Module):
    """ Combine Instance Norm and Batch Norm into One Layer
    """

    def __init__(self, in_channels):
        super(IBNorm, self).__init__()
        in_channels = in_channels
        self.bnorm_channels = int(in_channels / 2)
        self.inorm_channels = in_channels - self.bnorm_channels

        self.bnorm = nn.BatchNorm2d(self.bnorm_channels, affine=True)
        self.inorm = nn.InstanceNorm2d(self.inorm_channels, affine=False)
        
    def forward(self, x):
        bn_x = self.bnorm(x[:, :self.bnorm_channels, ...].contiguous())
        in_x = self.inorm(x[:, self.bnorm_channels:, ...].contiguous())

        return torch.cat((bn_x, in_x), 1)


class Conv2dIBNormRelu(nn.Module):
    """ Convolution + IBNorm + ReLu
    """

    def __init__(self, in_channels, out_channels, kernel_size, 
                 stride=1, padding=0, dilation=1, groups=1, bias=True, 
                 with_ibn=True, with_relu=True):
        super(Conv2dIBNormRelu, self).__init__()

        layers = [
            nn.Conv2d(in_channels, out_channels, kernel_size, 
                      stride=stride, padding=padding, dilation=dilation, 
                      groups=groups, bias=bias)
        ]

        if with_ibn:       
            layers.append(IBNorm(out_channels))
        if with_relu:
            layers.append(nn.ReLU(inplace=True))

        self.layers = nn.Sequential(*layers)

    def forward(self, x):
        return self.layers(x) 


class SEBlock(nn.Module):
    """ SE Block Proposed in https://arxiv.org/pdf/1709.01507.pdf 
    """

    def __init__(self, in_channels, out_channels, reduction=1):
        super(SEBlock, self).__init__()
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(in_channels, int(in_channels // reduction), bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(int(in_channels // reduction), out_channels, bias=False),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        b, c, _, _ = x.size()
        w = self.pool(x).view(b, c)
        w = self.fc(w).view(b, c, 1, 1)

        return x * w.expand_as(x)


#------------------------------------------------------------------------------
#  MobileNetV2 Backbone
#------------------------------------------------------------------------------

def _make_divisible(v, divisor, min_value=None):
    if min_value is None:
        min_value = divisor
    new_v = max(min_value, int(v + divisor / 2) // divisor * divisor)
    if new_v < 0.9 * v:
        new_v += divisor
    return new_v


def conv_bn(inp, oup, stride):
    return nn.Sequential(
        nn.Conv2d(inp, oup, 3, stride, 1, bias=False),
        nn.BatchNorm2d(oup),
        nn.ReLU6(inplace=True)
    )


def conv_1x1_bn(inp, oup):
    return nn.Sequential(
        nn.Conv2d(inp, oup, 1, 1, 0, bias=False),
        nn.BatchNorm2d(oup),
        nn.ReLU6(inplace=True)
    )


class InvertedResidual(nn.Module):
    def __init__(self, inp, oup, stride, expansion, dilation=1):
        super(InvertedResidual, self).__init__()
        self.stride = stride
        assert stride in [1, 2]

        hidden_dim = round(inp * expansion)
        self.use_res_connect = self.stride == 1 and inp == oup

        if expansion == 1:
            self.conv = nn.Sequential(
                # dw
                nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, dilation=dilation, bias=False),
                nn.BatchNorm2d(hidden_dim),
                nn.ReLU6(inplace=True),
                # pw-linear
                nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False),
                nn.BatchNorm2d(oup),
            )
        else:
            self.conv = nn.Sequential(
                # pw
                nn.Conv2d(inp, hidden_dim, 1, 1, 0, bias=False),
                nn.BatchNorm2d(hidden_dim),
                nn.ReLU6(inplace=True),
                # dw
                nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, dilation=dilation, bias=False),
                nn.BatchNorm2d(hidden_dim),
                nn.ReLU6(inplace=True),
                # pw-linear
                nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False),
                nn.BatchNorm2d(oup),
            )

    def forward(self, x):
        if self.use_res_connect:
            return x + self.conv(x)
        else:
            return self.conv(x)


class MobileNetV2(nn.Module):
    def __init__(self, in_channels, alpha=1.0, expansion=6, num_classes=1000):
        super(MobileNetV2, self).__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes
        input_channel = 32
        last_channel = 1280
        interverted_residual_setting = [
            # t, c, n, s
            [1        , 16, 1, 1],
            [expansion, 24, 2, 2],
            [expansion, 32, 3, 2],
            [expansion, 64, 4, 2],
            [expansion, 96, 3, 1],
            [expansion, 160, 3, 2],
            [expansion, 320, 1, 1],
        ]

        # building first layer
        input_channel = _make_divisible(input_channel*alpha, 8)
        self.last_channel = _make_divisible(last_channel*alpha, 8) if alpha > 1.0 else last_channel
        self.features = [conv_bn(self.in_channels, input_channel, 2)]

        # building inverted residual blocks
        for t, c, n, s in interverted_residual_setting:
            output_channel = _make_divisible(int(c*alpha), 8)
            for i in range(n):
                if i == 0:
                    self.features.append(InvertedResidual(input_channel, output_channel, s, expansion=t))
                else:
                    self.features.append(InvertedResidual(input_channel, output_channel, 1, expansion=t))
                input_channel = output_channel

        # building last several layers
        self.features.append(conv_1x1_bn(input_channel, self.last_channel))

        # make it nn.Sequential
        self.features = nn.Sequential(*self.features)

        # Initialize weights
        self._init_weights()

    def forward(self, x):
        # Stage1
        x = self.features[0](x)
        x = self.features[1](x)
        # Stage2
        x = self.features[2](x)
        x = self.features[3](x)
        # Stage3
        x = self.features[4](x)
        x = self.features[5](x)
        x = self.features[6](x)
        # Stage4
        x = self.features[7](x)
        x = self.features[8](x)
        x = self.features[9](x)
        x = self.features[10](x)
        x = self.features[11](x)
        x = self.features[12](x)
        x = self.features[13](x)
        # Stage5
        x = self.features[14](x)
        x = self.features[15](x)
        x = self.features[16](x)
        x = self.features[17](x)
        x = self.features[18](x)

        return x

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                n = m.weight.size(1)
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()


class MobileNetV2Backbone(nn.Module):
    """ MobileNetV2 Backbone for MODNet
    """

    def __init__(self, in_channels):
        super(MobileNetV2Backbone, self).__init__()
        self.in_channels = in_channels

        self.model = MobileNetV2(self.in_channels, alpha=1.0, expansion=6, num_classes=None)
        self.enc_channels = [16, 24, 32, 96, 1280]

    def forward(self, x):
        x = self.model.features[0](x)
        x = self.model.features[1](x)
        enc2x = x

        x = self.model.features[2](x)
        x = self.model.features[3](x)
        enc4x = x

        x = self.model.features[4](x)
        x = self.model.features[5](x)
        x = self.model.features[6](x)
        enc8x = x

        x = self.model.features[7](x)
        x = self.model.features[8](x)
        x = self.model.features[9](x)
        x = self.model.features[10](x)
        x = self.model.features[11](x)
        x = self.model.features[12](x)
        x = self.model.features[13](x)
        enc16x = x

        x = self.model.features[14](x)
        x = self.model.features[15](x)
        x = self.model.features[16](x)
        x = self.model.features[17](x)
        x = self.model.features[18](x)
        enc32x = x
        return [enc2x, enc4x, enc8x, enc16x, enc32x]


#------------------------------------------------------------------------------
#  MODNet Branches
#------------------------------------------------------------------------------

class LRBranch(nn.Module):
    """ Low Resolution Branch of MODNet
    """

    def __init__(self, backbone):
        super(LRBranch, self).__init__()

        enc_channels = backbone.enc_channels
        
        self.backbone = backbone
        self.se_block = SEBlock(enc_channels[4], enc_channels[4], reduction=4)
        self.conv_lr16x = Conv2dIBNormRelu(enc_channels[4], enc_channels[3], 5, stride=1, padding=2)
        self.conv_lr8x = Conv2dIBNormRelu(enc_channels[3], enc_channels[2], 5, stride=1, padding=2)
        self.conv_lr = Conv2dIBNormRelu(enc_channels[2], 1, kernel_size=3, stride=2, padding=1, with_ibn=False, with_relu=False)

    def forward(self, img, inference):
        enc_features = self.backbone.forward(img)
        enc2x, enc4x, enc8x, enc16x, enc32x = enc_features

        enc32x = self.se_block(enc32x)
        lr16x = F.interpolate(enc32x, scale_factor=2, mode='bilinear', align_corners=False)
        lr16x = self.conv_lr16x(lr16x)
        lr8x = F.interpolate(lr16x, scale_factor=2, mode='bilinear', align_corners=False)
        lr8x = self.conv_lr8x(lr8x)

        pred_semantic = None
        if not inference:
            lr = self.conv_lr(lr8x)
            pred_semantic = torch.sigmoid(lr)

        return pred_semantic, lr8x, [enc2x, enc4x]


class HRBranch(nn.Module):
    """ High Resolution Branch of MODNet
    """

    def __init__(self, hr_channels, enc_channels):
        super(HRBranch, self).__init__()

        self.tohr_enc2x = Conv2dIBNormRelu(enc_channels[0], hr_channels, 1, stride=1, padding=0)
        self.conv_enc2x = Conv2dIBNormRelu(hr_channels + 3, hr_channels, 3, stride=2, padding=1)

        self.tohr_enc4x = Conv2dIBNormRelu(enc_channels[1], hr_channels, 1, stride=1, padding=0)
        self.conv_enc4x = Conv2dIBNormRelu(2 * hr_channels, 2 * hr_channels, 3, stride=1, padding=1)

        self.conv_hr4x = nn.Sequential(
            Conv2dIBNormRelu(3 * hr_channels + 3, 2 * hr_channels, 3, stride=1, padding=1),
            Conv2dIBNormRelu(2 * hr_channels, 2 * hr_channels, 3, stride=1, padding=1),
            Conv2dIBNormRelu(2 * hr_channels, hr_channels, 3, stride=1, padding=1),
        )

        self.conv_hr2x = nn.Sequential(
            Conv2dIBNormRelu(2 * hr_channels, 2 * hr_channels, 3, stride=1, padding=1),
            Conv2dIBNormRelu(2 * hr_channels, hr_channels, 3, stride=1, padding=1),
            Conv2dIBNormRelu(hr_channels, hr_channels, 3, stride=1, padding=1),
            Conv2dIBNormRelu(hr_channels, hr_channels, 3, stride=1, padding=1),
        )

        self.conv_hr = nn.Sequential(
            Conv2dIBNormRelu(hr_channels + 3, hr_channels, 3, stride=1, padding=1),
            Conv2dIBNormRelu(hr_channels, 1, kernel_size=1, stride=1, padding=0, with_ibn=False, with_relu=False),
        )

    def forward(self, img, enc2x, enc4x, lr8x, inference):
        img2x = F.interpolate(img, scale_factor=1/2, mode='bilinear', align_corners=False)
        img4x = F.interpolate(img, scale_factor=1/4, mode='bilinear', align_corners=False)

        enc2x = self.tohr_enc2x(enc2x)
        hr4x = self.conv_enc2x(torch.cat((img2x, enc2x), dim=1))

        enc4x = self.tohr_enc4x(enc4x)
        hr4x = self.conv_enc4x(torch.cat((hr4x, enc4x), dim=1))

        lr4x = F.interpolate(lr8x, scale_factor=2, mode='bilinear', align_corners=False)
        hr4x = self.conv_hr4x(torch.cat((hr4x, lr4x, img4x), dim=1))

        hr2x = F.interpolate(hr4x, scale_factor=2, mode='bilinear', align_corners=False)
        hr2x = self.conv_hr2x(torch.cat((hr2x, enc2x), dim=1))

        pred_detail = None
        if not inference:
            hr = F.interpolate(hr2x, scale_factor=2, mode='bilinear', align_corners=False)
            hr = self.conv_hr(torch.cat((hr, img), dim=1))
            pred_detail = torch.sigmoid(hr)

        return pred_detail, hr2x


class FusionBranch(nn.Module):
    """ Fusion Branch of MODNet
    """

    def __init__(self, hr_channels, enc_channels):
        super(FusionBranch, self).__init__()
        self.conv_lr4x = Conv2dIBNormRelu(enc_channels[2], hr_channels, 5, stride=1, padding=2)
        
        self.conv_f2x = Conv2dIBNormRelu(2 * hr_channels, hr_channels, 3, stride=1, padding=1)
        self.conv_f = nn.Sequential(
            Conv2dIBNormRelu(hr_channels + 3, int(hr_channels / 2), 3, stride=1, padding=1),
            Conv2dIBNormRelu(int(hr_channels / 2), 1, 1, stride=1, padding=0, with_ibn=False, with_relu=False),
        )

    def forward(self, img, lr8x, hr2x):
        lr4x = F.interpolate(lr8x, scale_factor=2, mode='bilinear', align_corners=False)
        lr4x = self.conv_lr4x(lr4x)
        lr2x = F.interpolate(lr4x, scale_factor=2, mode='bilinear', align_corners=False)

        f2x = self.conv_f2x(torch.cat((lr2x, hr2x), dim=1))
        f = F.interpolate(f2x, scale_factor=2, mode='bilinear', align_corners=False)
        f = self.conv_f(torch.cat((f, img), dim=1))
        pred_matte = torch.sigmoid(f)

        return pred_matte


#------------------------------------------------------------------------------
#  MODNet
#------------------------------------------------------------------------------

class ModNet(nn.Module):
    """ Architecture of MODNet
    """

    def __init__(self, in_channels=3, hr_channels=32, backbone_arch='mobilenetv2', backbone_pretrained=True):
        super(ModNet, self).__init__()

        self.in_channels = in_channels
        self.hr_channels = hr_channels
        self.backbone_arch = backbone_arch
        self.backbone_pretrained = backbone_pretrained

        self.backbone = MobileNetV2Backbone(self.in_channels)

        self.lr_branch = LRBranch(self.backbone)
        self.hr_branch = HRBranch(self.hr_channels, self.backbone.enc_channels)
        self.f_branch = FusionBranch(self.hr_channels, self.backbone.enc_channels)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                self._init_conv(m)
            elif isinstance(m, nn.BatchNorm2d) or isinstance(m, nn.InstanceNorm2d):
                self._init_norm(m)

    def forward(self, img, inference=True):
        pred_semantic, lr8x, [enc2x, enc4x] = self.lr_branch(img, inference)
        pred_detail, hr2x = self.hr_branch(img, enc2x, enc4x, lr8x, inference)
        pred_matte = self.f_branch(img, lr8x, hr2x)

        return pred_semantic, pred_detail, pred_matte
    
    def freeze_norm(self):
        norm_types = [nn.BatchNorm2d, nn.InstanceNorm2d]
        for m in self.modules():
            for n in norm_types:
                if isinstance(m, n):
                    m.eval()
                    continue

    def _init_conv(self, conv):
        nn.init.kaiming_uniform_(
            conv.weight, a=0, mode='fan_in', nonlinearity='relu')
        if conv.bias is not None:
            nn.init.constant_(conv.bias, 0)

    def _init_norm(self, norm):
        if norm.weight is not None:
            nn.init.constant_(norm.weight, 1)
            nn.init.constant_(norm.bias, 0)


# 初始化ModNet人像分割模型
modnet = ModNet().eval()

# 尝试加载预训练权重
try:
    model_path = "./app/models/modnet_photographic_portrait_matting.ckpt"
    
    # 加载权重，处理DataParallel格式
    state_dict = torch.load(model_path, map_location=torch.device('cpu'))
    
    # 移除权重中的'module.'前缀（如果存在）
    new_state_dict = {}
    for k, v in state_dict.items():
        if k.startswith('module.'):
            new_state_dict[k[7:]] = v  # 移除'module.'前缀
        else:
            new_state_dict[k] = v
    
    modnet.load_state_dict(new_state_dict)
    print("✅ ModNet预训练权重加载成功")
except Exception as e:
    print(f"⚠️  ModNet预训练权重加载失败: {str(e)}")
    print("   将使用随机初始化的模型")


def detect_face(image, target_region=None):
    """
    人脸检测函数 - 使用MTCNN从图像中检测人脸，并优化人脸区域选择
    
    Args:
        image (PIL.Image): 输入的PIL图像对象
        target_region (tuple, optional): 目标人脸区域坐标 (x1, y1, x2, y2)，用于优先选择指定区域内的人脸
        
    Returns:
        tuple: (人脸坐标列表, 裁剪后的人脸图像列表, 人脸置信度列表)
            - face_boxes: 人脸边界框坐标列表，格式为[(x1, y1, x2, y2), ...]，按置信度和区域优先级排序
            - face_images: 裁剪后的人脸图像列表[PIL.Image, ...]
            - confidences: 人脸检测置信度列表[float, ...]
            
    Raises:
        Exception: 当图像格式不支持或处理失败时抛出异常
    """
    try:
        # 确保输入是PIL图像
        if not isinstance(image, Image.Image):
            raise TypeError("输入必须是PIL.Image对象")
        
        # 转换图像为RGB格式
        rgb_image = image.convert('RGB')
        
        # 使用MTCNN检测人脸
        # 返回人脸边界框、置信度和关键点
        results = mtcnn.detect_faces(np.array(rgb_image))
        
        # 如果没有检测到人脸，返回空列表
        if not results:
            return [], [], []
        
        face_data = []  # 存储人脸数据(坐标、图像、置信度)
        
        # 处理每个检测到的人脸
        for result in results:
            # 获取边界框坐标（x1, y1, width, height）
            x1, y1, width, height = result['box']
            # 计算右下角坐标
            x2 = x1 + width
            y2 = y1 + height
            
            # 确保坐标在图像范围内（防止越界）
            x1, y1 = max(0, x1), max(0, y1)
            x2 = min(image.width, x2)
            y2 = min(image.height, y2)
            
            # 计算人脸区域中心
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # 扩展边界框，确保包含完整人脸
            # 扩展比例
            expand_ratio = 0.1
            expand_w = int(width * expand_ratio)
            expand_h = int(height * expand_ratio)
            
            # 扩展边界框
            x1_expanded = max(0, x1 - expand_w)
            y1_expanded = max(0, y1 - expand_h)
            x2_expanded = min(image.width, x2 + expand_w)
            y2_expanded = min(image.height, y2 + expand_h)
            
            # 裁剪扩展后的人脸区域
            face_img = rgb_image.crop((x1_expanded, y1_expanded, x2_expanded, y2_expanded))
            
            # 获取置信度
            confidence = result.get('confidence', 0)
            
            # 计算与人脸区域的重叠度或距离（用于优先选择目标区域内的人脸）
            region_score = 0
            if target_region:
                t_x1, t_y1, t_x2, t_y2 = target_region
                # 计算重叠区域面积
                overlap_x1 = max(x1, t_x1)
                overlap_y1 = max(y1, t_y1)
                overlap_x2 = min(x2, t_x2)
                overlap_y2 = min(y2, t_y2)
                
                if overlap_x1 < overlap_x2 and overlap_y1 < overlap_y2:
                    overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
                    face_area = (x2 - x1) * (y2 - y1)
                    target_area = (t_x2 - t_x1) * (t_y2 - t_y1)
                    # 计算IOU（交并比）
                    union_area = face_area + target_area - overlap_area
                    if union_area > 0:
                        region_score = overlap_area / union_area
                else:
                    # 计算中心点距离
                    t_center_x = (t_x1 + t_x2) / 2
                    t_center_y = (t_y1 + t_y2) / 2
                    distance = np.sqrt((center_x - t_center_x)**2 + (center_y - t_center_y)**2)
                    # 距离越近，得分越高
                    max_distance = np.sqrt(image.width**2 + image.height**2)
                    region_score = 1 - (distance / max_distance)
            
            # 综合评分：置信度(0.7权重) + 区域匹配度(0.3权重)
            score = confidence * 0.7 + region_score * 0.3
            
            # 存储人脸数据
            face_data.append({
                'box': (x1, y1, x2, y2),
                'image': face_img,
                'confidence': confidence,
                'score': score
            })
        
        # 按综合评分降序排序，优先选择评分高的人脸
        face_data.sort(key=lambda x: x['score'], reverse=True)
        
        # 提取排序后的结果
        face_boxes = [item['box'] for item in face_data]
        face_images = [item['image'] for item in face_data]
        confidences = [item['confidence'] for item in face_data]
        
        return face_boxes, face_images, confidences
        
    except Exception as e:
        # 记录错误信息
        print(f"人脸检测出错: {str(e)}")
        raise Exception(f"人脸检测失败: {str(e)}")


def segment_face(face_image):
    """
    人脸分割函数 - 使用ModNet对人脸图像进行分割，提取高质量的人脸掩码
    
    Args:
        face_image (PIL.Image): 输入的人脸图像（已裁剪）
        
    Returns:
        PIL.Image: 分割后的人脸图像，背景为透明
    """
    try:
        # 确保输入是PIL图像
        if not isinstance(face_image, Image.Image):
            raise TypeError("输入必须是PIL.Image对象")
        
        # 图像预处理
        # 1. 转换为RGB格式
        rgb_image = face_image.convert('RGB')
        
        # 2. 调整尺寸为ModNet输入大小 (512x512)
        input_size = (512, 512)
        resized_image = rgb_image.resize(input_size, Image.LANCZOS)
        
        # 3. 转换为numpy数组
        img_np = np.array(resized_image)
        
        # 4. 归一化 (0-1)
        img_np = img_np.astype(np.float32) / 255.0
        
        # 5. 转换为PyTorch张量
        img_tensor = torch.tensor(img_np).permute(2, 0, 1).unsqueeze(0)
        
        # 模型推理
        with torch.no_grad():
            # 生成掩码 - 使用新的ModNet forward方法，返回三个值
            pred_semantic, pred_detail, pred_matte = modnet(img_tensor, inference=True)
            
            # 使用融合分支的输出作为最终掩码
            mask_tensor = pred_matte
            
            # 将掩码调整回原始人脸图像大小
            mask_tensor = F.interpolate(
                mask_tensor,
                size=face_image.size[::-1],
                mode='bilinear',
                align_corners=False
            )
            
            # 转换为numpy数组
            mask_np = mask_tensor.squeeze().cpu().numpy()
        
        # 应用掩码到原始图像
        # 1. 获取原始图像的numpy数组
        original_np = np.array(face_image)
        
        # 2. 将掩码转换为3通道
        mask_3ch = np.repeat(mask_np[:, :, np.newaxis], 3, axis=2)
        
        # 3. 应用掩码
        segmented_np = original_np * mask_3ch
        segmented_np = segmented_np.astype(np.uint8)
        
        # 4. 转换为PIL图像（直接返回3通道RGB图像）
        segmented_image = Image.fromarray(segmented_np)
        
        return segmented_image
        
    except Exception as e:
        print(f"人脸分割出错: {str(e)}")
        # 如果分割失败，返回原始图像
        return face_image


def extract_face_feature(face_images, use_segmentation=True):
    """
    人脸特征提取函数 - 使用FaceNet提取人脸特征向量
    
    Args:
        face_images (list): 裁剪后的人脸图像列表 [PIL.Image, ...]
        use_segmentation (bool): 是否使用ModNet进行人脸分割，默认为True
    
    Returns:
        list: 512维人脸特征向量列表 [numpy.array, ...]
    
    Raises:
        Exception: 当特征提取失败时抛出异常
    """
    try:
        # 检查输入
        if not face_images or not all(isinstance(img, Image.Image) for img in face_images):
            return []
        
        feature_vectors = []  # 存储特征向量
        
        # 处理每个人脸图像
        for face_img in face_images:
            # 1. 人脸分割（如果启用）
            if use_segmentation:
                face_img = segment_face(face_img)
            
            # 2. 图像预处理增强
            # 2.1 转换为numpy数组
            img_np = np.array(face_img)
            
            # 2.2 处理alpha通道（如果存在）
            if len(img_np.shape) == 4:
                # 如果有alpha通道，将其转换为3通道RGB
                # 使用alpha通道作为掩码
                alpha_channel = img_np[:, :, 3] / 255.0
                img_np = img_np[:, :, :3] * alpha_channel[:, :, np.newaxis]
                img_np = img_np.astype(np.uint8)
            
            # 2.3 图像尺寸检查和调整
            if img_np is None or img_np.size == 0:
                print("错误：空图像输入")
                feature_vectors.append(np.zeros(512))
                continue
                
            # 获取图像尺寸
            h, w = img_np.shape[:2]
            
            # 2.4 检查最小尺寸要求（确保至少能被卷积核处理）
            min_size = 10  # 最小尺寸要求
            if h < min_size or w < min_size:
                print(f"警告：人脸图像尺寸过小 ({w}x{h}px)，需要调整尺寸")
                # 调整为标准尺寸 (160x160)，这是FaceNet的标准输入尺寸
                img_np = cv2.resize(img_np, (160, 160), interpolation=cv2.INTER_CUBIC)
            else:
                # 确保图像尺寸为160x160，这是FaceNet的标准输入尺寸
                if h != 160 or w != 160:
                    img_np = cv2.resize(img_np, (160, 160), interpolation=cv2.INTER_CUBIC)
            
            # 2.5 应用直方图均衡化来增强对比度
            # 只对Y通道（亮度）进行均衡化
            if len(img_np.shape) == 3 and img_np.shape[2] == 3:
                # 转换到YUV色彩空间
                img_yuv = cv2.cvtColor(img_np, cv2.COLOR_RGB2YUV)
                # 均衡化Y通道
                img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
                # 转换回RGB
                img_np = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2RGB)
            
            # 2.6 高斯模糊去噪（轻微）
            img_np = cv2.GaussianBlur(img_np, (3, 3), 0)
            
            # 3. 直接使用numpy数组转换为PyTorch张量并标准化
            # 确保是3通道RGB图像
            if len(img_np.shape) == 3 and img_np.shape[2] == 3:
                img_tensor = torch.tensor(img_np).float().permute(2, 0, 1)
                img_tensor = (img_tensor / 255.0 - 0.5) * 2.0  # 标准化
                img_tensor = img_tensor.unsqueeze(0)  # 添加批次维度
            else:
                # 如果不是3通道，转换为3通道
                print(f"警告：图像通道数不是3，当前通道数: {img_np.shape[2] if len(img_np.shape) == 3 else 1}")
                if len(img_np.shape) == 2:
                    # 灰度图像，转换为3通道
                    img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2RGB)
                elif len(img_np.shape) == 4:
                    # 有alpha通道，再次处理
                    alpha_channel = img_np[:, :, 3] / 255.0
                    img_np = img_np[:, :, :3] * alpha_channel[:, :, np.newaxis]
                    img_np = img_np.astype(np.uint8)
                img_tensor = torch.tensor(img_np).float().permute(2, 0, 1)
                img_tensor = (img_tensor / 255.0 - 0.5) * 2.0  # 标准化
                img_tensor = img_tensor.unsqueeze(0)  # 添加批次维度
            
            # 4. 提取特征向量
            with torch.no_grad():  # 关闭梯度计算，提高性能
                feature = resnet(img_tensor)
            
            # 5. 特征归一化，增强匹配稳定性
            feature_np = feature.squeeze().cpu().numpy()
            feature_np = feature_np / np.linalg.norm(feature_np) if np.linalg.norm(feature_np) > 0 else feature_np
            
            feature_vectors.append(feature_np)
        
        return feature_vectors
        
    except Exception as e:
        print(f"特征提取出错: {str(e)}")
        raise Exception(f"人脸特征提取失败: {str(e)}")


def compare_face_features(input_feature, db_features, threshold=0.55):
    """
    人脸特征比对函数 - 计算余弦相似度进行特征比对
    
    Args:
        input_feature (numpy.array): 待比对的人脸特征向量 (512维)
        db_features (list): 数据库中的人脸特征向量列表 [numpy.array, ...]
        threshold (float): 相似度阈值，默认为0.55
        
    Returns:
        tuple: (匹配结果列表, 最高相似度)
            - matches: [(索引, 相似度值), ...]，按相似度降序排列
            - max_similarity: 最高相似度值
        
    Raises:
        ValueError: 当输入特征格式不正确时抛出异常
    """
    """
    人脸特征比对函数 - 计算余弦相似度进行特征比对
    
    Args:
        input_feature (numpy.array): 待比对的人脸特征向量 (512维)
        db_features (list): 数据库中的人脸特征向量列表 [numpy.array, ...]
        threshold (float): 相似度阈值，默认为0.55
        
    Returns:
        tuple: (匹配结果列表, 最高相似度)
            - matches: [(索引, 相似度值), ...]，按相似度降序排列
            - max_similarity: 最高相似度值
        
    Raises:
        ValueError: 当输入特征格式不正确时抛出异常
    """
    try:
        # 验证输入特征向量
        if not isinstance(input_feature, np.ndarray) or input_feature.shape != (512,):
            raise ValueError("输入特征必须是512维numpy数组")
        
        if not db_features:
            return [], 0.0
        
        matches = []  # 存储匹配结果
        
        # 计算输入特征与每个数据库特征的余弦相似度
        for i, db_feature in enumerate(db_features):
            # 验证数据库特征
            if not isinstance(db_feature, np.ndarray) or db_feature.shape != (512,):
                continue
            
            # 计算余弦相似度
            # cos_sim = (a·b) / (||a||×||b||)
            dot_product = np.dot(input_feature, db_feature)
            norm_input = np.linalg.norm(input_feature)
            norm_db = np.linalg.norm(db_feature)
            
            # 避免除零错误
            if norm_input > 0 and norm_db > 0:
                similarity = dot_product / (norm_input * norm_db)
                
                # 相似度优化：对于接近阈值的匹配给予一定加权
                if threshold - 0.05 <= similarity < threshold:
                    # 对于接近阈值的情况，轻微提高相似度
                    weighted_similarity = similarity + 0.02
                    if weighted_similarity >= threshold:
                        matches.append((i, weighted_similarity))
                elif similarity >= threshold:
                    matches.append((i, similarity))
        
        # 按相似度降序排序
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # 计算最高相似度
        max_similarity = matches[0][1] if matches else 0.0
        
        return matches, max_similarity
        
    except ValueError:
        raise
    except Exception as e:
        print(f"特征比对出错: {str(e)}")
        raise Exception(f"人脸特征比对失败: {str(e)}")


def save_face_feature(feature_vector, file_path):
    """
    保存人脸特征向量到文件
    
    Args:
        feature_vector (numpy.array): 512维人脸特征向量
        file_path (str): 保存文件路径
        
    Returns:
        bool: 保存是否成功
    """
    try:
        np.save(file_path, feature_vector)
        return True
    except Exception as e:
        print(f"保存特征向量失败: {str(e)}")
        return False


def load_face_feature(file_path):
    """
    从文件加载人脸特征向量
    
    Args:
        file_path (str): 特征向量文件路径
        
    Returns:
        numpy.array or None: 512维特征向量，如果加载失败返回None
    """
    try:
        return np.load(file_path)
    except Exception as e:
        print(f"加载特征向量失败: {str(e)}")
        return None