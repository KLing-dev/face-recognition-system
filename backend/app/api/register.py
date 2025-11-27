"""人脸注册接口模块

提供两种人脸录入方式：
1. 摄像头采集 - 通过POST /api/register/camera接收base64编码的图像
2. 照片上传 - 通过POST /api/register/upload接收文件上传

核心功能：
- 接收人脸图像并进行有效性验证
- 调用后端注册逻辑处理人脸特征提取和存储
- 返回统一格式的响应信息

依赖：
- Flask-RESTful用于API实现
- PIL用于图像处理
- 后端register_face模块处理核心注册逻辑
"""
from flask import request
from flask_restful import Resource
import base64
import io
import json
import re
from PIL import Image

# 导入统一响应格式
from . import success_response, register_block_response, error_response, system_error_response

# 导入数据处理模块
from app.utils.data_process import register_face

class CameraRegisterAPI(Resource):
    """摄像头采集录入接口
    
    通过摄像头采集的方式录入人脸信息
    接口地址: POST /api/register/camera
    
    请求参数(JSON):
    - name: 用户名(必填)
    - image: base64编码的图像数据(必填)
    - user_id: 用户ID(可选，不提供则自动生成)
    - face_box: 人脸区域坐标(可选)
    
    返回数据:
    - 成功: {"code": 0, "msg": "注册成功", "data": {...}}
    - 失败: {"code": [错误码], "msg": [错误信息], "data": {}}
    """
    
    def post(self):
        """处理摄像头采集录入请求
        
        Returns:
            JSON: 包含注册结果的响应数据
        """
        try:
            # 获取请求数据
            data = request.get_json()
            
            # 参数验证
            if not data:
                return error_response(2, "无效的请求数据")
            
            # 验证必填参数
            name = data.get('name')
            image = data.get('image')
            
            if not name:
                return error_response(1, "用户名为必填项")
            
            if not image:
                return error_response(2, "图像数据为必填项")
            
            # 可选参数
            user_id = data.get('user_id')
            face_box = data.get('face_box')
            
            # 验证name格式
            if not isinstance(name, str) or not name.strip():
                return error_response(1, "用户名格式错误")
            
            # 验证user_id格式（如果提供）
            if user_id and not re.match(r'^USR\d{12}$', user_id):
                return error_response(4, "用户ID格式错误，正确格式：USR+年月日+4位序号")
            
            # 解码base64图像
            try:
                # 移除base64头部信息
                if 'base64,' in image:
                    image = image.split('base64,')[1]
                
                # 解码base64数据
                image_data = base64.b64decode(image)
                
                # 验证图像格式
                img = Image.open(io.BytesIO(image_data))
                
                # 转换为RGB格式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 保存到字节流
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_data = img_byte_arr.getvalue()
                
            except Exception as e:
                return error_response(2, f"图像解码失败: {str(e)}")
            
            # 调用后端注册逻辑
            try:
                # 将user_id作为identity_id传递，因为register_face函数使用identity_id参数
                result = register_face(
                    name=name,
                    image=img,
                    identity_id=user_id
                )
                
                # 处理注册结果
                if result.get('success'):
                    # 注册成功
                    return success_response({
                        'user_id': result['user_id'],
                        'create_time': result.get('create_time', ''),
                        'image_path': result.get('image_path', '')
                    })
                elif result.get('status') == 'blocked':
                    # 注册阻断
                    return register_block_response(
                        msg=result['message'],
                        similarity=result.get('similarity'),
                        suggestion=result.get('suggestion')
                    )
                else:
                    # 其他错误
                    return error_response(5, result.get('message', '注册失败'))
                    
            except Exception as e:
                # 捕获特定的业务异常
                error_msg = str(e)
                if "人脸质量" in error_msg:
                    return register_block_response(
                        msg=error_msg,
                        suggestion="请确保人脸清晰可见，面部完全暴露在画面中"
                    )
                elif "唯一性" in error_msg:
                    return register_block_response(
                        msg=error_msg,
                        suggestion="该人脸已存在于系统中，请确认是否为同一人"
                    )
                elif "ID唯一性" in error_msg:
                    return register_block_response(
                        msg=error_msg,
                        suggestion="请更换用户ID或不指定ID（系统将自动生成）"
                    )
                else:
                    # 其他异常
                    raise
                    
        except Exception as e:
            # 记录错误日志
            print(f"摄像头注册接口错误: {str(e)}")
            return system_error_response()


