"""数据模型文件 - 定义数据库表结构和ORM映射"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import config


# 创建基类
Base = declarative_base()

# 创建数据库引擎
engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    """用户数据模型 - 存储人脸信息和用户相关数据"""
    
    __tablename__ = "users"  # 数据库表名
    
    # 主键字段
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="用户ID")
    
    # 用户名 - 允许重复，只设置索引不设唯一约束
    name = Column(String(100), index=True, nullable=False, comment="用户名")
    
    # 身份ID - 唯一约束确保不会有重复身份ID
    identity_id = Column(String(50), unique=True, index=True, nullable=False, comment="身份ID")
    
    # 人脸特征向量存储路径
    feature_path = Column(String(255), nullable=False, comment="人脸特征向量文件存储路径")
    
    # 人脸图片存储路径
    image_path = Column(String(255), nullable=False, comment="人脸图片存储路径")
    
    # 创建时间 - 记录数据添加时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 更新时间 - 记录数据最后更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    def __repr__(self):
        """返回用户对象的字符串表示"""
        return f"<User(id={self.id}, name='{self.name}', identity_id='{self.identity_id}')>"


def get_db():
    """
    获取数据库会话的依赖函数
    用于FastAPI或Flask中获取数据库会话
    
    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库 - 创建所有表
    应用启动时调用，确保数据库表结构存在
    """
    Base.metadata.create_all(bind=engine)