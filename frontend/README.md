# 人脸识别系统前端

## 项目介绍

基于Vue3 + Vite + Axios + Element Plus开发的人脸识别系统前端，支持人脸录入、识别和数据管理等核心功能。

## 技术栈

- **Vue 3**: 渐进式JavaScript框架
- **Vite**: 现代前端构建工具
- **Element Plus**: Vue 3 UI组件库
- **Axios**: HTTP客户端
- **Vue Router**: 路由管理
- **js-base64**: Base64编码解码
- **vue-draggable-next**: 拖拽功能
- **Sass**: CSS预处理器

## 安装步骤

### 1. 环境准备

确保你的开发环境已安装：
- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

### 2. 安装依赖

```bash
# 使用npm安装依赖
npm install

# 或使用yarn安装依赖
yarn install
```

### 3. 启动开发服务器

```bash
# 开发模式启动
npm run dev

# 或使用yarn
yarn dev
```

启动后，可通过浏览器访问 http://localhost:5173 查看项目。

## 项目结构

```
frontend/
├── public/
├── src/
│   ├── assets/         # 静态资源
│   │   └── styles/     # 样式文件
│   │       └── theme.scss # 主题样式
│   ├── components/     # 公共组件
│   │   ├── LoadingOverlay.vue    # 加载动画组件
│   │   ├── OperationResult.vue   # 操作结果组件
│   │   ├── FaceDetector.vue      # 人脸检测组件
│   │   └── ImageAnnotator.vue    # 图片标注组件
│   ├── pages/          # 页面组件
│   │   ├── Home.vue             # 首页
│   │   ├── Register.vue         # 录入页
│   │   ├── Recognition.vue      # 识别页
│   │   └── DataManage.vue       # 数据管理页
│   ├── router/         # 路由配置
│   │   └── index.js    # 路由定义
│   ├── services/       # API服务
│   ├── App.vue         # 应用入口
│   └── main.js         # 主入口文件
├── index.html          # HTML模板
├── package.json        # 项目依赖
├── vite.config.js      # Vite配置
└── README.md           # 项目说明
```

## 核心功能说明

### 1. 首页

- 系统介绍和规则说明
- 功能导航按钮
- 统计数据展示

### 2. 人脸录入

- 摄像头模式：实时检测人脸，自动标注
- 上传模式：支持本地图片上传识别
- 支持手动指定ID或自动生成
- 人脸区域调整功能
- 注册阻断处理和错误提示

### 3. 人脸识别

- 摄像头拍照识别
- 本地上传图片识别
- 识别结果展示（标注图像、相似度、置信度）
- 匹配结果和未出现列表展示

### 4. 数据管理

- 用户数据查询
- 单条/批量删除功能
- 统计信息展示

## 调试方法

### 1. 前端调试

- **浏览器控制台**：使用Chrome/Firefox等浏览器的开发者工具查看控制台日志、网络请求和组件状态
- **Vue DevTools**：安装Vue DevTools浏览器扩展，方便调试Vue组件
- **Vite HMR**：修改代码后自动热更新，无需手动刷新页面

### 2. 与后端联调

前端默认连接到`http://localhost:5000`的后端服务。如果后端服务端口或地址有变化，请修改`src/services/api.js`中的基础URL配置。

### 3. 常见问题排查

- **API连接失败**：检查后端服务是否正常运行
- **数据格式错误**：确保前端与后端API的数据结构保持一致
- **人脸识别无结果**：检查图片质量和后端模型训练状态

### 4. 核心功能调试指南

#### 手动指定ID功能测试

1. 进入人脸录入页面
2. 开启「手动指定ID」开关
3. 输入自定义ID（如：USER123）
4. 提交注册，检查返回结果中的ID是否为手动输入的ID

#### 注册阻断提示测试

1. 使用已注册的人脸图片进行重复注册
2. 观察系统是否显示包含「[注册阻断]」前缀的错误提示
3. 检查错误信息中是否包含解决建议

#### 人脸尺寸校验测试

1. 在录入页面检测到人脸后，点击「调整人脸区域」
2. 测试不同尺寸的人脸区域是否都能正确保存

## API接口说明

### 数据录入

```
POST /api/record/upload
Content-Type: multipart/form-data
```

### 人脸识别

```
POST /api/recognize/upload
Content-Type: multipart/form-data
```

### 数据管理

```
GET /api/data/list          # 获取用户列表
DELETE /api/data/delete     # 删除用户数据
GET /api/data/statistic     # 获取统计信息
```

## 开发注意事项

1. 确保后端服务正常运行后再启动前端服务
2. 开发过程中如有API变更，请及时更新前端相应逻辑
3. 所有图片上传功能需要用户授权浏览器访问摄像头
4. 如需修改主题样式，可在`src/assets/styles/theme.scss`文件中进行定制
5. 新增组件时请遵循现有的命名规范和代码风格

## 许可证

MIT