class UploadRegisterAPI(Resource):
    """照片上传录入接口
    
    通过文件上传的方式录入人脸信息
    接口地址: POST /api/register/upload
    
    请求参数(Form-Data):
    - name: 用户名(必填)
    - file: 图像文件(必填，支持JPG、PNG等常见格式)
    - user_id: 用户ID(可选，不提供则自动生成)
    
    返回数据:
    - 成功: {"code": 0, "msg": "注册成功", "data": {...}}
    - 失败: {"code": [错误码], "msg": [错误信息], "data": {}}
    """
    
    def post(self):
        """处理照片上传录入请求
        
        Returns:
            JSON: 包含注册结果的响应数据
        """
        try:
            # 获取表单数据
            name = request.form.get('name')
            user_id = request.form.get('user_id')
            
            # 获取上传的文件
            file = request.files.get('file')
            
            # 验证必填参数
            if not name:
                return error_response(1, "用户名为必填项")
            
            if not file:
                return error_response(2, "文件为必填项")
            
            # 验证name格式
            if not isinstance(name, str) or not name.strip():
                return error_response(1, "用户名格式错误")
            
            # 验证user_id格式（如果提供）
            if user_id and not re.match(r'^USR\d{12}$', user_id):
                return error_response(4, "用户ID格式错误，正确格式：USR+年月日+4位序号")
            
            # 读取文件内容
            try:
                img_data = file.read()
                
                # 验证图像格式
                img = Image.open(io.BytesIO(img_data))
                
                # 转换为RGB格式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 保存到字节流
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_data = img_byte_arr.getvalue()
                
            except Exception as e:
                return error_response(2, f"文件解析失败: {str(e)}")
            
            # 获取face_box参数（如果提供）
            face_box_str = request.form.get('face_box')
            face_box = None
            if face_box_str:
                try:
                    face_box = json.loads(face_box_str)
                except:
                    return error_response(2, "face_box参数格式错误")
            
            # 调用后端注册逻辑
            try:
                # 将user_id作为identity_id传递，因为register_face函数使用identity_id参数
                result = register_face(
                    name=name,
                    image=img,
                    identity_id=user_id
                )
                
                # 处理注册结果
                if result.get('success'):
                    # 注册成功
                    return success_response({
                        'user_id': result['user_id'],
                        'create_time': result.get('create_time', ''),
                        'image_path': result.get('image_path', '')
                    })
                elif result.get('status') == 'blocked':
                    # 注册阻断
                    return register_block_response(
                        msg=result['message'],
                        similarity=result.get('similarity'),
                        suggestion=result.get('suggestion')
                    )
                else:
                    # 其他错误
                    return error_response(5, result.get('message', '注册失败'))
                    
            except Exception as e:
                # 捕获特定的业务异常
                error_msg = str(e)
                if "人脸质量" in error_msg:
                    return register_block_response(
                        msg=error_msg,
                        suggestion="请确保人脸清晰可见，面部完全暴露在画面中"
                    )
                elif "唯一性" in error_msg:
                    return register_block_response(
                        msg=error_msg,
                        suggestion="该人脸已存在于系统中，请确认是否为同一人"
                    )
                elif "ID唯一性" in error_msg:
                    return register_block_response(
                        msg=error_msg,
                        suggestion="请更换用户ID或不指定ID（系统将自动生成）"
                    )
                else:
                    # 其他异常
                    raise
                    
        except Exception as e:
            # 记录错误日志
            print(f"上传注册接口错误: {str(e)}")
            return system_error_response()


def register_routes(api):
    """注册路由函数
    
    将所有注册相关的API路由添加到Flask-RESTful的Api对象中
    
    Args:
        api: Flask-RESTful的Api实例
    
    注册的路由：
    - POST /register/camera: 摄像头采集录入接口
    - POST /register/upload: 照片上传录入接口
    """
    api.add_resource(CameraRegisterAPI, '/register/camera')
    api.add_resource(UploadRegisterAPI, '/register/upload')


# 测试代码（仅在直接运行模块时执行）
if __name__ == '__main__':
    from flask import Flask
    from flask_restful import Api
    
    app = Flask(__name__)
    api = Api(app)
    register_routes(api)
    
    print("人脸注册接口测试服务启动")
    print("访问 http://127.0.0.1:5000/register/camera (POST)")
    print("访问 http://127.0.0.1:5000/register/upload (POST)")
    
    app.run(debug=True)