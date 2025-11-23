import datetime
import sqlite3
import re
from app.config import Config

class UserIDGenerator:
    """
    用户编号生成器类
    
    负责生成、验证和检查用户编号的唯一性，支持标准编号和
    自定义前缀编号生成。采用时间戳和序列组合的方式确保唯一性。
    
    Attributes:
        ID_PREFIX (str): 默认编号前缀
        ID_LENGTH (int): 默认编号总长度
        SEQUENCE_LENGTH (int): 序列部分长度
    """
    
    # 编号规则常量
    ID_PREFIX = "USR"  # 编号前缀
    ID_LENGTH = 10     # 编号总长度
    SEQUENCE_LENGTH = 4  # 序列部分长度
    
    @classmethod
    def generate_user_id(cls, db_path=None):
        """
        生成用户编号
        
        基于日期和序列号生成唯一的用户ID，确保编号的唯一性和顺序性。
        每天从1开始重新计数，格式为：USR + 年月日 + 3位序号。
        
        Args:
            db_path (str, optional): 数据库路径，默认使用配置文件中的路径
            
        Returns:
            str: 生成的用户编号，格式为：USR + 年月日 + 3位序号
            
        Raises:
            Exception: 当数据库操作失败时抛出异常
        """
        try:
            # 获取数据库连接
            if db_path is None:
                db_path = Config.DATABASE_PATH
            
            # 生成日期部分 (YYMMDD格式)
            today = datetime.datetime.now()
            date_part = today.strftime("%y%m%d")
            
            # 构建今天的编号前缀
            today_prefix = f"{cls.ID_PREFIX}{date_part}"
            
            # 从数据库中查找今天已生成的最大序号
            max_sequence = cls._get_max_sequence_for_today(db_path, today_prefix)
            
            # 生成新序号
            new_sequence = max_sequence + 1
            
            # 格式化序号（前面补0）
            sequence_str = str(new_sequence).zfill(cls.SEQUENCE_LENGTH)
            
            # 组合完整编号
            user_id = f"{today_prefix}{sequence_str}"
            
            return user_id
            
        except Exception as e:
            raise Exception(f"用户编号生成失败: {str(e)}")
    
    @classmethod
    def _get_max_sequence_for_today(cls, db_path, today_prefix):
        """
        获取今天的最大序列号
        
        查询数据库中今天已生成的最大序列号，用于生成下一个编号。
        
        Args:
            db_path (str): 数据库路径
            today_prefix (str): 今天的前缀（USR+年月日）
            
        Returns:
            int: 最大序列号，如果没有找到则返回0
            
        Raises:
            Exception: 当数据库操作失败时抛出异常
        """
        try:
            # 连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查询今天已生成的用户ID
            query = "SELECT user_id FROM users WHERE user_id LIKE ? ORDER BY user_id DESC LIMIT 1"
            cursor.execute(query, (f"{today_prefix}%",))
            result = cursor.fetchone()
            
            # 关闭连接
            conn.close()
            
            # 如果找到了记录，提取序号部分
            if result:
                last_user_id = result[0]
                # 提取序号部分（去掉前缀和日期部分）
                sequence_part = last_user_id[len(cls.ID_PREFIX) + 6:]  # 6是日期部分长度
                
                # 验证是否为数字并转换
                if sequence_part.isdigit():
                    return int(sequence_part)
            
            # 如果没有记录或解析失败，返回0
            return 0
            
        except Exception as e:
            # 如果数据库查询失败，记录日志但仍尝试生成ID
            print(f"数据库查询失败，将使用备选方案: {str(e)}")
            return 0
    
    @classmethod
    def validate_user_id(cls, user_id):
        """
        验证用户编号格式是否正确
        
        Args:
            user_id (str): 待验证的用户编号
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        # 检查格式
        pattern = f"^{cls.ID_PREFIX}\d{{10}}$".format(cls.ID_PREFIX)
        if not re.match(pattern, user_id):
            return False, f"用户编号格式错误，应为: {cls.ID_PREFIX} + 6位日期 + 4位序号"
        
        # 检查日期部分是否合法
        date_str = user_id[len(cls.ID_PREFIX):len(cls.ID_PREFIX) + 6]
        try:
            # 解析日期
            year = int("20" + date_str[:2])  # 添加20前缀转换为4位年份
            month = int(date_str[2:4])
            day = int(date_str[4:6])
            
            # 验证日期有效性
            datetime.datetime(year, month, day)
        except ValueError:
            return False, "用户编号中的日期部分无效"
        
        return True, "用户编号格式有效"
    
    @classmethod
    def is_id_unique(cls, user_id, db_path=None):
        """
        检查用户编号是否已存在
        
        Args:
            user_id (str): 待检查的用户编号
            db_path (str, optional): 数据库路径
            
        Returns:
            bool: 是否唯一
        """
        try:
            # 获取数据库连接
            if db_path is None:
                db_path = Config.DATABASE_PATH
            
            # 连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查询编号是否已存在
            query = "SELECT COUNT(*) FROM users WHERE user_id = ?"
            cursor.execute(query, (user_id,))
            count = cursor.fetchone()[0]
            
            # 关闭连接
            conn.close()
            
            # 如果计数为0，则表示唯一
            return count == 0
            
        except Exception as e:
            # 如果数据库查询失败，默认返回False（安全起见）
            print(f"数据库查询失败: {str(e)}")
            return False
    
    @classmethod
    def generate_sequential_id(cls, start_id="00001", db_path=None):
        """
        生成顺序编号（备选方案）
        格式: USR + 5位序号
        
        Args:
            start_id (str): 起始序号
            db_path (str, optional): 数据库路径
            
        Returns:
            str: 生成的用户编号
        """
        try:
            # 获取数据库连接
            if db_path is None:
                db_path = Config.DATABASE_PATH
            
            # 连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查询所有以USR开头的编号
            query = "SELECT user_id FROM users WHERE user_id LIKE ? ORDER BY user_id DESC LIMIT 1"
            cursor.execute(query, ("USR%",))
            result = cursor.fetchone()
            
            # 关闭连接
            conn.close()
            
            # 如果找到了记录，提取序号
            if result:
                last_id = result[0]
                # 提取数字部分
                number_part = "".join(filter(str.isdigit, last_id))
                if number_part:
                    last_number = int(number_part)
                    new_number = last_number + 1
                else:
                    new_number = int(start_id)
            else:
                new_number = int(start_id)
            
            # 格式化新编号
            user_id = f"{cls.ID_PREFIX}{new_number:05d}"
            
            return user_id
            
        except Exception:
            # 如果失败，生成一个基于时间戳的备用编号
            timestamp = str(int(datetime.datetime.now().timestamp()))[-5:]
            return f"{cls.ID_PREFIX}{timestamp}"
    
    @classmethod
    def generate_id_with_prefix(cls, custom_prefix="", db_path=None):
        """
        生成带自定义前缀的用户编号
        
        Args:
            custom_prefix (str): 自定义前缀（2-4个字符）
            db_path (str, optional): 数据库路径
            
        Returns:
            str: 生成的用户编号
        """
        try:
            # 验证自定义前缀
            if custom_prefix:
                # 确保前缀只包含字母和数字，且长度在2-4个字符
                if not re.match(r'^[A-Za-z0-9]{2,4}$', custom_prefix):
                    raise ValueError("自定义前缀必须是2-4个字母或数字")
                
                # 统一转换为大写
                custom_prefix = custom_prefix.upper()
            else:
                custom_prefix = cls.ID_PREFIX
            
            # 生成时间戳部分
            timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
            
            # 从数据库中查找类似前缀的最大序号
            max_sequence = cls._get_max_sequence_for_prefix(db_path, custom_prefix)
            
            # 生成新序号
            new_sequence = max_sequence + 1
            sequence_str = str(new_sequence).zfill(3)
            
            # 组合完整编号
            user_id = f"{custom_prefix}{timestamp}{sequence_str}"
            
            # 如果编号过长，截断时间戳部分
            if len(user_id) > 20:
                # 保留前缀、日期部分和序号
                user_id = f"{custom_prefix}{timestamp[:6]}{sequence_str}"
            
            return user_id
            
        except Exception as e:
            # 如果失败，返回标准编号
            return cls.generate_user_id(db_path)
    
    @classmethod
    def _get_max_sequence_for_prefix(cls, db_path, prefix):
        """
        获取指定前缀的最大序号
        
        Args:
            db_path (str): 数据库路径
            prefix (str): 自定义前缀
            
        Returns:
            int: 最大序号
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            query = "SELECT user_id FROM users WHERE user_id LIKE ? ORDER BY user_id DESC LIMIT 1"
            cursor.execute(query, (f"{prefix}%",))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                # 尝试提取序号部分（假设最后3位是序号）
                last_id = result[0]
                if len(last_id) >= 3:
                    sequence_part = last_id[-3:]
                    if sequence_part.isdigit():
                        return int(sequence_part)
            
            return 0
            
        except Exception:
            return 0

