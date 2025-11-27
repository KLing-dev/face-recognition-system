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
from sqlalchemy import text

# 处理相对导入问题
if __name__ == "__main__":
    # 直接运行时添加backend目录到Python路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    sys.path.insert(0, backend_dir)
    from app.config import config
    from app.models.models import User, get_db, SessionLocal
    from app.utils.face_utils import detect_face, extract_face_feature, save_face_feature, load_face_feature, compare_face_features
    from app.utils.user_id_generator import generate_new_user_id, validate_user_id_format, check_user_id_uniqueness
    from app.utils.user_data_manager import delete_user, delete_users
else:
    # 作为模块导入时使用相对导入
    from app.utils.user_data_manager import delete_user, delete_users
    from ..config import config
    from ..models.models import User, get_db, SessionLocal
    from .face_utils import detect_face, extract_face_feature, save_face_feature, load_face_feature, compare_face_features
    from .user_id_generator import generate_new_user_id, validate_user_id_format, check_user_id_uniqueness


def generate_unique_identity_id(db):
    """
    生成唯一身份ID的辅助函数
    
    使用user_id_generator模块中的功能生成唯一身份ID，
    确保唯一性且格式标准。
    
    Args:
        db: 数据库会话对象（保持参数兼容性，但实际实现已使用独立模块）
        
    Returns:
        str: 唯一的身份ID
    """
    # 使用统一的用户ID生成器生成唯一ID
    identity_id = generate_new_user_id()
    
    # 确保生成的ID在数据库中确实唯一
    while db.query(User).filter(User.identity_id == identity_id).first():
        # 如果ID已存在（极低概率），重新生成
        identity_id = generate_new_user_id()
    
    return identity_id


