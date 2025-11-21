"""人脸工具模块 - 实现人脸检测、特征提取、特征比对等核心功能"""
import numpy as np
from PIL import Image
from mtcnn import MTCNN
from facenet_pytorch import InceptionResnetV1
import torch
import cv2


# 初始化MTCNN人脸检测器
mtcnn = MTCNN(
    min_face_size=20,  # 最小可检测人脸大小
    steps_threshold=[0.6, 0.7, 0.7],  # 检测阈值
    scale_factor=0.709  # 缩放因子
)


# 初始化FaceNet特征提取模型（预训练模型）
# 加载预训练的InceptionResnetV1模型，设置为评估模式
resnet = InceptionResnetV1(pretrained='vggface2').eval()


def detect_face(image):
    """
    人脸检测函数 - 使用MTCNN从图像中检测人脸
    
    Args:
        image (PIL.Image): 输入的PIL图像对象
        
    Returns:
        tuple: (人脸坐标列表, 裁剪后的人脸图像列表)
            - face_boxes: 人脸边界框坐标列表，格式为[(x1, y1, x2, y2), ...]
            - face_images: 裁剪后的人脸图像列表[PIL.Image, ...]
            
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
            return [], []
        
        face_boxes = []  # 存储人脸坐标
        face_images = []  # 存储裁剪后的人脸图像
        
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
            
            # 存储边界框坐标
            face_boxes.append((x1, y1, x2, y2))
            
            # 裁剪人脸区域
            face_img = rgb_image.crop((x1, y1, x2, y2))
            # 调整大小为人脸特征提取所需的尺寸
            face_img = face_img.resize((160, 160), Image.BILINEAR)
            face_images.append(face_img)
        
        return face_boxes, face_images
        
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
        list: 128维人脸特征向量列表 [numpy.array, ...]
        
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
            # 转换PIL图像为numpy数组并标准化
            # 1. 转换为numpy数组 (H, W, C)
            # 2. 转换为PyTorch张量
            # 3. 标准化像素值到[-1, 1]
            img_tensor = torch.tensor(np.array(face_img)).float().permute(2, 0, 1)
            img_tensor = (img_tensor / 255.0 - 0.5) * 2.0  # 标准化
            img_tensor = img_tensor.unsqueeze(0)  # 添加批次维度
            
            # 提取特征向量
            with torch.no_grad():  # 关闭梯度计算，提高性能                                                                                                                                                         
                feature = resnet(img_tensor)
            
            # 转换为numpy数组并存储
            feature_np = feature.squeeze().cpu().numpy()
            feature_vectors.append(feature_np)
        
        return feature_vectors
        
    except Exception as e:
        print(f"特征提取出错: {str(e)}")
        raise Exception(f"人脸特征提取失败: {str(e)}")


def compare_face_features(input_feature, db_features, threshold=0.6):
    """
    人脸特征比对函数 - 计算余弦相似度进行特征比对
    
    Args:
        input_feature (numpy.array): 待比对的人脸特征向量 (128维)
        db_features (list): 数据库中的人脸特征向量列表 [numpy.array, ...]
        threshold (float): 相似度阈值，默认为0.6
        
    Returns:
        tuple: (匹配结果列表, 最高相似度)
            - matches: [(索引, 相似度值), ...]，按相似度降序排列
            - max_similarity: 最高相似度值
        
    Raises:
        ValueError: 当输入特征格式不正确时抛出异常
    """
    try:
        # 验证输入特征向量
        if not isinstance(input_feature, np.ndarray) or input_feature.shape != (128,):
            raise ValueError("输入特征必须是128维numpy数组")
        
        if not db_features:
            return [], 0.0
        
        matches = []  # 存储匹配结果
        
        # 计算输入特征与每个数据库特征的余弦相似度
        for i, db_feature in enumerate(db_features):
            # 验证数据库特征
            if not isinstance(db_feature, np.ndarray) or db_feature.shape != (128,):
                continue
            
            # 计算余弦相似度
            # cos_sim = (a·b) / (||a||×||b||)
            dot_product = np.dot(input_feature, db_feature)
            norm_input = np.linalg.norm(input_feature)
            norm_db = np.linalg.norm(db_feature)
            
            # 避免除零错误
            if norm_input > 0 and norm_db > 0:
                similarity = dot_product / (norm_input * norm_db)
                # 只保留大于阈值的匹配
                if similarity >= threshold:
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
        feature_vector (numpy.array): 128维人脸特征向量
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
        numpy.array or None: 128维特征向量，如果加载失败返回None
    """
    try:
        return np.load(file_path)
    except Exception as e:
        print(f"加载特征向量失败: {str(e)}")
        return None