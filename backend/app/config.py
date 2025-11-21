"""配置文件 - 定义项目路径、数据存储路径、算法参数等"""
import os


class Config:
    """配置类 - 定义应用程序的所有配置参数"""
    
    # 项目根路径 - 获取backend目录的绝对路径
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 数据存储路径配置
    DATA_DIR = os.path.join(BASE_DIR, "data")  # 数据根目录
    FACE_IMAGE_DIR = os.path.join(DATA_DIR, "faces")  # 人脸图片存储目录
    DB_PATH = os.path.join(DATA_DIR, "face_db.db")  # SQLite数据库文件路径
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"  # SQLite数据库URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭修改跟踪（提高性能）
    
    # 人脸识别配置
    RECOGNITION_THRESHOLD = 0.6  # 人脸识别阈值（相似度低于此值视为不匹配，0-1之间）
    
    # Flask配置
    DEBUG = True  # 开发模式下启用调试
    HOST = "127.0.0.1"  # 服务器主机地址
    PORT = 5000  # 服务器端口
    SECRET_KEY = os.urandom(24)  # 用于会话管理的密钥


# 创建必要的目录（如果不存在）
os.makedirs(Config.FACE_IMAGE_DIR, exist_ok=True)
os.makedirs(Config.DATA_DIR, exist_ok=True)


# 默认配置实例
config = Config()