def register_face(name, image, identity_id=None):
    """
    人脸注册函数 - 注册新用户并保存人脸信息，并实施严格的人脸与身份ID绑定机制
    
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
        ValueError: 当输入参数无效、未检测到人脸、人脸质量不满足要求或身份ID已存在时抛出
        Exception: 当数据库操作失败时抛出
    """
    # 参数验证
    if not name or not isinstance(name, str):
        raise ValueError("[注册阻断] 用户名不能为空且必须是字符串格式。请输入有效的用户名后重试。")
    
    if identity_id is not None and not isinstance(identity_id, str):
        raise ValueError("[注册阻断] 身份ID必须是字符串类型。请不指定身份ID以自动生成，或输入有效的字符串格式身份ID。")
    
    if not isinstance(image, Image.Image):
        raise ValueError("[注册阻断] 图片格式无效。请提供有效的图像文件。")
    
    # 人脸检测 - 实现严格的面部检测与验证
    face_boxes, face_images, confidences = detect_face(image)
    
    # 检查是否检测到人脸
    if not face_images:
        raise ValueError("[注册阻断] 未检测到人脸，请确保图像中有人脸且光线充足。人脸检测是注册的必要条件，请重新拍摄包含清晰人脸的照片。")
    
    # 只取第一张人脸（假设每张图片只有一个人脸）
    if len(face_images) > 1:
        print(f"⚠️ 检测到{len(face_images)}张人脸，只使用第一张人脸进行注册")
    
    face_box = face_boxes[0]
    face_image = face_images[0]
    confidence = confidences[0] if confidences else 0
    
    # 增强人脸质量验证 - 要求更高的置信度
    MIN_CONFIDENCE_THRESHOLD = 0.85
    if confidence < MIN_CONFIDENCE_THRESHOLD:
        raise ValueError(f"[注册阻断] 人脸图像质量不满足要求。当前置信度为: {confidence:.2f}，要求最低置信度: {MIN_CONFIDENCE_THRESHOLD}。请重新拍摄，确保人脸清晰可见，光线充足，避免遮挡。")
    
    # 验证人脸图像尺寸 - 确保人脸足够大且清晰
    face_width, face_height = face_image.size
    MIN_FACE_SIZE = 100  # 最小人脸尺寸要求
    if face_width < MIN_FACE_SIZE or face_height < MIN_FACE_SIZE:
        raise ValueError(f"[注册阻断] 人脸图像尺寸过小。检测到人脸尺寸: {face_width}x{face_height}px，要求最小尺寸: {MIN_FACE_SIZE}x{MIN_FACE_SIZE}px。请将人脸靠近摄像头，确保人脸占据画面的主要部分。")
    
    # 提取人脸特征
    feature_vectors = extract_face_feature([face_image])
    if not feature_vectors:
        raise ValueError("[注册阻断] 人脸特征提取失败。可能是因为人脸质量不佳或存在遮挡。请确保拍摄的人脸清晰、完整、无遮挡。")
    
    feature_vector = feature_vectors[0]
    
    # 创建数据库会话 - 在整个注册流程中只使用一个会话
    db = SessionLocal()
    try:
        # 1. 处理身份ID - 确保唯一性和格式正确
        if identity_id is not None:
            # 验证身份ID格式
            is_valid, msg = validate_user_id_format(identity_id)
            if not is_valid:
                raise ValueError(f"[注册阻断] 身份ID格式无效: {msg}。请不指定身份ID以使用系统自动生成的有效身份ID。")
                
            # 检查提供的身份ID是否已存在
            existing_id = db.query(User).filter(User.identity_id == identity_id).first()
            if existing_id:
                raise ValueError(f"[注册阻断] 身份ID '{identity_id}' 已存在。每个人脸必须对应唯一的身份ID，请不指定身份ID以自动生成，或使用其他未被使用的身份ID。")
        else:
            # 生成唯一的身份ID
            identity_id = generate_unique_identity_id(db)
            
            # 双重检查自动生成的ID是否确实唯一
            while db.query(User).filter(User.identity_id == identity_id).first():
                identity_id = generate_unique_identity_id(db)
        
        # 2. 人脸唯一性校验机制 - 核心的'一人一脸一ID'实现
        # 验证当前人脸是否已存在于系统中
        existing_users = db.query(User).all()
        db_features = []
        db_users = []
        
        for user in existing_users:
            try:
                existing_feature = load_face_feature(user.feature_path)
                if existing_feature is not None:
                    db_features.append(existing_feature)
                    db_users.append(user)
            except Exception as e:
                print(f"⚠️ 加载用户 '{user.name}' 的特征向量失败: {str(e)}")
                continue
        
        # 如果数据库中有特征向量，进行人脸唯一性校验
        if db_features:
            # 使用更高的阈值来确保唯一性（比识别阈值更严格）
            UNIQUENESS_THRESHOLD = 0.50  # 比默认识别阈值0.55更严格
            
            # 比较当前人脸特征与数据库中的所有特征
            matches, max_similarity = compare_face_features(
                feature_vector, 
                db_features, 
                threshold=UNIQUENESS_THRESHOLD
            )
            
            if matches:
                # 找到匹配的用户，获取最相似的用户信息
                best_match_index = matches[0][0]
                matched_user = db_users[best_match_index]
                
                # 阻断机制：发现人脸已注册，立即终止注册
                raise ValueError(f"[注册阻断] 该人脸已注册，不可重复注册。根据'一人一脸一ID'原则，当前人脸已与身份ID '{matched_user.identity_id}' (用户: {matched_user.name}) 绑定。如需更新信息，请使用现有身份ID进行更新操作。")
        
        # 3. 生成文件路径和文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # 保存人脸图片
        image_filename = f"{name}_{timestamp}_{unique_id}.jpg"
        image_path = os.path.join(config.FACE_IMAGE_DIR, image_filename)
        
        # 保存特征向量
        feature_filename = f"{name}_{timestamp}_{unique_id}.npy"
        feature_path = os.path.join(config.DATA_DIR, "features", feature_filename)
        
        # 确保目录存在
        os.makedirs(config.FACE_IMAGE_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(feature_path), exist_ok=True)
        
        # 4. 保存数据
        face_image.save(image_path, "JPEG", quality=95)
        save_face_feature(feature_vector, feature_path)
        
        # 5. 创建用户记录 - 完成'一人一脸一ID'绑定
        new_user = User(
            name=name,
            identity_id=identity_id,  # 严格绑定身份ID
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
            raise Exception(f"[注册阻断] 系统内部错误: {str(e)}。注册流程已终止，请稍后重试或联系系统管理员。")
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
                    "similarity": float(0.0),  # 确保是Python原生float
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
                    "similarity": float(best_similarity),  # 确保转换为Python原生float
                    "face_box": face_box,
                    "error": None
                })
                
                print(f"✅ 人脸 {i+1}: 匹配到用户 '{best_match_name}' (相似度: {best_similarity:.3f})")
            else:
                # 未找到匹配
                match_details.append({
                    "face_index": i,
                    "matched_user": None,
                    "similarity": float(max_similarity),  # 确保转换为Python原生float
                    "face_box": face_box,
                    "error": "未找到匹配用户"
                })
                
                print(f"❌ 人脸 {i+1}: 未找到匹配用户 (最高相似度: {max_similarity:.3f})")
        
        # 统计结果
        total_count = len(face_images)
        matched_count = len(matched_names)
        # 修正计算：数据库中存在但未出现在当前识别中的用户数
        unmatched_count_db = len(user_names) - matched_count
        
        # 获取数据库中未出现的用户名
        all_db_names = set(user_names)
        matched_names_list = list(matched_names)
        unmatched_names_db = list(all_db_names - matched_names)
        
        # 转换人脸框为Python原生类型（如果是NumPy数组）
        if face_boxes:
            # 确保face_boxes中的每个元素都是包含Python原生类型的元组
            processed_face_boxes = []
            for box in face_boxes:
                # 处理不同情况的人脸框数据
                if isinstance(box, (list, tuple, np.ndarray)):
                    processed_face_boxes.append(tuple(float(coord) for coord in box))
                else:
                    processed_face_boxes.append(box)  # 如果是其他类型，保持不变
            face_boxes = processed_face_boxes
        else:
            face_boxes = []
        
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


