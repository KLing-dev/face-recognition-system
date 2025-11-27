from flask import Flask
from flask_cors import CORS
from flask_restful import Api

# 创建Flask应用实例
def create_app():
    app = Flask(__name__)
    
    # 配置跨域，允许前端http://127.0.0.1:3000访问
    CORS(app, origins=['http://127.0.0.1:3000'])
    
    # 创建API实例，路由前缀统一为/api
    api = Api(app, prefix='/api')
    
    # 导入并注册各个接口
    from .register import CameraRegisterAPI, UploadRegisterAPI
    from .recognize import CameraRecognizeAPI, UploadRecognizeAPI
    from .delete import SingleDeleteAPI, BatchDeleteAPI
    from .statistic import StatisticAPI
    from .user import UserListAPI
    
    # 注册接口路由
    api.add_resource(CameraRegisterAPI, '/register/camera')
    api.add_resource(UploadRegisterAPI, '/register/upload')
    api.add_resource(CameraRecognizeAPI, '/recognize/camera')
    api.add_resource(UploadRecognizeAPI, '/recognize/upload')
    api.add_resource(SingleDeleteAPI, '/delete/single')
    api.add_resource(BatchDeleteAPI, '/delete/batch')
    api.add_resource(StatisticAPI, '/statistic')
    api.add_resource(UserListAPI, '/user/list')
    
    return app

# 统一响应格式函数
def success_response(data=None):
    """成功响应"""
    return {
        "code": 0,
        "msg": "操作成功",
        "data": data or {}
    }, 200

def register_block_response(msg, suggestion=None, similarity=None):
    """注册阻断响应"""
    data = {}
    if similarity is not None:
        data['similarity'] = similarity
    if suggestion:
        data['suggestion'] = suggestion
    return {
        "code": 3,
        "msg": f"[注册阻断] {msg}",
        "data": data
    }, 200

def error_response(code, msg, data=None):
    """错误响应"""
    return {
        "code": code,
        "msg": msg,
        "data": data or {}
    }, 200

def system_error_response():
    """系统错误响应"""
    return {
        "code": 999,
        "msg": "系统异常，请重试",
        "data": {}
    }, 500