# 提供简化的函数接口供其他模块调用
def generate_new_user_id():
    """
    生成新的用户编号
    
    Returns:
        str: 生成的用户编号
    """
    return UserIDGenerator.generate_user_id()

def validate_user_id_format(user_id):
    """
    验证用户编号格式
    
    Args:
        user_id (str): 待验证的用户编号
        
    Returns:
        tuple: (是否有效, 消息)
    """
    return UserIDGenerator.validate_user_id(user_id)

def check_user_id_uniqueness(user_id):
    """
    检查用户编号是否唯一
    
    Args:
        user_id (str): 待检查的用户编号
        
    Returns:
        bool: 是否唯一
    """
    return UserIDGenerator.is_id_unique(user_id)

def generate_user_id_with_prefix(custom_prefix=""):
    """
    生成带自定义前缀的用户编号
    
    Args:
        custom_prefix (str): 自定义前缀
        
    Returns:
        str: 生成的用户编号
    """
    return UserIDGenerator.generate_id_with_prefix(custom_prefix)

# 测试函数（用于验证生成器功能）
def test_id_generation():
    """
    测试用户编号生成功能
    """
    try:
        # 生成标准编号
        std_id = generate_new_user_id()
        print(f"标准编号: {std_id}")
        
        # 验证编号格式
        is_valid, msg = validate_user_id_format(std_id)
        print(f"格式验证: {'通过' if is_valid else '失败'}", msg)
        
        # 生成带自定义前缀的编号
        custom_id = generate_user_id_with_prefix("VIP")
        print(f"自定义前缀编号: {custom_id}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

# 如果作为脚本直接运行，执行测试
if __name__ == "__main__":
    test_id_generation()