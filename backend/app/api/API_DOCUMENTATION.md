# 人脸识别系统后端接口文档

## 1. 接口基础配置

### 1.1 跨域配置
- 已配置跨域支持，允许前端 http://127.0.0.1:3000 访问
- 使用 Flask-CORS 实现跨域资源共享

### 1.2 统一响应格式

#### 成功响应
```json
{
  "code": 0,
  "msg": "操作成功",
  "data": { 具体数据 }
}
```

#### 注册阻断响应
```json
{
  "code": 3,
  "msg": "[注册阻断] 错误原因",
  "data": {
    "similarity": 相似度（可选）,
    "suggestion": "解决建议"
  }
}
```

#### 系统错误响应
```json
{
  "code": 999,
  "msg": "系统异常，请重试",
  "data": {}
}
```

## 2. 接口详情

### 2.1 注册接口

#### 2.1.1 摄像头采集录入
- **接口地址**: `POST /api/register/camera`
- **请求方式**: POST
- **请求参数**:
  - `name`: 用户名（必填，字符串）
  - `user_id`: 身份ID（可选，字符串，手动指定时需唯一）
  - `image`: base64编码图像（必填）
  - `face_box`: 可选，`{"x1":int,"y1":int,"x2":int,"y2":int}`（手工调整人脸坐标）

- **成功响应示例**:
```json
{
  "code": 0,
  "msg": "操作成功",
  "data": {
    "user_id": "USR20241123001",
    "create_time": "2024-11-23 14:30:45",
    "image_path": "/faces/USR20241123001.jpg"
  }
}
```

- **错误响应示例**:
  - 空用户名 (code=1)
  - 无效图像 (code=2)
  - 注册阻断 (code=3)
  - ID格式错误 (code=4)

#### 2.1.2 照片上传录入
- **接口地址**: `POST /api/register/upload`
- **请求方式**: POST
- **请求参数**:
  - `name`: 用户名（必填）
  - `user_id`: 身份ID（可选）
  - `file`: 图片文件（必填）
  - `face_box`: 可选

- **响应格式**同摄像头采集录入

### 2.2 识别接口

#### 2.2.1 摄像头实时识别
- **接口地址**: `POST /api/recognize/camera`
- **请求方式**: POST
- **请求参数**:
  - `image`: base64编码图像（必填）

- **成功响应示例**:
```json
{
  "code": 0,
  "msg": "操作成功",
  "data": {
    "total_count": 2,
    "matched_count": 1,
    "unmatched_count_db": 1,
    "matched_names": [
      {
        "name": "张三",
        "user_id": "USR20241123001",
        "similarity": 0.85,
        "confidence": 0.92
      }
    ],
    "unmatched_names_db": [],
    "face_boxes": [[100, 80, 200, 200], [300, 90, 400, 210]],
    "face_confidences": [0.92, 0.88],
    "annotated_image": "base64编码的标注图像"
  }
}
```

- **错误响应示例**:
  - 无有效人脸 (code=10)
  - 人脸数量为0 (code=11)

#### 2.2.2 照片上传识别
- **接口地址**: `POST /api/recognize/upload`
- **请求方式**: POST
- **请求参数**:
  - `file`: 图片文件（必填）

- **响应格式**同摄像头实时识别

### 2.3 删除接口

#### 2.3.1 单条删除
- **接口地址**: `DELETE /api/delete/single`
- **请求方式**: DELETE
- **请求参数**:
  - `user_id`: 身份ID（必填）

- **成功响应示例**:
```json
{
  "code": 0,
  "msg": "操作成功",
  "data": {
    "deleted_user_id": "USR20241123001",
    "message": "用户删除成功"
  }
}
```

- **错误响应示例**:
  - ID不存在 (code=20)

#### 2.3.2 批量删除
- **接口地址**: `DELETE /api/delete/batch`
- **请求方式**: DELETE
- **请求参数**:
  - `user_ids`: 用户ID数组（必填，如 `["USR20241123001","USR20241123002"]`）

- **成功响应示例**:
```json
{
  "code": 0,
  "msg": "操作成功",
  "data": {
    "deleted_count": 2,
    "deleted_user_ids": ["USR20241123001", "USR20241123002"],
    "message": "批量删除成功"
  }
}
```

- **部分失败响应示例**:
```json
{
  "code": 21,
  "msg": "部分用户删除失败",
  "data": {
    "success_ids": ["USR20241123001"],
    "failed_ids": ["USR20241123002"]
  }
}
```

### 2.4 统计接口

- **接口地址**: `GET /api/statistic`
- **请求方式**: GET
- **请求参数**: 无

- **成功响应示例**:
```json
{
  "code": 0,
  "msg": "操作成功",
  "data": {
    "total_users": 156,
    "today_registered": 12,
    "total_deleted": 23,
    "valid_face_rate": 89.5
  }
}
```

## 3. Postman测试用例

### 3.1 注册接口测试

#### 摄像头注册
1. **请求设置**:
   - 方法: POST
   - URL: `http://127.0.0.1:5000/api/register/camera`
   - Headers: `Content-Type: application/json`

2. **Body** (raw JSON):
```json
{
  "name": "测试用户",
  "image": "base64编码的图像数据"
}
```

