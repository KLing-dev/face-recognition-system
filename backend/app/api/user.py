from flask_restful import Resource
from flask import request
from ..models.models import SessionLocal, User

# 从api/__init__.py复制响应格式化函数
def success_response(data=None):
    """成功响应"""
    return {
        "code": 0,
        "msg": "操作成功",
        "data": data or {}
    }, 200

def system_error_response():
    """系统错误响应"""
    return {
        "code": 999,
        "msg": "系统异常，请重试",
        "data": {}
    }, 500

class UserListAPI(Resource):
    """
    用户列表接口
    
    获取系统中所有用户的数据
    接口地址: GET /api/user/list
    
    查询参数:
    - page: 页码，默认为1
    - page_size: 每页数量，默认为10
    - search: 搜索关键词，可搜索用户ID或用户名
    
    返回数据:
    - 成功: {"code": 0, "msg": "成功", "data": {"total": 总用户数, "users": [{"user_id": "身份ID", "name": "用户名", "created_at": "创建时间", "is_deleted": false}]}}
    - 失败: {"code": 错误码, "msg": "错误信息", "data": {}}
    """
    def get(self):
        try:
            # 获取请求参数
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 10, type=int)
            search = request.args.get('search', '', type=str)
            
            # 获取数据库会话
            db = SessionLocal()
            
            try:
                # 构建查询
                query = db.query(User)
                
                # 如果有搜索关键词，添加搜索条件
                if search:
                    query = query.filter(
                        (User.identity_id.contains(search)) | 
                        (User.name.contains(search))
                    )
                
                # 计算总数
                total = query.count()
                
                # 分页查询
                users = query.offset((page - 1) * page_size).limit(page_size).all()
                
                # 转换为响应格式
                user_list = [
                    {
                        "user_id": user.identity_id,  # 使用identity_id作为user_id
                        "name": user.name,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "face_thumbnail": user.image_path if hasattr(user, 'image_path') and user.image_path else '',
                        "is_deleted": user.is_deleted if hasattr(user, 'is_deleted') else False
                    }
                    for user in users
                ]
                
                # 返回成功响应
                return success_response({
                    "total": total,
                    "users": user_list
                })
                
            except Exception as e:
                db.rollback()
                return system_error_response()
            finally:
                db.close()
                
        except Exception as e:
            return system_error_response()

# request 已经在文件顶部导入

def register_routes(api):
    """注册路由函数
    
    将用户相关的API路由添加到Flask-RESTful的Api对象中
    
    Args:
        api: Flask-RESTful的Api实例
    
    注册的路由：
    - GET /api/user/list: 获取用户列表
    """
    api.add_resource(UserListAPI, '/api/user/list')
