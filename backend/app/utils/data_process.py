"""人脸数据处理模块

该模块实现人脸识别系统的核心业务逻辑，包括人脸注册和识别功能。
利用MTCNN检测人脸，FaceNet提取特征，并与数据库进行交互。

典型用法：
    from app.utils.data_process import register_face, recognize_face
    from PIL import Image
    
    # 注册人脸
    image = Image.open('user_photo.jpg')
    result = register_face("张三", image)
    
    # 识别人脸
    recognition_result = recognize_face(image)
"""
import os
import sys
import uuid
from datetime import datetime
from PIL import Image
import numpy as np

# 处理相对导入问题
if __name__ == "__main__":
    # 直接运行时添加backend目录到Python路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(os.path.dirname(current_dir))
    sys.path.insert(0, backend_dir)
    from app.config import config
    from app.models.models import User, get_db, SessionLocal
    from app.utils.face_utils import detect_face, extract_face_feature, save_face_feature, load_face_feature, compare_face_features
else:
    # 作为模块导入时使用相对导入
    from ..config import config
    from ..models.models import User, get_db, SessionLocal
    from .face_utils import detect_face, extract_face_feature, save_face_feature, load_face_feature, compare_face_features


def generate_unique_identity_id(db):
    """
    生成唯一身份ID的辅助函数
    
    基于数据库中已有最大ID顺序向下生成唯一身份ID，
    确保唯一性且格式简单。
    
    Args:
        db: 数据库会话对象
        
    Returns:
        str: 唯一的身份ID
    """
    while True:
        try:
            # 查询数据库中最大的identity_id
            max_user = db.query(User).order_by(User.identity_id.desc()).first()
            
            if max_user and max_user.identity_id.isdigit():
                # 如果存在用户且identity_id是数字，则+1
                next_id = int(max_user.identity_id) + 1
            else:
                # 否则从1开始
                next_id = 1
            
            # 格式化为字符串ID
            identity_id = str(next_id)
            
            # 再次检查ID是否存在，防止并发情况
            existing_user = db.query(User).filter(User.identity_id == identity_id).first()
            if not existing_user:
                return identity_id
        except Exception as e:
            # 如果查询失败，使用时间戳作为备选方案
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            identity_id = timestamp
            # 检查时间戳ID是否存在
            existing_user = db.query(User).filter(User.identity_id == identity_id).first()
            if not existing_user:
                return identity_id


def register_face(name, image, identity_id=None):
    """
    人脸注册函数 - 注册新用户并保存人脸信息
    
    处理流程：
    1. 验证输入参数
    2. 检测人脸区域
    3. 提取人脸特征向量
    4. 生成唯一文件名和路径
    5. 自动生成或验证唯一身份ID
    6. 保存用户信息到数据库
    7. 保存人脸图片和特征向量到文件系统
    
    Args:
        name (str): 用户名
        image (PIL.Image): 用户人脸图片
        identity_id (str, optional): 身份ID，如不提供则自动生成唯一ID
        
    Returns:
        dict: 注册结果信息
            - success (bool): 是否成功
            - user_id (int): 用户ID
            - identity_id (str): 生成或提供的身份ID
            - message (str): 结果消息
            
    Raises:
        ValueError: 当输入参数无效、未检测到人脸或身份ID已存在时抛出
        Exception: 当数据库操作失败时抛出
    """
    # 参数验证
    if not name or not isinstance(name, str):
        raise ValueError("用户名不能为空且必须是字符串")
    
    if identity_id is not None and not isinstance(identity_id, str):
        raise ValueError("身份ID必须是字符串类型")
    
    if not isinstance(image, Image.Image):
        raise ValueError("图片必须是PIL.Image对象")
    
    # 人脸检测
    face_boxes, face_images, _ = detect_face(image)
    
    # 检查是否检测到人脸
    if not face_images:
        raise ValueError("未检测到人脸")
    
    # 只取第一张人脸（假设每张图片只有一个人脸）
    if len(face_images) > 1:
        print(f"⚠️ 检测到{len(face_images)}张人脸，只使用第一张人脸进行注册")
    
    face_box = face_boxes[0]
    face_image = face_images[0]
    
    # 提取人脸特征
    feature_vectors = extract_face_feature([face_image])
    if not feature_vectors:
        raise ValueError("特征提取失败")
    
    feature_vector = feature_vectors[0]
    
    # 创建数据库会话
    db = SessionLocal()
    try:
        # 如果未提供身份ID，则自动生成唯一ID
        if identity_id is None:
            identity_id = generate_unique_identity_id(db)
        else:
            # 检查提供的身份ID是否已存在
            existing_user = db.query(User).filter(User.identity_id == identity_id).first()
            if existing_user:
                raise ValueError(f"身份ID '{identity_id}' 已存在")
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # 保存人脸图片
        image_filename = f"{name}_{timestamp}_{unique_id}.jpg"
        image_path = os.path.join(config.FACE_IMAGE_DIR, image_filename)
        
        # 保存图片文件
        face_image.save(image_path, "JPEG", quality=95)
        
        # 保存特征向量
        feature_filename = f"{name}_{timestamp}_{unique_id}.npy"
        feature_path = os.path.join(config.DATA_DIR, "features", feature_filename)
        
        # 确保特征目录存在
        os.makedirs(os.path.dirname(feature_path), exist_ok=True)
        save_face_feature(feature_vector, feature_path)
        
        # 创建用户记录
        new_user = User(
            name=name,
            identity_id=identity_id,
            feature_path=feature_path,
            image_path=image_path
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "success": True,
            "user_id": new_user.id,
            "identity_id": identity_id,
            "message": f"用户 '{name}' 注册成功，生成的身份ID为: {identity_id}"
        }
        
    except ValueError:
        # 重新抛出参数验证错误
        raise
    except Exception as e:
        db.rollback()
        raise Exception(f"数据库操作失败: {str(e)}")
    finally:
        db.close()


