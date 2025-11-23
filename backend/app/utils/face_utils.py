"""人脸工具模块 - 实现人脸检测、特征提取、特征比对等核心功能"""
import numpy as np
from PIL import Image
from mtcnn import MTCNN
from facenet_pytorch import InceptionResnetV1
import torch
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


def extract_face_feature(face_images):
    """
    人脸特征提取函数 - 使用FaceNet提取人脸特征向量
    
    Args:
        face_images (list): 裁剪后的人脸图像列表 [PIL.Image, ...]
    
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
            # 图像预处理增强
            # 1. 转换为numpy数组
            img_np = np.array(face_img)
            
            # 2. 图像尺寸检查和调整
            if img_np is None or img_np.size == 0:
                print("错误：空图像输入")
                feature_vectors.append(np.zeros(512))
                continue
                
            # 获取图像尺寸
            h, w = img_np.shape[:2]
            
            # 检查最小尺寸要求（确保至少能被卷积核处理）
            min_size = 10  # 最小尺寸要求
            if h < min_size or w < min_size:
                print(f"警告：人脸图像尺寸过小 ({w}x{h}px)，需要调整尺寸")
                # 调整为标准尺寸 (160x160)，这是FaceNet的标准输入尺寸
                img_np = cv2.resize(img_np, (160, 160), interpolation=cv2.INTER_CUBIC)
            else:
                # 确保图像尺寸为160x160，这是FaceNet的标准输入尺寸
                if h != 160 or w != 160:
                    img_np = cv2.resize(img_np, (160, 160), interpolation=cv2.INTER_CUBIC)
            
            # 3. 应用直方图均衡化来增强对比度
            # 只对Y通道（亮度）进行均衡化
            if len(img_np.shape) == 3 and img_np.shape[2] == 3:
                # 转换到YUV色彩空间
                img_yuv = cv2.cvtColor(img_np, cv2.COLOR_RGB2YUV)
                # 均衡化Y通道
                img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
                # 转换回RGB
                img_np = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2RGB)
            
            # 4. 高斯模糊去噪（轻微）
            img_np = cv2.GaussianBlur(img_np, (3, 3), 0)
            
            # 5. 转回PIL图像
            enhanced_img = Image.fromarray(img_np)
            
            # 6. 转换为PyTorch张量并标准化
            img_tensor = torch.tensor(np.array(enhanced_img)).float().permute(2, 0, 1)
            img_tensor = (img_tensor / 255.0 - 0.5) * 2.0  # 标准化
            img_tensor = img_tensor.unsqueeze(0)  # 添加批次维度
            
            # 7. 提取特征向量
            with torch.no_grad():  # 关闭梯度计算，提高性能
                feature = resnet(img_tensor)
            
            # 8. 特征归一化，增强匹配稳定性
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