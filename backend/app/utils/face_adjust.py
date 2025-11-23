"""人脸区域调整工具模块 - 提供人脸区域的自动检测和手工调整功能"""
import cv2
import numpy as np
from PIL import Image
import io
import base64
from app.utils.face_utils import detect_face

class FaceAdjustment:
    """
    人脸区域调整工具类 - 提供人脸区域的自动检测和手工调整功能
    """
    
    def __init__(self):
        """
        初始化人脸调整工具
        """
        self.current_face_box = None  # 当前人脸区域坐标
        self.image_data = None  # 原始图像数据
        self.adjusted_image = None  # 调整后的图像
        
    def process_image(self, image_file, target_region=None):
        """
        处理输入图像，自动检测人脸区域
        
        Args:
            image_file: 图像文件对象或PIL Image对象
            target_region (tuple, optional): 目标人脸区域坐标 (x1, y1, x2, y2)
            
        Returns:
            dict: 包含检测结果的字典
                - success: 是否成功
                - face_box: 检测到的人脸区域坐标
                - face_count: 检测到的人脸数量
                - image_data: 包含人脸框选的图像数据(Base64)
                - message: 处理消息
        
        Raises:
            Exception: 当图像处理失败时抛出异常
        """
        try:
            # 检查输入类型并转换为PIL Image
            if isinstance(image_file, Image.Image):
                image = image_file
            else:
                # 从文件对象读取
                image = Image.open(image_file).convert('RGB')
            
            # 保存原始图像
            self.image_data = image
            
            # 使用优化后的人脸检测函数
            face_boxes, _, confidences = detect_face(image, target_region)
            
            # 转换PIL Image为OpenCV格式进行处理
            cv_image = np.array(image)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            
            # 如果检测到人脸
            if face_boxes:
                # 选择第一个人脸区域（综合评分最高的）
                self.current_face_box = face_boxes[0]
                
                # 在图像上绘制人脸框
                x1, y1, x2, y2 = self.current_face_box
                cv2.rectangle(cv_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # 绿色框
                
                # 添加置信度文本
                if confidences:
                    confidence_text = f"Confidence: {confidences[0]:.2f}"
                    cv2.putText(cv_image, confidence_text, 
                               (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 
                               0.5, (0, 255, 0), 2)
                
                # 添加提示文本
                cv2.putText(cv_image, "Press 'A' to adjust, 'S' to save, 'D' to detect again", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 0, 255), 2)
                
                result = {
                    "success": True,
                    "face_box": self.current_face_box,
                    "face_count": len(face_boxes),
                    "message": f"成功检测到 {len(face_boxes)} 个人脸，已自动选择评分最高的人脸"
                }
            else:
                # 未检测到人脸
                self.current_face_box = None
                cv2.putText(cv_image, "未检测到人脸，请尝试调整图像或手动框选", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 0, 255), 2)
                
                result = {
                    "success": False,
                    "face_box": None,
                    "face_count": 0,
                    "message": "未检测到人脸，请尝试手动框选"
                }
            
            # 将OpenCV图像转换回PIL Image并保存
            self.adjusted_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            self.adjusted_image = Image.fromarray(self.adjusted_image)
            
            # 将调整后的图像转换为Base64编码
            buffered = io.BytesIO()
            self.adjusted_image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            result["image_data"] = img_str
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "face_box": None,
                "face_count": 0,
                "image_data": None,
                "message": f"图像处理失败: {str(e)}"
            }
    
    def manual_adjust(self, image_data, new_face_box):
        """
        手工调整人脸区域
        
        Args:
            image_data: 图像数据（Base64编码或PIL Image）
            new_face_box (tuple): 手动调整后的人脸区域坐标 (x1, y1, x2, y2)
            
        Returns:
            dict: 包含调整结果的字典
                - success: 是否成功
                - face_box: 调整后的人脸区域坐标
                - image_data: 包含新人脸框的图像数据(Base64)
                - message: 处理消息
        
        Raises:
            Exception: 当人脸区域调整失败时抛出异常
        """
        try:
            # 验证输入坐标
            if len(new_face_box) != 4:
                return {
                    "success": False,
                    "face_box": None,
                    "image_data": None,
                    "message": "无效的人脸区域坐标格式"
                }
            
            x1, y1, x2, y2 = new_face_box
            
            # 检查坐标有效性
            if x1 >= x2 or y1 >= y2:
                return {
                    "success": False,
                    "face_box": None,
                    "image_data": None,
                    "message": "无效的人脸区域坐标：左边界必须小于右边界，上边界必须小于下边界"
                }
            
            # 加载或使用当前图像
            if isinstance(image_data, Image.Image):
                image = image_data
            elif isinstance(image_data, str):
                # 从Base64解码
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            else:
                # 使用之前处理的图像
                image = self.image_data
            
            if image is None:
                return {
                    "success": False,
                    "face_box": None,
                    "image_data": None,
                    "message": "未找到图像数据"
                }
            
            # 更新当前人脸区域
            self.current_face_box = (x1, y1, x2, y2)
            
            # 在图像上绘制新的人脸框
            cv_image = np.array(image)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            
            # 绘制手动调整的人脸框（红色）
            cv2.rectangle(cv_image, (x1, y1), (x2, y2), (0, 0, 255), 2)  # 红色框
            
            # 添加提示文本
            cv2.putText(cv_image, "Manual Adjustment Applied", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (0, 0, 255), 2)
            
            # 更新调整后的图像
            self.adjusted_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            self.adjusted_image = Image.fromarray(self.adjusted_image)
            
            # 将调整后的图像转换为Base64编码
            buffered = io.BytesIO()
            self.adjusted_image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return {
                "success": True,
                "face_box": self.current_face_box,
                "image_data": img_str,
                "message": "人脸区域已成功调整"
            }
            
        except Exception as e:
            return {
                "success": False,
                "face_box": None,
                "image_data": None,
                "message": f"人脸区域调整失败: {str(e)}"
            }
    
    def get_adjusted_face(self):
        """
        获取调整后的人脸图像
        
        Returns:
            PIL.Image or None: 裁剪后的人脸图像
        
        Raises:
            Exception: 当获取调整后人脸失败时抛出异常
        """
        if self.image_data is not None and self.current_face_box is not None:
            # 裁剪人脸区域
            x1, y1, x2, y2 = self.current_face_box
            
            # 扩展边界框以确保包含完整人脸
            width = x2 - x1
            height = y2 - y1
            expand_ratio = 0.1
            expand_w = int(width * expand_ratio)
            expand_h = int(height * expand_ratio)
            
            x1_expanded = max(0, x1 - expand_w)
            y1_expanded = max(0, y1 - expand_h)
            x2_expanded = min(self.image_data.width, x2 + expand_w)
            y2_expanded = min(self.image_data.height, y2 + expand_h)
            
            # 裁剪扩展后的人脸区域
            face_image = self.image_data.crop((x1_expanded, y1_expanded, x2_expanded, y2_expanded))
            
            # 调整大小为人脸特征提取所需的尺寸
            face_image = face_image.resize((160, 160), Image.BILINEAR)
            
            return face_image
        
        return None
    
    def validate_face_region(self, face_box, image_size):
        """
        验证人脸区域是否有效
        
        Args:
            face_box (tuple): 人脸区域坐标 (x1, y1, x2, y2)
            image_size (tuple): 图像尺寸 (width, height)
            
        Returns:
            tuple: (是否有效, 消息)
        """
        if not face_box or len(face_box) != 4:
            return False, "无效的人脸区域格式"
        
        x1, y1, x2, y2 = face_box
        width, height = image_size
        
        # 检查坐标是否在图像范围内
        if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
            return False, "人脸区域超出图像范围"
        
        # 检查区域是否足够大
        region_width = x2 - x1
        region_height = y2 - y1
        
        min_size = 50  # 最小尺寸阈值
        if region_width < min_size or region_height < min_size:
            return False, "人脸区域太小，请选择更大的区域"
        
        # 检查宽高比是否合理（人脸通常不会太宽或太高）
        aspect_ratio = region_width / region_height
        if aspect_ratio < 0.5 or aspect_ratio > 2.0:
            return False, "人脸区域比例不合理，请调整"
        
        return True, "人脸区域有效"

