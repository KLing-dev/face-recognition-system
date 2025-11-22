# 人脸识别系统
基于Python + Flask + Vue3 + MTCNN + FaceNet的前后端分离人脸识别系统，支持人脸数据录入、实时/照片识别、人数统计等功能。

## 项目结构
```
face_recognition_system/
├── frontend/               # 前端Vue3项目
│   ├── public/             # 静态资源
│   └── src/                # 源码目录
│       ├── api/            # Axios接口封装
│       ├── components/     # 公共组件（如摄像头组件、上传组件）
│       ├── pages/          # 页面（Home/Register/Recognition）
│       ├── router/         # 路由配置
│       ├── App.vue         # 根组件
│       └── main.js         # 入口文件
├── backend/                # 后端Flask项目
│   ├── app/
│   │   ├── api/            # 接口路由（用户、识别、统计）
│   │   ├── models/         # 数据模型（User人脸信息）
│   │   ├── utils/          # 工具函数（人脸检测/特征提取/比对）
│   │   └── config.py       # 配置（数据库、路径、算法参数）
│   ├── data/               # 人脸数据存储（图片+特征）
│   │   ├── faces/          # 人脸图片
│   │   └── face_db.db      # SQLite数据库
│   ├── requirements.txt    # 后端依赖
│   └── run.py              # 后端启动文件
├── README.md               # 项目文档
└── .gitignore              # Git忽略文件
```

## 依赖安装
### 后端依赖（Python 3.11）
1. 激活conda虚拟环境：`conda activate face_recog`
2. 进入backend目录：`cd backend`
3. 安装依赖：`pip install -r requirements.txt`

### 前端依赖（Node.js 16+）
1. 安装Node.js（官网：https://nodejs.org/ ，选择16.x版本）
2. 进入frontend目录：`cd frontend`
3. 安装依赖：`npm install`

## 系统运行
### 1. 启动后端
```bash
# 进入backend目录
cd backend
# 启动Flask服务（默认端口5000）
python run.py
```
- 服务地址：http://127.0.0.1:5000
- 接口文档：http://127.0.0.1:5000/api/docs（后续接口开发智能体补充）

### 2. 启动前端
```bash
# 进入frontend目录
cd frontend
# 启动Vue开发服务器（默认端口3000）
npm run dev
```
- 前端地址：http://127.0.0.1:3000

## 部署说明
### 开发环境部署
- 后端：本地Flask服务 + SQLite数据库（无需额外配置）
- 前端：Vue开发服务器（热更新）

### 生产环境部署（简化版）
1. 后端：使用Gunicorn作为WSGI服务器，Nginx反向代理
   ```bash
   # 安装Gunicorn
   pip install gunicorn
   # 启动
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```
2. 前端：打包静态文件，Nginx部署
   ```bash
   # 前端打包
   npm run build
   # 将dist目录部署到Nginx的html目录下
   ```

## Git工作流规范
### 分支管理
- `main`：主分支，存放生产环境代码，仅通过合并`dev`分支更新
- `dev`：开发分支，存放测试通过的代码，由`feature`分支合并而来
- `feature/xxx`：功能分支，如`feature/user-register`（用户录入功能），开发完成后合并到`dev`

### 提交规范
- 格式：`type(scope): description`
- 示例：
  - `feat(backend): 实现人脸特征提取功能`
  - `fix(frontend): 修复图片上传失败问题`
  - `docs: 更新README.md接口文档`
- type类型：feat（新功能）、fix（修复）、docs（文档）、style（样式）、refactor（重构）、test（测试）、chore（构建/依赖）

### 合并流程
1. 功能开发完成后，提交`feature`分支到远程仓库
2. 创建Pull Request（PR）到`dev`分支
3. 代码审核通过后，合并到`dev`分支
4. 测试环境验证通过后，由`dev`分支合并到`main`分支

## 前端路由
| 路由路径       | 页面名称       | 功能描述               |
|----------------|----------------|------------------------|
| /              | 首页           | 功能入口（录入/识别）  |
| /register      | 人脸录入页     | 摄像头采集/照片上传录入 |
| /recognition   | 人脸识别页     | 实时拍照/照片上传识别  |