def get_statistics():
    """
    获取系统统计数据
    
    Returns:
        dict: 包含统计信息的字典（仅数据部分，不包含code/message包装）
    """
    try:
        # 获取数据库会话
        if __name__ == "__main__":
            from app.models.models import SessionLocal
        else:
            from ..models.models import SessionLocal
        
        db = SessionLocal()
        
        try:
            # 查询总用户数
            total_users = db.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
            
            # 查询今日活跃用户数
            from datetime import datetime, timedelta
            today = datetime.now().date()
            active_today = db.execute(
                text("SELECT COUNT(DISTINCT user_id) FROM recognition_logs WHERE date(timestamp) = :today"),
                {"today": today}
            ).fetchone()[0]
            
            # 查询总识别次数
            recognition_count = db.execute(text("SELECT COUNT(*) FROM recognition_logs")).fetchone()[0]
            
            # 只返回数据部分，不包装code/message
            return {
                "total_users": total_users,
                "active_today": active_today,
                "recognition_count": recognition_count
            }
        except Exception as e:
            # 发生错误时返回空数据
            return {
                "total_users": 0,
                "active_today": 0,
                "recognition_count": 0
            }
        finally:
            db.close()
    except Exception as e:
        # 发生系统错误时返回空数据
        return {
            "total_users": 0,
            "active_today": 0,
            "recognition_count": 0
        }

def delete_user_by_id(user_id):
    """
    删除指定ID的用户
    
    Args:
        user_id (str): 用户ID
    
    Returns:
        dict: 包含删除结果的字典
    """
    try:
        # 调用user_data_manager中的delete_user函数
        result = delete_user(user_id)
        
        if result['success']:
            return {
                "success": True,
                "message": "用户删除成功",
                "deleted_user_id": user_id
            }
        else:
            return {
                "success": False,
                "message": result['message'],
                "deleted_user_id": None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"删除用户时发生错误: {str(e)}",
            "deleted_user_id": None
        }

def batch_delete_users(user_ids):
    """
    批量删除用户
    
    Args:
        user_ids (list): 用户ID列表
    
    Returns:
        dict: 包含批量删除结果的字典
    """
    try:
        # 调用user_data_manager中的delete_users函数
        result = delete_users(user_ids, delete_images=True, require_confirmation=False)
        
        # 提取失败的ID列表
        failed_ids = []
        for detail in result.get('details', []):
            if not detail.get('success', False):
                failed_ids.append(detail.get('user_id'))
        
        return {
            "success": result.get('success', False),
            "success_count": result.get('deleted_count', 0),
            "failed_count": result.get('failed_count', 0),
            "failed_ids": failed_ids,
            "message": result.get('message', '批量删除完成')
        }
    except Exception as e:
        return {
            "success": False,
            "success_count": 0,
            "failed_count": len(user_ids),
            "failed_ids": user_ids,
            "message": f"批量删除用户时发生错误: {str(e)}"
        }