from flask_restful import Resource
from datetime import datetime
from . import success_response, system_error_response

# 使用数据处理模块获取统计数据
from app.utils.data_process import get_statistics

class StatisticAPI(Resource):
    """
    统计接口
    
    获取系统用户注册相关的统计信息
    接口地址: GET /api/statistic
    
    返回数据:
    - 成功: {"code": 0, "msg": "成功", "data": {"total_users": 总用户数, "total_recognitions": 总识别次数, "today_recognitions": 今日识别次数, "recognition_rate": 识别成功率}}
    - 失败: {"code": 错误码, "msg": "错误信息", "data": {}}
    """
    def get(self):
        try:
            # 直接调用数据处理模块获取统计信息
            statistics = get_statistics()
            
            # 返回统计结果
            return success_response(statistics)
                
        except Exception as e:
            # 捕获异常，返回系统错误响应
            return system_error_response()


def register_routes(api):
    """注册路由函数
    
    将系统统计相关的API路由添加到Flask-RESTful的Api对象中
    
    Args:
        api: Flask-RESTful的Api实例
    
    注册的路由：
    - GET /api/statistic: 获取系统统计信息接口
    """
    api.add_resource(StatisticAPI, '/api/statistic')


# 如果直接运行该模块，可以进行简单测试
if __name__ == '__main__':
    from flask import Flask
    from flask_restful import Api
    
    app = Flask(__name__)
    api = Api(app)
    register_routes(api)
    
    print("统计接口模块已初始化，可以通过以下接口访问：")
    print("GET /api/statistic - 获取系统统计信息")
    print("注意：直接运行此模块仅用于测试接口结构，实际功能需要完整的后端环境。")
