from flask import request
from flask_restful import Resource
from . import success_response, system_error_response, error_response
from app.utils.data_process import delete_user_by_id


class SingleDeleteAPI(Resource):
    """
    单用户删除接口
    
    根据用户ID删除单个用户的所有信息
    接口地址: DELETE /api/delete/single
    
    请求参数:
    - 方式1: JSON请求体中的user_id字段
    - 方式2: URL查询参数中的user_id参数
    两种方式都支持，优先从请求体获取
    
    返回数据:
    - 成功: {"code": 0, "msg": "成功", "data": {"deleted_user_id": "...", "message": "用户删除成功"}}
    - 失败: {"code": 错误码, "msg": "错误信息", "data": {}}
    """
    def delete(self):
        try:
            # 获取请求参数
            # DELETE请求通常使用query parameters或body传递参数
            # 这里支持两种方式，优先从body获取，其次从query parameters获取
            
            # 尝试从JSON body获取参数
            data = request.get_json()
            if data and 'user_id' in data:
                user_id = data['user_id']
            else:
                # 从query parameters获取参数
                user_id = request.args.get('user_id')
            
            # 验证必要参数
            if not user_id:
                return error_response(1, "用户ID不能为空")
            
            # 验证ID格式
            if not isinstance(user_id, str) or not user_id.startswith('USR'):
                return error_response(1, "用户ID格式错误")
            
            # 调用删除函数 - 使用从data_process导入的函数
            try:
                # 使用导入的delete_user_by_id函数
                success = delete_user_by_id(user_id)
                
                if not success:
                    return error_response(2, "用户ID不存在")
                
                # 构建成功响应
                return success_response({
                    "deleted_user_id": user_id,
                    "message": "用户删除成功"
                })
                
            except Exception as e:
                return system_error_response()
                
        except Exception as e:
            # 捕获其他未预期的异常
            return system_error_response()


class BatchDeleteAPI(Resource):
    """
    批量用户删除接口
    
    根据用户ID列表批量删除多个用户的所有信息
    接口地址: DELETE /api/delete/batch
    
    请求参数:
    - JSON请求体中的user_ids字段，格式为字符串数组
    
    返回数据:
    - 成功: {"code": 0, "msg": "成功", "data": {"success_count": 成功删除数量, "failed_count": 删除失败数量, "failed_ids": [失败的ID列表]}}
    - 失败: {"code": 错误码, "msg": "错误信息", "data": {}}
    """
    def delete(self):
        try:
            # 获取请求参数
            data = request.get_json()
            
            # 验证请求数据
            if not data or 'user_ids' not in data:
                return error_response(1, "请求数据无效，缺少user_ids参数")
            
            # 获取用户ID列表
            user_ids = data['user_ids']
            
            # 验证user_ids是否为数组
            if not isinstance(user_ids, list):
                return error_response(1, "user_ids必须为数组格式")
            
            # 验证数组不为空
            if len(user_ids) == 0:
                return error_response(1, "user_ids数组不能为空")
            
            # 验证所有ID的格式
            invalid_ids = []
            for user_id in user_ids:
                if not isinstance(user_id, str) or not user_id.startswith('USR'):
                    invalid_ids.append(user_id)
            
            if invalid_ids:
                return error_response(1, "存在无效的用户ID格式")
            
            # 调用批量删除函数
            try:
                # 从app.utils.data_process导入批量删除函数
                from app.utils.data_process import batch_delete_users
                
                # 使用导入的batch_delete_users函数
                result = batch_delete_users(user_ids)
                
                # 检查是否有部分删除失败
                if result.get("failed_ids", []):
                    return error_response(2, "部分用户删除失败")
                
                # 构建成功响应
                return success_response({
                    "deleted_count": len(result.get("success_ids", [])),
                    "deleted_user_ids": result.get("success_ids", []),
                    "message": "批量删除成功"
                })
                
            except Exception as e:
                return system_error_response()
                
        except Exception as e:
            # 捕获其他未预期的异常
            return system_error_response()


def register_routes(api):
    """注册路由函数
    
    将所有用户删除相关的API路由添加到Flask-RESTful的Api对象中
    
    Args:
        api: Flask-RESTful的Api实例
    
    注册的路由：
    - DELETE /api/delete/single: 单用户删除接口
    - DELETE /api/delete/batch: 批量用户删除接口
    """
    api.add_resource(SingleDeleteAPI, '/api/delete/single')
    api.add_resource(BatchDeleteAPI, '/api/delete/batch')


# 如果直接运行该模块，可以进行简单测试
if __name__ == '__main__':
    from flask import Flask
    from flask_restful import Api
    
    app = Flask(__name__)
    api = Api(app)
    register_routes(api)
    
    print("删除接口模块已初始化，可以通过以下接口访问：")
    print("1. DELETE /api/delete/single - 单条用户删除（参数: user_id）")
    print("2. DELETE /api/delete/batch - 批量用户删除（参数: user_ids数组）")
    print("注意：直接运行此模块仅用于测试接口结构，实际功能需要完整的后端环境。")
