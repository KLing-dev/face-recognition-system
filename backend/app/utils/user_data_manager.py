"""用户数据管理模块

该模块提供了用户数据的CRUD操作，特别是针对人脸识别系统的用户数据管理功能。
支持用户信息查询、删除、数据库完整性检查等功能。

典型用法：
    from app.utils.user_data_manager import delete_user, get_user_info
    user_info = get_user_info(user_id)
    delete_result = delete_user(user_id)
"""

import sqlite3
import os
from app.config import Config
import shutil

class UserDataManager:
    """
    用户数据管理器类
    
    提供用户数据的完整CRUD操作，特别是针对人脸识别系统优化的数据管理功能。
    支持用户信息查询、删除、数据库完整性检查等核心功能。
    
    Attributes:
        db_path (str): 数据库文件路径
    """
    
    def __init__(self, db_path=None):
        """
        初始化用户数据管理器
        
        初始化数据库连接，确保数据库文件和目录存在。
        
        Args:
            db_path (str, optional): 数据库路径，默认使用配置文件中的路径
        
        Raises:
            Exception: 当数据库初始化失败时抛出异常
        """
        self.db_path = db_path if db_path else Config.DB_PATH
        # 确保数据库路径存在
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """
        确保数据库文件和目录存在
        
        检查并创建数据库目录和文件，如果它们不存在的话。
        确保数据库操作能够正常进行。
        
        Raises:
            OSError: 当创建目录或数据库文件失败时抛出异常
        """
        # 获取数据库目录
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # 检查数据库文件是否存在，如果不存在则创建
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            conn.close()
    
    def get_user_by_id_or_name(self, user_identifier):
        """
        通过用户ID或用户名查找用户
        
        首先尝试通过identity_id查询用户，如果未找到则尝试通过name查询。
        返回用户的完整信息，包括ID、姓名、特征向量和图像路径。
        
        Args:
            user_identifier (str): 用户ID或用户名
            
        Returns:
            dict or None: 如果找到用户则返回用户数据字典，否则返回None
                字典包含: user_id, user_name, feature_vector, image_path
            
        Raises:
            Exception: 当数据库查询失败时抛出异常
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使用字典形式返回结果
            cursor = conn.cursor()
            
            # 首先尝试通过identity_id查询
            cursor.execute(
                "SELECT identity_id as user_id, name as user_name, feature_path, image_path FROM users WHERE identity_id = ?",
                (user_identifier,)
            )
            user = cursor.fetchone()
            
            # 如果没找到，尝试通过name查询
            if not user:
                cursor.execute(
                    "SELECT identity_id as user_id, name as user_name, feature_path, image_path FROM users WHERE name = ?",
                    (user_identifier,)
                )
                user = cursor.fetchone()
            
            conn.close()
            
            # 转换为字典返回
            return dict(user) if user else None
            
        except Exception as e:
            print(f"查询用户失败: {str(e)}")
            return None
    
    def get_users_by_ids_or_names(self, identifiers):
        """
        通过多个用户ID或用户名查找用户
        
        批量查询匹配给定ID或用户名列表的用户信息。
        返回所有匹配用户的完整信息。
        
        Args:
            identifiers (list): 用户ID或用户名列表
            
        Returns:
            list: 用户数据字典列表，每个字典包含: user_id, user_name, feature_vector, image_path
            
        Raises:
            Exception: 当数据库查询失败时抛出异常
        """
        users = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使用字典形式返回结果
            cursor = conn.cursor()
            
            # 创建查询参数
            placeholders = ','.join(['?'] * len(identifiers))
            
            # 查询匹配任一ID或用户名的用户
            query = f"""
                SELECT identity_id as user_id, name as user_name, feature_path, image_path 
                FROM users 
                WHERE identity_id IN ({placeholders}) OR name IN ({placeholders})
            """
            
            # 构建参数列表（需要重复identifiers两次，因为查询条件有两个IN子句）
            params = identifiers * 2
            cursor.execute(query, params)
            
            # 处理结果
            rows = cursor.fetchall()
            users = [dict(row) for row in rows]
            
            conn.close()
            
        except Exception as e:
            print(f"批量查询用户失败: {str(e)}")
        
        return users
    
    def delete_user_by_id(self, user_id, delete_images=True, dry_run=False):
        """
        通过用户ID删除单个用户数据
        
        删除指定ID的用户数据，可选择是否同时删除关联的图像文件。
        支持模拟删除（dry_run），只检查要删除的内容而不执行实际删除。
        
        Args:
            user_id (str): 用户ID
            delete_images (bool): 是否同时删除关联的图像文件，默认True
            dry_run (bool): 是否为模拟删除（仅检查，不执行实际删除），默认False
            
        Returns:
            dict: 删除操作结果
                - success (bool): 删除是否成功
                - message (str): 操作消息
                - deleted_user (dict or None): 被删除的用户信息
                - deleted_files (list): 被删除的文件路径列表
            
        Raises:
            Exception: 当数据库操作失败时抛出异常
        """
        try:
            print(f"[DEBUG] 开始删除用户，用户ID: {user_id}")
            
            # 先获取用户信息
            user_info = self.get_user_by_id_or_name(user_id)
            
            if not user_info:
                print(f"[DEBUG] 用户不存在: {user_id}")
                return {
                    "success": False,
                    "message": f"用户 ID '{user_id}' 不存在",
                    "deleted_user": None,
                    "deleted_files": []
                }
            
            # 收集需要删除的文件
            files_to_delete = []
            if delete_images and user_info.get('image_path'):
                image_path = user_info['image_path']
                # 确保路径是绝对路径或相对于当前目录
                if not os.path.isabs(image_path):
                    image_path = os.path.join(os.path.dirname(self.db_path), image_path)
                
                if os.path.exists(image_path):
                    files_to_delete.append(image_path)
            
            # 如果是模拟删除，只返回将要删除的内容
            if dry_run:
                return {
                    "success": True,
                    "message": f"模拟删除用户 '{user_info['user_name']}' ({user_info['user_id']})",
                    "deleted_user": user_info,
                    "deleted_files": files_to_delete
                }
            
            # 执行实际删除操作
            # 1. 删除数据库记录
            print(f"[DEBUG] 开始删除数据库记录，用户ID: {user_id}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE identity_id = ?", (user_id,))
            deleted_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            print(f"[DEBUG] 删除数据库记录完成，影响行数: {deleted_rows}")
            
            # 2. 删除关联的图像文件
            deleted_files = []
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    print(f"[DEBUG] 删除文件成功: {file_path}")
                except Exception as e:
                    print(f"删除文件 '{file_path}' 失败: {str(e)}")
            
            print(f"[DEBUG] 删除操作完成，删除文件数: {len(deleted_files)}")
            
            return {
                "success": True,
                "message": f"成功删除用户 '{user_info['user_name']}' ({user_info['user_id']})",
                "deleted_user": user_info,
                "deleted_files": deleted_files
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"删除用户失败: {str(e)}",
                "deleted_user": None,
                "deleted_files": []
            }
    
    def delete_users_by_identifiers(self, identifiers, delete_images=True, require_confirmation=True):
        """
        通过多个标识符（用户ID或用户名）删除多个用户
        
        批量删除匹配给定ID或用户名列表的用户数据。
        支持删除前确认，确保安全操作。
        
        Args:
            identifiers (list): 用户ID或用户名列表
            delete_images (bool): 是否同时删除关联的图像文件，默认True
            require_confirmation (bool): 是否需要确认后再删除，默认True
            
        Returns:
            dict: 删除操作结果
                - success (bool): 是否全部删除成功
                - message (str): 操作消息
                - deleted_count (int): 成功删除的用户数量
                - failed_count (int): 删除失败的用户数量
                - details (list): 每个用户的删除详情
                - confirmation_required (bool, optional): 是否需要确认
                - users_to_confirm (list, optional): 需要确认删除的用户列表
            
        Raises:
            Exception: 当数据库操作失败时抛出异常
        """
        # 首先验证标识符列表
        if not identifiers or not isinstance(identifiers, list):
            return {
                "success": False,
                "message": "无效的用户标识符列表",
                "deleted_count": 0,
                "failed_count": 0,
                "details": []
            }
        
        # 先查询所有匹配的用户
        users_to_delete = self.get_users_by_ids_or_names(identifiers)
        
        # 如果找不到用户
        if not users_to_delete:
            return {
                "success": False,
                "message": "未找到匹配的用户",
                "deleted_count": 0,
                "failed_count": 0,
                "details": []
            }
        
        # 如果需要确认
        if require_confirmation:
            # 这里返回确认信息，需要调用方进行确认
            # 在实际应用中，这里可能会弹出确认对话框
            return {
                "success": False,
                "message": "需要确认删除操作",
                "deleted_count": 0,
                "failed_count": 0,
                "details": [],
                "confirmation_required": True,
                "users_to_confirm": users_to_delete
            }
        
        # 执行批量删除
        results = []
        deleted_count = 0
        failed_count = 0
        
        for user in users_to_delete:
            delete_result = self.delete_user_by_id(
                user['user_id'], 
                delete_images=delete_images,
                dry_run=False
            )
            
            results.append({
                "user_id": user['user_id'],
                "user_name": user['user_name'],
                "success": delete_result['success'],
                "message": delete_result['message'],
                "deleted_files": delete_result['deleted_files']
            })
            
            if delete_result['success']:
                deleted_count += 1
            else:
                failed_count += 1
        
        return {
            "success": failed_count == 0,
            "message": f"批量删除完成：成功 {deleted_count} 个，失败 {failed_count} 个",
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "details": results
        }
    
    def confirm_and_delete_users(self, user_ids):
        """
        确认并删除指定的用户
        
        在用户确认后执行实际删除操作，直接调用delete_users_by_identifiers
        但禁用确认要求，适用于已获得用户确认后的场景。
        
        Args:
            user_ids (list): 要删除的用户ID列表
            
        Returns:
            dict: 删除操作结果，与delete_users_by_identifiers相同格式
                - success (bool): 是否全部删除成功
                - message (str): 操作消息
                - deleted_count (int): 成功删除的用户数量
                - failed_count (int): 删除失败的用户数量
                - details (list): 每个用户的删除详情
            
        Raises:
            Exception: 当数据库操作失败时抛出异常
        """
        # 调用删除方法，不要求再次确认
        return self.delete_users_by_identifiers(
            user_ids,
            delete_images=True,
            require_confirmation=False
        )
    
    def delete_all_users(self, delete_images=True, require_confirmation=True):
        """
        删除所有用户数据
        
        此方法非常危险，会删除数据库中的所有用户记录和相关图像文件。
        默认启用确认机制以防止误操作。
        
        Args:
            delete_images (bool): 是否同时删除关联的图像文件，默认True
            require_confirmation (bool): 是否需要确认后再删除，默认True
            
        Returns:
            dict: 删除操作结果
                - success (bool): 是否删除成功
                - message (str): 操作消息
                - deleted_count (int): 成功删除的用户数量
                - failed_count (int): 删除失败的用户数量
                - deleted_files (list): 被删除的文件路径列表
                - warning (str, optional): 安全警告信息
                - confirmation_required (bool, optional): 是否需要确认
                - users_to_confirm (list, optional): 需要确认删除的用户列表
            
        Raises:
            Exception: 当数据库操作失败时抛出异常
        """
        # 非常危险的操作，默认需要确认
        if require_confirmation:
            # 获取所有用户
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, user_name, feature_vector, image_path FROM users")
            all_users = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return {
                "success": False,
                "message": "需要确认删除所有用户操作",
                "deleted_count": 0,
                "failed_count": 0,
                "details": [],
                "confirmation_required": True,
                "users_to_confirm": all_users,
                "warning": "此操作将删除所有用户数据，包括数据库记录和图像文件，操作不可撤销！"
            }
        
        # 执行全部删除
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 先获取所有用户信息，用于后续删除文件
            cursor.execute("SELECT user_id, image_path FROM users")
            users = cursor.fetchall()
            
            # 删除所有用户记录
            cursor.execute("DELETE FROM users")
            conn.commit()
            conn.close()
            
            # 删除关联的图像文件
            deleted_files = []
            for user in users:
                if delete_images and user[1]:  # user[1] 是 image_path
                    image_path = user[1]
                    if not os.path.isabs(image_path):
                        image_path = os.path.join(os.path.dirname(self.db_path), image_path)
                    
                    if os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                            deleted_files.append(image_path)
                        except Exception as e:
                            print(f"删除文件 '{image_path}' 失败: {str(e)}")
            
            return {
                "success": True,
                "message": f"成功删除所有 {len(users)} 个用户记录",
                "deleted_count": len(users),
                "failed_count": 0,
                "deleted_files": deleted_files,
                "details": []
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"删除所有用户失败: {str(e)}",
                "deleted_count": 0,
                "failed_count": 0,
                "deleted_files": [],
                "details": []
            }
    
    def create_delete_confirmation(self, users):
        """
        为删除操作创建确认信息
        
        为批量删除操作生成格式化的确认信息，包括用户列表和安全警告。
        用于用户界面显示删除确认对话框。
        
        Args:
            users (list): 要删除的用户列表
            
        Returns:
            dict: 确认信息
                - confirmation_text (str): 格式化的确认文本
                - user_count (int): 用户数量
                - user_details (list): 用户详细信息列表
                - safety_warning (str): 安全警告信息
                - required_action (str): 要求用户执行的操作说明
        """
        # 生成用户列表文本
        user_list = "\n".join([f"- {user['user_name']} (ID: {user['user_id']})" for user in users])
        
        return {
            "confirmation_text": f"您确定要删除以下 {len(users)} 个用户吗？\n{user_list}",
            "user_count": len(users),
            "user_details": users,
            "safety_warning": "注意：此操作将永久删除用户数据和相关图像文件，操作不可撤销！",
            "required_action": "请确认是否继续执行删除操作"
        }
    
    def check_database_integrity(self):
        """
        检查数据库完整性
        
        检查数据库中的用户记录与关联的图像文件是否一致，
        查找孤立的图像文件引用或损坏的数据。
        
        Returns:
            dict: 完整性检查结果
                - status (str): 完整性状态，可能的值：'ok', 'warning', 'error'
                - message (str): 检查结果消息
                - issues (list): 发现的问题列表，每项包含问题类型、描述等信息
            
        Raises:
            Exception: 当数据库操作失败时抛出异常
        """
        issues = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询所有用户的图像路径
            cursor.execute("SELECT user_id, user_name, image_path FROM users")
            users = cursor.fetchall()
            conn.close()
            
            # 检查每个图像文件是否存在
            for user in users:
                user_id, user_name, image_path = user
                
                if image_path:
                    # 转换为绝对路径
                    if not os.path.isabs(image_path):
                        image_path = os.path.join(os.path.dirname(self.db_path), image_path)
                    
                    if not os.path.exists(image_path):
                        issues.append({
                            "type": "missing_file",
                            "description": f"用户 '{user_name}' (ID: {user_id}) 的图像文件不存在",
                            "file_path": image_path,
                            "user_id": user_id
                        })
            
            # 如果没有问题
            if not issues:
                return {
                    "status": "ok",
                    "message": "数据库完整性检查通过，未发现问题",
                    "issues": []
                }
            
            return {
                "status": "warning",
                "message": f"发现 {len(issues)} 个潜在问题",
                "issues": issues
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"数据库完整性检查失败: {str(e)}",
                "issues": []
            }

# 提供简化的函数接口供其他模块调用
def delete_user(user_identifier, delete_images=True, dry_run=False):
    """
    删除单个用户的便捷函数
    
    提供简单的接口调用UserDataManager.delete_user_by_id方法。
    删除指定用户的数据库记录和可选的关联图像文件。
    
    Args:
        user_identifier (str): 用户ID或用户名
        delete_images (bool): 是否同时删除图像文件，默认True
        dry_run (bool): 是否为模拟删除，默认False
        
    Returns:
        dict: 删除结果
            - success (bool): 删除是否成功
            - message (str): 操作消息
            - deleted_user (dict or None): 被删除的用户信息
            - deleted_files (list): 被删除的文件路径列表
    """
    manager = UserDataManager()
    return manager.delete_user_by_id(user_identifier, delete_images=delete_images, dry_run=dry_run)

def delete_users(identifiers, delete_images=True, require_confirmation=True):
    """
    删除多个用户的便捷函数
    
    提供简单的接口调用UserDataManager.delete_users_by_identifiers方法。
    批量删除多个用户的数据库记录和可选的关联图像文件。
    
    Args:
        identifiers (list): 用户ID或用户名列表
        delete_images (bool): 是否同时删除图像文件，默认True
        require_confirmation (bool): 是否需要确认，默认True
        
    Returns:
        dict: 删除结果
            - success (bool): 是否全部删除成功
            - message (str): 操作消息
            - deleted_count (int): 成功删除的用户数量
            - failed_count (int): 删除失败的用户数量
            - details (list): 每个用户的删除详情
    """
    manager = UserDataManager()
    return manager.delete_users_by_identifiers(
        identifiers, 
        delete_images=delete_images, 
        require_confirmation=require_confirmation
    )

def confirm_delete(confirmed_user_ids):
    """
    确认并删除用户的便捷函数
    
    提供简单的接口调用UserDataManager.confirm_and_delete_users方法。
    在用户确认后执行实际的删除操作。
    
    Args:
        confirmed_user_ids (list): 已确认删除的用户ID列表
        
    Returns:
        dict: 删除结果
            - success (bool): 是否全部删除成功
            - message (str): 操作消息
            - deleted_count (int): 成功删除的用户数量
            - failed_count (int): 删除失败的用户数量
            - details (list): 每个用户的删除详情
    """
    manager = UserDataManager()
    return manager.confirm_and_delete_users(confirmed_user_ids)

def check_database():
    """
    检查数据库完整性的便捷函数
    
    提供简单的接口调用UserDataManager.check_database_integrity方法。
    检查数据库中的用户记录与关联的图像文件是否一致。
    
    Returns:
        dict: 完整性检查结果
            - status (str): 完整性状态，可能的值：'ok', 'warning', 'error'
            - message (str): 检查结果消息
            - issues (list): 发现的问题列表
    """
    manager = UserDataManager()
    return manager.check_database_integrity()

def get_user_info(user_identifier):
    """
    获取用户信息的便捷函数
    
    提供简单的接口调用UserDataManager.get_user_by_id_or_name方法。
    通过用户ID或用户名查询用户信息。
    
    Args:
        user_identifier (str): 用户ID或用户名
        
    Returns:
        dict or None: 如果找到用户则返回用户数据字典，否则返回None
            字典包含: user_id, user_name, feature_vector, image_path
    """
    manager = UserDataManager()
    return manager.get_user_by_id_or_name(user_identifier)

# 如果作为脚本直接运行，执行简单测试
if __name__ == "__main__":
    print("用户数据管理器初始化完成。")
    print("可用功能:")
    print("  - 删除单个用户: delete_user(user_identifier)")
    print("  - 删除多个用户: delete_users(identifiers)")
    print("  - 确认删除: confirm_delete(confirmed_user_ids)")
    print("  - 获取用户信息: get_user_info(user_identifier)")
    print("  - 检查数据库: check_database()")