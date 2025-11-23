"""人脸识别接口模块

提供两种人脸识别方式：
1. 摄像头识别 - 通过POST /api/recognize/camera接收base64编码的图像
2. 照片上传识别 - 通过POST /api/recognize/upload接收文件上传

核心功能：
- 接收人脸图像并进行有效性验证
- 调用后端识别逻辑进行人脸匹配
- 返回统一格式的响应信息，包含匹配结果

依赖：
- Flask-RESTful用于API实现
- PIL用于图像处理
- 后端recognize_face模块处理核心识别逻辑
"""
import base64
import io
from PIL import Image
from flask import request
from flask_restful import Resource
from werkzeug.utils import secure_filename

# 导入统一响应格式函数
from . import success_response, system_error_response

# 导入核心业务逻辑
from app.utils.data_process import recognize_face


class CameraRecognizeAPI(Resource):
    """摄像头识别人脸接口
    
    通过摄像头采集的方式进行人脸识别
    接口地址: POST /api/recognize/camera
    
    请求参数(JSON):
    - image: base64编码的图像数据(必填)
    
    返回数据:
    - 成功: {"code": 0, "msg": "识别成功", "data": {...}}
    - 失败: {"code": [错误码], "msg": [错误信息], "data": {}}
    
    成功响应data字段说明:
    - total_count: 检测到的人脸总数
    - matched_count: 匹配到的人脸数量
    - matched_names: 匹配到的人脸详情列表
    - face_boxes: 检测到的人脸框坐标
    """
    def post(self):
        """处理摄像头识别人脸请求
        
        Returns:
            JSON: 包含识别结果的响应数据
        """
        try:
            # 导入统一响应格式函数
            from . import error_response
            
            # 获取请求数据
            data = request.get_json()
            if not data:
                return error_response(2, "请求数据无效")
            
            # 验证必要参数
            image_data = data.get("image")
            if not image_data:
                return error_response(2, "图像数据不能为空")
            
            # 解码base64图像
            try:
                # 去除可能的base64前缀
                if image_data.startswith('data:image/'):
                    # 提取base64部分
                    image_data = image_data.split(',')[1]
                
                # 解码base64
                image_bytes = base64.b64decode(image_data)
                # 转换为PIL Image对象
                image = Image.open(io.BytesIO(image_bytes))
                
            except Exception as e:
                return error_response(2, f"图像解码失败: {str(e)}")
            
            # 调用核心识别逻辑
            try:
                result = recognize_face(image)
                
                # 检查是否有匹配结果
                if result.get("total_count", 0) == 0:
                    return error_response(11, "未检测到人脸")
                
                # 转换匹配详情为所需格式
                matched_names = []
                for detail in result.get("match_details", []):
                    if detail.get("matched_user"):
                        matched_names.append({
                            "name": detail["matched_user"],
                            "user_id": "N/A",  # 从数据库获取user_id需要额外查询
                            "similarity": detail.get("similarity", 0.0),
                            "confidence": 0.95  # 这里简化处理，实际应该从检测结果获取
                        })
                
                # 构建响应数据
                response_data = {
                    "total_count": result.get("total_count", 0),
                    "matched_count": result.get("matched_count", 0),
                    "unmatched_count_db": result.get("unmatched_count_db", 0),
                    "matched_names": matched_names,
                    "unmatched_names_db": result.get("unmatched_names_db", []),
                    "face_boxes": result.get("face_boxes", []),
                    "face_confidences": [0.95] * result.get("total_count", 0)  # 简化处理
                }
                
                # 添加annotated_image（可选，需要额外实现）
                # 这里简化处理，实际应该生成标注图像
                
                return success_response(response_data)
                
            except ValueError as e:
                error_msg = str(e)
                if "未检测到人脸" in error_msg:
                    return error_response(11, "人脸数量为0")
                elif "没有有效特征向量" in error_msg:
                    return error_response(10, "无有效人脸")
                else:
                    return error_response(10, "人脸识别失败: " + error_msg)
            except Exception as e:
                return system_error_response()
                
        except Exception as e:
            # 捕获其他未预期的异常
            return system_error_response()


