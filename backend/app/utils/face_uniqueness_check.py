"""人脸唯一性校验模块 - 提供人脸特征比对、唯一性校验和注册确认功能"""
import sqlite3
import numpy as np
from app.config import Config
from app.utils.face_utils import compare_face_features, extract_face_feature, detect_face
from PIL import Image
import io
import base64

class FaceUniquenessChecker:
    """
    人脸唯一性校验器类 - 提供人脸特征比对、唯一性校验和提示功能
    """
    
    # 唯一性校验阈值设置
    # 建议值：比识别阈值稍低，以减少误判
    UNIQUENESS_THRESHOLD = 0.5  # 人脸唯一性校验阈值
    
    def __init__(self, db_path=None):
        """
        初始化人脸唯一性校验器
        
        Args:
            db_path (str, optional): 数据库路径
        """
        self.db_path = db_path if db_path else Config.DATABASE_PATH
        
    def check_face_uniqueness(self, face_image, threshold=None):
        """
        检查人脸是否唯一（尚未注册）
        
        Args:
            face_image (PIL.Image): 待检查的人脸图像
            threshold (float, optional): 自定义唯一性阈值
            
        Returns:
            dict: 校验结果字典
                - is_unique: 是否唯一
                - message: 提示信息
                - similar_users: 相似用户列表 [{'user_id': '', 'user_name': '', 'similarity': 0.0}]
                - max_similarity: 最高相似度
        
        Raises:
            Exception: 当校验过程中发生异常时抛出
        """
        try:
            # 使用自定义阈值或默认阈值
            current_threshold = threshold if threshold is not None else self.UNIQUENESS_THRESHOLD
            
            # 1. 从人脸图像中提取特征
            face_features = self._extract_features_from_image(face_image)
            
            if not face_features:
                return {
                    "is_unique": False,
                    "message": "无法从图像中提取人脸特征",
                    "similar_users": [],
                    "max_similarity": 0.0
                }
            
            # 2. 从数据库加载所有已注册用户的特征
            db_user_data = self._load_all_user_features()
            
            if not db_user_data:
                # 数据库为空，表示这是第一个用户
                return {
                    "is_unique": True,
                    "message": "数据库为空，这是第一个注册用户",
                    "similar_users": [],
                    "max_similarity": 0.0
                }
            
            # 3. 提取特征向量列表
            db_features = [np.array(data['feature_vector']) for data in db_user_data]
            
            # 4. 进行特征比对
            matches, max_similarity = compare_face_features(
                face_features[0],  # 当前只有一个人脸的特征
                db_features,
                threshold=current_threshold
            )
            
            # 5. 分析比对结果
            similar_users = []
            
            # 查找所有相似度超过阈值的用户
            for index, similarity in matches:
                if similarity >= current_threshold:
                    user_info = db_user_data[index]
                    similar_users.append({
                        "user_id": user_info['user_id'],
                        "user_name": user_info['user_name'],
                        "similarity": float(similarity),
                        "image_path": user_info.get('image_path', '')
                    })
            
            # 按相似度降序排序
            similar_users.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 6. 生成结果
            if similar_users:
                # 找到相似用户
                top_similar_user = similar_users[0]
                
                # 根据相似度程度生成不同的提示信息
                if max_similarity >= 0.75:
                    message = f"高度相似！该人脸与用户 '{top_similar_user['user_name']}' ({top_similar_user['user_id']}) 相似度高达 {max_similarity:.2%}，可能已注册。"
                elif max_similarity >= 0.65:
                    message = f"中度相似！该人脸与用户 '{top_similar_user['user_name']}' ({top_similar_user['user_id']}) 相似度为 {max_similarity:.2%}，请确认是否为同一人。"
                else:
                    message = f"低度相似！该人脸与用户 '{top_similar_user['user_name']}' ({top_similar_user['user_id']}) 相似度为 {max_similarity:.2%}，可能为同一人。"
                
                return {
                    "is_unique": False,
                    "message": message,
                    "similar_users": similar_users,
                    "max_similarity": float(max_similarity)
                }
            else:
                # 未找到相似用户
                return {
                    "is_unique": True,
                    "message": f"人脸未注册，相似度校验通过（最高相似度: {max_similarity:.2%}）",
                    "similar_users": [],
                    "max_similarity": float(max_similarity)
                }
                
        except Exception as e:
            # 校验过程出错
            return {
                "is_unique": False,
                "message": f"人脸唯一性校验失败: {str(e)}",
                "similar_users": [],
                "max_similarity": 0.0
            }
    
    def _extract_features_from_image(self, face_image):
        """
        从人脸图像中提取特征向量
        
        Args:
            face_image (PIL.Image or str): 人脸图像或Base64编码的图像数据
            
        Returns:
            list: 特征向量列表，失败返回空列表
        
        Raises:
            TypeError: 当输入类型无效时抛出
        """
        try:
            # 首先确保图像是PIL Image对象
            if not isinstance(face_image, Image.Image):
                # 如果是Base64数据，尝试解码
                if isinstance(face_image, str) and face_image.startswith('data:image/'):
                    # 移除数据头
                    header, base64_data = face_image.split(',', 1)
                    # 解码Base64数据
                    image_data = base64.b64decode(base64_data)
                    face_image = Image.open(io.BytesIO(image_data)).convert('RGB')
                else:
                    raise TypeError("输入必须是PIL Image对象或Base64编码的图像数据")
            
            # 检查是否需要先检测人脸（如果输入是完整图像）
            # 尝试检测人脸
            face_boxes, face_images, _ = detect_face(face_image)
            
            if not face_images:
                # 如果没检测到人脸，但输入图像已经是裁剪好的人脸
                # 假设输入的就是人脸图像
                face_images = [face_image.resize((160, 160), Image.BILINEAR)]
            
            # 提取特征
            features = extract_face_feature(face_images)
            
            return features
            
        except Exception as e:
            print(f"特征提取失败: {str(e)}")
            return []
    
    def _load_all_user_features(self):
        """
        从数据库加载所有用户的特征数据
        
        Returns:
            list: 用户数据列表 [{'user_id': '', 'user_name': '', 'feature_vector': []}]
        
        Raises:
            Exception: 当数据库操作失败时抛出
        """
        user_data = []
        
        try:
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使用字典形式返回结果
            cursor = conn.cursor()
            
            # 查询所有用户数据
            query = """
                SELECT user_id, user_name, feature_vector, image_path 
                FROM users 
                WHERE feature_vector IS NOT NULL
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # 处理查询结果
            for row in rows:
                # 解析特征向量字符串为numpy数组
                try:
                    # 移除括号和空格，然后分割成数字字符串列表
                    feature_str = row['feature_vector'].strip('[]')
                    feature_vector = np.array([float(x) for x in feature_str.split(',')])
                    
                    user_data.append({
                        'user_id': row['user_id'],
                        'user_name': row['user_name'],
                        'feature_vector': feature_vector,
                        'image_path': row.get('image_path', '')
                    })
                except Exception as e:
                    print(f"解析用户 {row['user_id']} 的特征向量失败: {str(e)}")
                    continue
            
            # 关闭连接
            conn.close()
            
        except Exception as e:
            print(f"加载用户特征数据失败: {str(e)}")
        
        return user_data
    
    def get_similarity_level(self, similarity):
        """
        根据相似度值返回相似度级别描述
        
        Args:
            similarity (float): 相似度值 (0.0-1.0)
            
        Returns:
            tuple: (级别, 描述)
        """
        if similarity >= 0.85:
            return "极高", "几乎可以确定是同一人"
        elif similarity >= 0.75:
            return "高", "很可能是同一人"
        elif similarity >= 0.65:
            return "中等", "可能是同一人"
        elif similarity >= 0.55:
            return "低", "略微相似，可能不是同一人"
        else:
            return "极低", "几乎不可能是同一人"
    
    def generate_confirmation_prompt(self, check_result):
        """
        生成二次确认提示信息
        
        Args:
            check_result (dict): 唯一性校验结果
            
        Returns:
            dict: 确认提示信息
                - prompt_type: 'warning', 'info', 'error'
                - title: 提示标题
                - message: 提示内容
                - action_required: 是否需要用户操作
                - similar_users: 相似用户列表（如果有）
        """
        if check_result['is_unique']:
            # 人脸唯一，直接提示成功
            return {
                "prompt_type": "info",
                "title": "注册确认",
                "message": "人脸唯一性校验通过，可以继续注册流程。",
                "action_required": False,
                "similar_users": []
            }
        else:
            # 找到相似用户，需要二次确认
            similar_users = check_result['similar_users']
            max_similarity = check_result['max_similarity']
            
            # 获取相似度级别
            level, description = self.get_similarity_level(max_similarity)
            
            # 构建提示消息
            if similar_users:
                top_user = similar_users[0]
                message = f"检测到人脸可能已注册！" \
                          f"与用户 '{top_user['user_name']}' ({top_user['user_id']}) 的相似度为 {max_similarity:.2%}，" \
                          f"{description}。\n\n" \
                          f"您确定要继续注册吗？"
            else:
                message = "人脸唯一性校验失败，请重试。"
            
            return {
                "prompt_type": "warning" if level != "极高" else "error",
                "title": f"人脸相似度警告（{level}）",
                "message": message,
                "action_required": True,
                "similar_users": similar_users
            }
    
    def verify_registration_permission(self, check_result, user_confirmation=False):
        """
        验证用户是否有权限继续注册
        
        Args:
            check_result (dict): 唯一性校验结果
            user_confirmation (bool): 用户是否确认继续注册（当检测到相似人脸时）
            
        Returns:
            dict: 权限验证结果
                - allowed: 是否允许注册
                - reason: 允许或拒绝的原因
                - action: 建议的下一步操作
        """
        # 如果人脸唯一，直接允许注册
        if check_result['is_unique']:
            return {
                "allowed": True,
                "reason": "人脸唯一，通过唯一性校验",
                "action": "继续注册流程"
            }
        
        # 检查相似度是否极高（可能是同一人）
        max_similarity = check_result['max_similarity']
        if max_similarity >= 0.85:
            # 极高相似度，需要用户确认
            if user_confirmation:
                return {
                    "allowed": True,
                    "reason": "尽管检测到极高相似度，但用户确认继续注册",
                    "action": "继续注册流程，但建议检查是否为重复注册"
                }
            else:
                return {
                    "allowed": False,
                    "reason": "检测到极高相似度人脸，疑似重复注册",
                    "action": "请确认是否为同一人，如需继续请手动确认"
                }
        
        # 中等相似度，需要用户确认
        if max_similarity >= 0.65:
            if user_confirmation:
                return {
                    "allowed": True,
                    "reason": "用户已确认继续注册",
                    "action": "继续注册流程"
                }
            else:
                return {
                    "allowed": False,
                    "reason": "检测到相似人脸",
                    "action": "请确认是否继续注册"
                }
        
        # 低相似度，可以提示但允许注册
        return {
            "allowed": True,
            "reason": "相似度较低，可能是不同的人",
            "action": "继续注册流程"
        }

# 提供简化的函数接口供其他模块调用
def check_face_is_unique(face_image, threshold=None):
    """
    检查人脸是否唯一的便捷函数
    
    Args:
        face_image (PIL.Image): 人脸图像
        threshold (float, optional): 自定义阈值
        
    Returns:
        dict: 校验结果字典
            - is_unique: 是否唯一
            - message: 提示信息
            - similar_users: 相似用户列表
            - max_similarity: 最高相似度
    """
    checker = FaceUniquenessChecker()
    return checker.check_face_uniqueness(face_image, threshold)

def generate_confirmation_message(check_result):
    """
    生成确认消息的便捷函数
    
    Args:
        check_result (dict): 校验结果
        
    Returns:
        dict: 确认提示信息
            - prompt_type: 'warning', 'info', 'error'
            - title: 提示标题
            - message: 提示内容
            - action_required: 是否需要用户操作
            - similar_users: 相似用户列表（如果有）
    """
    checker = FaceUniquenessChecker()
    return checker.generate_confirmation_prompt(check_result)

def validate_registration_permission(check_result, user_confirmation=False):
    """
    验证注册权限的便捷函数
    
    Args:
        check_result (dict): 校验结果
        user_confirmation (bool): 用户确认
        
    Returns:
        dict: 权限验证结果
            - allowed: 是否允许注册
            - reason: 允许或拒绝的原因
            - action: 建议的下一步操作
    """
    checker = FaceUniquenessChecker()
    return checker.verify_registration_permission(check_result, user_confirmation)

# 测试函数
def test_face_uniqueness_check(face_image_path):
    """
    测试人脸唯一性校验功能
    
    Args:
        face_image_path (str): 测试人脸图像路径
        
    Returns:
        dict: 测试结果
            - test_passed: 是否测试通过
            - check_result: 校验结果
            - confirmation: 确认提示
            - permission: 权限验证结果
            - error: 错误信息（如果测试失败）
    """
    try:
        # 打开测试图像
        face_image = Image.open(face_image_path).convert('RGB')
        
        # 创建校验器
        checker = FaceUniquenessChecker()
        
        # 执行校验
        result = checker.check_face_uniqueness(face_image)
        
        # 生成确认提示
        confirmation = checker.generate_confirmation_prompt(result)
        
        # 测试权限验证
        permission = checker.verify_registration_permission(result, user_confirmation=True)
        
        return {
            "test_passed": True,
            "check_result": result,
            "confirmation": confirmation,
            "permission": permission
        }
        
    except Exception as e:
        return {
            "test_passed": False,
            "error": str(e)
        }

# 如果作为脚本直接运行，执行简单测试
if __name__ == "__main__":
    print("人脸唯一性校验器初始化完成，可以通过调用相应函数进行测试。")
    print("示例用法:")
    print("  from app.utils.face_uniqueness_check import check_face_is_unique")
    print("  result = check_face_is_unique(face_image)")
    print(f"  当前默认唯一性阈值: {FaceUniquenessChecker.UNIQUENESS_THRESHOLD}")