## 后端路由
| 接口路径                | 请求方式 | 功能描述               | 请求参数                  | 响应格式                  |
|-------------------------|----------|------------------------|---------------------------|---------------------------|
| /api/register/camera    | POST     | 摄像头采集录入         | name（用户名）、image（base64图片） | {code:0, msg:"成功", data:{} } |
| /api/register/upload    | POST     | 照片上传录入           | name（用户名）、file（图片文件） | {code:0, msg:"成功", data:{} } |
| /api/recognize/camera   | POST     | 摄像头拍照识别         | image（base64图片）       | {code:0, msg:"成功", data:{总人数、匹配人数、未匹配人数、标注图片、人名列表、未出现人名列表} } |
| /api/recognize/upload   | POST     | 本地照片上传识别       | file（图片文件）          | 同上                      |
| /api/statistic          | GET      | 获取数据库统计信息     | -                         | {code:0, msg:"成功", data:{总用户数} } |

## 模块说明
### 前端模块
1. 首页模块：功能导航，跳转至录入/识别页
2. 录入模块：摄像头实时流展示、拍照/上传按钮、用户名输入框
3. 识别模块：图片上传区域、摄像头控制、识别结果展示（标注图片、统计数据）

### 后端模块
1. 配置模块（config.py）：数据库路径、人脸图片存储路径、算法参数
2. 数据模型模块（models.py）：User表（id、name、feature_path、image_path）
3. 人脸工具模块（utils/face_utils.py）：人脸检测（MTCNN）、特征提取（FaceNet）、特征比对
4. 接口模块（api/）：路由注册、请求处理、响应返回

## 配置说明
### 后端配置（backend/app/config.py）
```python
import os

# 项目根路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据存储路径
DATA_DIR = os.path.join(BASE_DIR, "data")
FACE_IMAGE_DIR = os.path.join(DATA_DIR, "faces")
DB_PATH = os.path.join(DATA_DIR, "face_db.db")

# 创建目录（不存在则创建）
os.makedirs(FACE_IMAGE_DIR, exist_ok=True)

# 人脸识别阈值（相似度低于此值视为不匹配，0-1之间，越小匹配越严格）
RECOGNITION_THRESHOLD = 0.6

# Flask配置
DEBUG = True
HOST = "127.0.0.1"
PORT = 5000
```

## 核心算法模块说明
### 1. 人脸检测（MTCNN）
- 功能：从图片中检测人脸位置（ bounding box ），过滤非人脸区域
- 优势：轻量、高效，支持多人脸检测
- 流程：图片输入 → MTCNN模型 → 输出人脸坐标和置信度（过滤低置信度结果）

### 2. 人脸特征提取（FaceNet）
- 功能：将检测到的人脸图像转换为128维的特征向量
- 优势：特征向量具有良好的区分性，支持相似度计算
- 流程：人脸图像 → 预处理（归一化、对齐） → FaceNet预训练模型 → 128维特征向量

### 3. 特征比对（余弦相似度）
- 功能：计算输入人脸特征与数据库中所有特征的余弦相似度
- 判定规则：相似度 > 阈值（0.6） → 匹配成功，返回对应用户名
- 公式：cos_sim(a,b) = (a·b) / (||a||×||b||)

## 故障排除
### 1. 环境安装失败
- 问题：MTCNN/FaceNet安装失败 → 解决方案：确保Python版本为3.11，先安装依赖`pip install setuptools wheel`，再重新安装
- 问题：OpenCV导入失败 → 解决方案：使用`pip install opencv-python-headless`（无GUI版本）

### 2. 人脸识别准确率低
- 解决方案：调整`RECOGNITION_THRESHOLD`阈值（0.5-0.7之间），确保录入人脸时光线充足、正面拍摄

### 3. 前端无法访问后端接口
- 解决方案：检查后端是否启动（http://127.0.0.1:5000），确认后端已安装`flask-cors`（跨域支持）

### 4. 摄像头无法调用
- 解决方案：浏览器授权摄像头访问，确保前端代码中摄像头权限申请正确，后端接口支持base64图片传输

## 应用场景
1. 课堂考勤：实时拍摄课堂照片，统计出勤人数、未出勤人数
2. 会议签到：通过摄像头快速识别参会人员，自动签到
3. 门禁系统：实时检测人脸，与授权人员数据库比对，允许授权人员进入
4. 人群统计：精确统计照片/视频中的总人数，适用于公共场合人流统计