# 提供简化的函数接口供其他模块调用
def auto_detect_and_adjust(image_file, target_region=None):
    """
    自动检测人脸并提供调整接口
    
    Args:
        image_file: 图像文件
        target_region (tuple, optional): 目标人脸区域 (x1, y1, x2, y2)
        
    Returns:
        dict: 检测和调整结果
            - success: 是否成功
            - face_box: 检测到的人脸区域坐标
            - face_count: 检测到的人脸数量
            - image_data: 包含人脸框选的图像数据(Base64)
            - message: 处理消息
    """
    adjuster = FaceAdjustment()
    return adjuster.process_image(image_file, target_region)

def manual_adjust_face_region(image_data, new_face_box):
    """
    手动调整人脸区域
    
    Args:
        image_data: 图像数据（Base64编码或PIL Image）
        new_face_box (tuple): 新的人脸区域坐标 (x1, y1, x2, y2)
        
    Returns:
        dict: 调整结果
            - success: 是否成功
            - face_box: 调整后的人脸区域坐标
            - image_data: 包含新人脸框的图像数据(Base64)
            - message: 处理消息
    """
    adjuster = FaceAdjustment()
    return adjuster.manual_adjust(image_data, new_face_box)

def get_cropped_face(image_file, face_box):
    """
    获取裁剪后的人脸图像
    
    Args:
        image_file: 图像文件
        face_box (tuple): 人脸区域坐标 (x1, y1, x2, y2)
        
    Returns:
        PIL.Image or None: 裁剪后的人脸图像
    
    Raises:
        ValueError: 当人脸区域无效时抛出异常
    """
    try:
        # 打开图像
        if isinstance(image_file, Image.Image):
            image = image_file
        else:
            image = Image.open(image_file).convert('RGB')
        
        # 验证人脸区域
        adjuster = FaceAdjustment()
        is_valid, message = adjuster.validate_face_region(face_box, (image.width, image.height))
        
        if not is_valid:
            raise ValueError(message)
        
        # 扩展边界框
        x1, y1, x2, y2 = face_box
        width = x2 - x1
        height = y2 - y1
        expand_ratio = 0.1
        expand_w = int(width * expand_ratio)
        expand_h = int(height * expand_ratio)
        
        x1_expanded = max(0, x1 - expand_w)
        y1_expanded = max(0, y1 - expand_h)
        x2_expanded = min(image.width, x2 + expand_w)
        y2_expanded = min(image.height, y2 + expand_h)
        
        # 裁剪人脸区域
        face_image = image.crop((x1_expanded, y1_expanded, x2_expanded, y2_expanded))
        
        # 调整大小
        face_image = face_image.resize((160, 160), Image.BILINEAR)
        
        return face_image
        
    except Exception as e:
        print(f"裁剪人脸图像失败: {e}")
        return None

# 人脸区域验证函数
def validate_face_region(face_box, image_size):
    """
    验证人脸区域是否有效
    
    Args:
        face_box (tuple): 人脸区域坐标 (x1, y1, x2, y2)
        image_size (tuple): 图像尺寸 (width, height)
        
    Returns:
        tuple: (是否有效, 消息)
    """
    adjuster = FaceAdjustment()
    return adjuster.validate_face_region(face_box, image_size)