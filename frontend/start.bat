@echo off

REM 人脸识别系统前端启动脚本（Windows版）

echo ========================================
echo  人脸识别系统前端启动脚本（Windows版）  
echo ========================================

REM 检查Node.js环境
echo 检查Node.js版本...
node -v >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js，请先安装Node.js 16.0.0或更高版本
    pause
    exit /b 1
)

for /f "delims=" %%i in ('node -v') do set NODE_VERSION=%%i
echo 当前Node.js版本: %NODE_VERSION%

REM 检查npm环境
npm -v >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到npm，请确保Node.js安装正确
    pause
    exit /b 1
)

for /f "delims=" %%i in ('npm -v') do set NPM_VERSION=%%i
echo 当前npm版本: %NPM_VERSION%

REM 安装依赖
echo.
echo 开始安装项目依赖...
npm install
if %errorlevel% neq 0 (
    echo 错误: 依赖安装失败，请检查网络连接或package.json文件
    pause
    exit /b 1
)

echo.
echo 依赖安装成功！

REM 启动开发服务器
echo.
echo 启动开发服务器...
echo 服务启动后，可通过以下地址访问:
echo http://localhost:5173
echo 按 Ctrl+C 可停止服务
echo ========================================

npm run dev