def recognize_face(image):
    """
    人脸识别函数 - 从图片中识别人脸并返回匹配结果
    
    处理流程：
    1. 验证输入参数
    2. 检测图片中的所有人脸
    3. 提取每个人脸的特征向量
    4. 加载数据库中所有用户的特征向量
    5. 对比特征向量找出最匹配的用户
    6. 统计并返回匹配结果
    
    Args:
        image (PIL.Image): 待识别的图片
        
    Returns:
        dict: 识别结果
            - total_count (int): 检测到的人脸总数
            - matched_count (int): 匹配成功的人数
            - unmatched_count_db (int): 数据库中未出现人数
            - matched_names (list): 匹配的用户名列表
            - unmatched_names_db (list): 数据库中未出现的用户名列表  
            - face_boxes (list): 人脸坐标列表 [(x1, y1, x2, y2), ...]
            - match_details (list): 详细匹配信息列表
                - face_index (int): 人脸索引
                - matched_user (str): 匹配的用户名（如果匹配成功）
                - similarity (float): 相似度分数
                - face_box (tuple): 人脸坐标
                - error (str or None): 错误信息（如果有）
                
    Raises:
        ValueError: 当输入参数无效、未检测到人脸或数据库中没有有效特征向量时抛出
        Exception: 当数据库操作失败时抛出
    """
    # 参数验证
    if not isinstance(image, Image.Image):
        raise ValueError("图片必须是PIL.Image对象")
    
    # 人脸检测
    face_boxes, face_images, _ = detect_face(image)
    
    # 检查是否检测到人脸
    if not face_images:
        raise ValueError("未检测到人脸")
    
    # 创建数据库会话
    db = SessionLocal()
    try:
        # 获取所有用户
        all_users = db.query(User).all()
        
        if not all_users:
            return {
                "total_count": len(face_images),
                "matched_count": 0,
                "unmatched_count_db": 0,
                "matched_names": [],
                "unmatched_names_db": [],
                "face_boxes": face_boxes,
                "match_details": []
            }
        
        # 加载所有用户的特征向量
        user_features = []
        user_names = []
        
        for user in all_users:
            try:
                feature = load_face_feature(user.feature_path)
                if feature is not None:
                    user_features.append(feature)
                    user_names.append(user.name)
            except Exception as e:
                print(f"⚠️ 加载用户 '{user.name}' 的特征向量失败: {str(e)}")
                continue
        
        if not user_features:
            raise ValueError("数据库中没有有效的特征向量")
        
        # 处理每张人脸
        match_details = []
        matched_names = set()
        
        for i, (face_image, face_box) in enumerate(zip(face_images, face_boxes)):
            # 提取当前人脸的特征
            feature_vectors = extract_face_feature([face_image])
            if not feature_vectors:
                match_details.append({
                    "face_index": i,
                    "matched_user": None,
                    "similarity": 0.0,
                    "face_box": face_box,
                    "error": "特征提取失败"
                })
                continue
            
            current_feature = feature_vectors[0]
            
            # 与数据库中的特征进行比对
            matches, max_similarity = compare_face_features(
                current_feature, 
                user_features, 
                threshold=config.RECOGNITION_THRESHOLD
            )
            
            if matches:
                # 找到匹配的用户
                best_match_index = matches[0][0]  # 最匹配的索引
                best_match_name = user_names[best_match_index]
                best_similarity = matches[0][1]
                
                matched_names.add(best_match_name)
                
                match_details.append({
                    "face_index": i,
                    "matched_user": best_match_name,
                    "similarity": best_similarity,
                    "face_box": face_box,
                    "error": None
                })
                
                print(f"✅ 人脸 {i+1}: 匹配到用户 '{best_match_name}' (相似度: {best_similarity:.3f})")
            else:
                # 未找到匹配
                match_details.append({
                    "face_index": i,
                    "matched_user": None,
                    "similarity": max_similarity,
                    "face_box": face_box,
                    "error": "未找到匹配用户"
                })
                
                print(f"❌ 人脸 {i+1}: 未找到匹配用户 (最高相似度: {max_similarity:.3f})")
        
        # 统计结果
        total_count = len(face_images)
        matched_count = len(matched_names)
        unmatched_count_db = total_count - matched_count
        
        # 获取数据库中未出现的用户名
        all_db_names = set(user_names)
        matched_names_list = list(matched_names)
        unmatched_names_db = list(all_db_names - matched_names)
        
        return {
            "total_count": total_count,
            "matched_count": matched_count,
            "unmatched_count_db": unmatched_count_db,
            "matched_names": matched_names_list,
            "unmatched_names_db": unmatched_names_db,
            "face_boxes": face_boxes,
            "match_details": match_details
        }
        
    except ValueError:
        # 重新抛出参数验证错误
        raise
    except Exception as e:
        raise Exception(f"数据库操作失败: {str(e)}")
    finally:
        db.close()