#### 上传注册
1. **请求设置**:
   - 方法: POST
   - URL: `http://127.0.0.1:5000/api/register/upload`
   - Headers: 无需特别设置

2. **Body** (form-data):
   - Key: name, Value: 测试用户
   - Key: file, Value: [选择图片文件]

### 3.2 识别接口测试

#### 摄像头识别
1. **请求设置**:
   - 方法: POST
   - URL: `http://127.0.0.1:5000/api/recognize/camera`
   - Headers: `Content-Type: application/json`

2. **Body** (raw JSON):
```json
{
  "image": "base64编码的图像数据"
}
```

#### 上传识别
1. **请求设置**:
   - 方法: POST
   - URL: `http://127.0.0.1:5000/api/recognize/upload`

2. **Body** (form-data):
   - Key: file, Value: [选择图片文件]

### 3.3 删除接口测试

#### 单条删除
1. **请求设置**:
   - 方法: DELETE
   - URL: `http://127.0.0.1:5000/api/delete/single?user_id=USR20241123001`
   
   或使用Body传递参数:
   - Headers: `Content-Type: application/json`
   - Body (raw JSON): `{"user_id": "USR20241123001"}`

#### 批量删除
1. **请求设置**:
   - 方法: DELETE
   - URL: `http://127.0.0.1:5000/api/delete/batch`
   - Headers: `Content-Type: application/json`

2. **Body** (raw JSON):
```json
{
  "user_ids": ["USR20241123001", "USR20241123002"]
}
```

### 3.4 统计接口测试
1. **请求设置**:
   - 方法: GET
   - URL: `http://127.0.0.1:5000/api/statistic`

## 4. curl命令示例

### 4.1 注册接口

#### 摄像头注册
```bash
curl -X POST http://127.0.0.1:5000/api/register/camera \
  -H "Content-Type: application/json" \
  -d '{"name":"测试用户","image":"base64编码的图像数据"}'
```

#### 上传注册
```bash
curl -X POST http://127.0.0.1:5000/api/register/upload \
  -F "name=测试用户" \
  -F "file=@/path/to/image.jpg"
```

### 4.2 识别接口

#### 摄像头识别
```bash
curl -X POST http://127.0.0.1:5000/api/recognize/camera \
  -H "Content-Type: application/json" \
  -d '{"image":"base64编码的图像数据"}'
```

#### 上传识别
```bash
curl -X POST http://127.0.0.1:5000/api/recognize/upload \
  -F "file=@/path/to/image.jpg"
```

### 4.3 删除接口

#### 单条删除
```bash
curl -X DELETE "http://127.0.0.1:5000/api/delete/single?user_id=USR20241123001"
```

#### 批量删除
```bash
curl -X DELETE http://127.0.0.1:5000/api/delete/batch \
  -H "Content-Type: application/json" \
  -d '{"user_ids":["USR20241123001","USR20241123002"]}'
```

### 4.4 统计接口
```bash
curl -X GET http://127.0.0.1:5000/api/statistic
```

## 5. 异常处理说明

### 5.1 注册类异常
- **code=1**: 空用户名 - 请提供有效的用户名
- **code=2**: 无效图像 - 请检查图像格式和质量
- **code=3**: 注册阻断 - 
  - 可能原因：重复人脸（相似度>0.50）、人脸质量不达标（置信度<0.85、尺寸<100x100px）、ID重复
  - 解决建议：提供清晰的正面人脸图像，确保唯一性
- **code=4**: ID格式错误 - 请使用正确格式的ID（以USR开头）

### 5.2 识别类异常
- **code=10**: 无有效人脸 - 请提供包含清晰人脸的图像
- **code=11**: 人脸数量为0 - 未检测到人脸，请调整图像或姿势

### 5.3 删除类异常
- **code=20**: ID不存在 - 请检查用户ID是否正确
- **code=21**: 批量删除部分失败 - 请检查失败ID的存在性和权限

## 6. 调用说明

### 6.1 启动服务器
```bash
cd backend
python run.py
```

### 6.2 依赖安装
```bash
pip install -r requirements.txt
```

### 6.3 核心模块调用说明
- 所有接口均已在 `backend/app/api/__init__.py` 中注册
- 调用 `data_process.py` 中的 `register_face` 和 `recognize_face` 函数处理核心业务逻辑
- 删除接口依赖 `user_data_manager.py` 中的用户数据管理功能
- 所有接口均支持异常捕获和统一响应格式

### 6.4 测试脚本使用
如需使用 interactive_test.py 测试接口，请确保：
1. 后端服务已启动
2. 测试脚本正确配置了API地址（默认 http://127.0.0.1:5000）
3. 准备好测试用的图像文件

测试脚本示例调用：
```python
# 测试注册接口
python interactive_test.py --api register --mode camera --image test.jpg --name "测试用户"

# 测试识别接口
python interactive_test.py --api recognize --mode upload --image test.jpg

# 测试统计接口
python interactive_test.py --api statistic
```

## 7. 注意事项
1. 请确保在调用接口前启动后端服务
2. 上传图片文件时，请确保文件大小不超过限制（默认10MB）
3. base64编码的图像数据可能会很长，注意传输效率
4. 生产环境中建议添加请求频率限制和用户认证
5. 定期备份人脸数据和特征文件
