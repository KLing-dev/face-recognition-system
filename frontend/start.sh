#!/bin/bash

# 人脸识别系统前端启动脚本

echo "========================================"
echo " 人脸识别系统前端启动脚本 "
echo "========================================"

# 检查Node.js环境
echo "检查Node.js版本..."
if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js，请先安装Node.js 16.0.0或更高版本"
    exit 1
fi

NODE_VERSION=$(node -v)
echo "当前Node.js版本: $NODE_VERSION"

# 检查npm环境
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到npm，请确保Node.js安装正确"
    exit 1
fi

NPM_VERSION=$(npm -v)
echo "当前npm版本: $NPM_VERSION"

# 安装依赖
echo "\n开始安装项目依赖..."
npm install
if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败，请检查网络连接或package.json文件"
    exit 1
fi

echo "\n依赖安装成功！"

# 启动开发服务器
echo "\n启动开发服务器..."
echo "服务启动后，可通过以下地址访问:"
echo "http://localhost:5173"
echo "按 Ctrl+C 可停止服务"
echo "========================================"

npm run dev