# 测试和示例代码
if __name__ == "__main__":
    """
    函数调用示例和测试代码
    """
    print("🧪 开始测试数据处理模块...")
    
    # 确保数据库和目录存在
    if __name__ == "__main__":
        from app.models.models import init_db
    else:
        from ..models.models import init_db
    init_db()
    
    # 创建测试图片（生成一张简单的人脸模拟图片）
    test_image = Image.new('RGB', (200, 200), color='white')
    
    print("\n=== 测试1: 人脸注册 ===")
    try:
        # 注意：这里使用模拟图片，实际使用时需要真实的人脸图片
        result = register_face("test_user", test_image)
        print(f"注册结果: {result}")
    except ValueError as e:
        print(f"预期错误（模拟图片无真实人脸）: {e}")
    except Exception as e:
        print(f"其他错误: {e}")
    
    print("\n=== 测试2: 人脸识别 ===")
    try:
        # 注意：这里使用模拟图片，实际使用时需要真实的人脸图片
        result = recognize_face(test_image)
        print(f"识别结果: {result}")
    except ValueError as e:
        print(f"预期错误（模拟图片无真实人脸）: {e}")
    except Exception as e:
        print(f"其他错误: {e}")
    
    print("\n📋 使用说明:")
    print("1. 使用真实的人脸图片进行测试")
    print("2. 确保图片清晰，人脸清晰可见")
    print("3. 注册时用户名不能重复")
    print("4. 识别时会返回详细的人脸匹配信息")
    
    print("\n🔧 异常处理说明:")
    print("- ValueError: 输入参数无效、未检测到人脸、用户名已存在")
    print("- Exception: 数据库操作失败、特征提取失败、文件操作失败")
    print("- 所有异常都会提供明确的错误信息")