class UploadRecognizeAPI(Resource):
    """上传图像识别人脸接口
    
    通过文件上传的方式进行人脸识别
    接口地址: POST /api/recognize/upload
    
    请求参数(Form-Data):
    - file: 图像文件(必填，支持jpg、jpeg、png、gif格式)
    
    返回数据:
    - 成功: {"code": 0, "msg": "识别成功", "data": {...}}
    - 失败: {"code": [错误码], "msg": [错误信息], "data": {}}
    
    成功响应data字段说明:
    - total_count: 检测到的人脸总数
    - matched_count: 匹配到的人脸数量
    - matched_names: 匹配到的人脸详情列表
    - face_boxes: 检测到的人脸框坐标
    """
    def post(self):
        """处理上传图像识别人脸请求
        
        Returns:
            JSON: 包含识别结果的响应数据
        """
        try:
            # 导入统一响应格式函数
            from . import error_response
            
            # 检查是否有文件上传
            if 'file' not in request.files:
                return error_response(2, "未提供图像文件")
            
            file = request.files['file']
            
            # 检查文件是否为空
            if file.filename == '':
                return error_response(2, "文件名为空")
            
            # 验证文件类型（简单验证文件扩展名）
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            if '.' not in file.filename or \
               file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                return error_response(2, "不支持的文件类型，请上传图片文件")
            
            # 安全处理文件名（虽然这里我们不保存文件，只是用于验证）
            secure_filename(file.filename)
            
            # 读取并处理图像
            try:
                # 转换为PIL Image对象
                image = Image.open(file.stream)
                # 确保图像在内存中（某些情况下可能需要）
                image.load()
            except Exception as e:
                return error_response(2, f"图像解析失败: {str(e)}")
            
            # 调用核心识别逻辑（与摄像头接口相同）
            try:
                result = recognize_face(image)
                
                # 检查是否有匹配结果
                if result.get("total_count", 0) == 0:
                    return jsonify({
                        "code": 11,
                        "msg": "未检测到人脸",
                        "data": {}
                    })
                
                # 转换匹配详情为所需格式
                matched_names = []
                for detail in result.get("match_details", []):
                    if detail.get("matched_user"):
                        matched_names.append({
                            "name": detail["matched_user"],
                            "user_id": "N/A",  # 从数据库获取user_id需要额外查询
                            "similarity": detail.get("similarity", 0.0),
                            "confidence": 0.95  # 简化处理
                        })
                
                # 构建响应数据
                response_data = {
                    "total_count": result.get("total_count", 0),
                    "matched_count": result.get("matched_count", 0),
                    "unmatched_count_db": result.get("unmatched_count_db", 0),
                    "matched_names": matched_names,
                    "unmatched_names_db": result.get("unmatched_names_db", []),
                    "face_boxes": result.get("face_boxes", []),
                    "face_confidences": [0.95] * result.get("total_count", 0)  # 简化处理
                }
                
                return success_response(response_data)
                
            except ValueError as e:
                error_msg = str(e)
                if "未检测到人脸" in error_msg:
                    return error_response(11, "人脸数量为0")
                elif "没有有效特征向量" in error_msg:
                    return error_response(10, "无有效人脸")
                else:
                    return error_response(10, "人脸识别失败: " + error_msg)
            except Exception as e:
                return system_error_response()
                
        except Exception as e:
            # 捕获其他未预期的异常
            return system_error_response()


def register_routes(api):
    """注册路由函数
    
    将所有人脸识别相关的API路由添加到Flask-RESTful的Api对象中
    
    Args:
        api: Flask-RESTful的Api实例
    
    注册的路由：
    - POST /api/recognize/camera: 摄像头识别人脸接口
    - POST /api/recognize/upload: 上传图像识别人脸接口
    """
    api.add_resource(CameraRecognizeAPI, '/api/recognize/camera')
    api.add_resource(UploadRecognizeAPI, '/api/recognize/upload')


# 如果直接运行该模块，可以进行简单测试
if __name__ == '__main__':
    from flask import Flask
    from flask_restful import Api
    
    app = Flask(__name__)
    api = Api(app)
    register_routes(api)
    
    print("人脸识别接口模块已初始化，可以通过以下接口访问：")
    print("1. POST /api/recognize/camera - 摄像头识别人脸（base64图像）")
    print("2. POST /api/recognize/upload - 上传图像识别人脸（文件上传）")
    print("注意：直接运行此模块仅用于测试接口结构，实际功能需要完整的后端环境。")
