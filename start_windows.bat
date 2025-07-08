@echo off
REM StoryGenius Windows启动脚本
REM 使用venv创建虚拟环境并运行应用

REM 设置UTF-8编码
chcp 65001 >nul

setlocal enabledelayedexpansion

echo ===========================================
echo     🎭 StoryGenius AI小说创作平台
echo ===========================================
echo.

REM 检查Python是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到python命令
    echo 请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 设置变量
set ENV_NAME=venv
set ENV_PATH=%cd%\%ENV_NAME%
set PYTHON_VERSION=3.9
set PORT=8091

echo 📦 检查虚拟环境...

REM 检查虚拟环境是否存在
if exist "%ENV_PATH%" (
    echo ✅ 虚拟环境已存在: %ENV_PATH%
) else (
    echo 🔧 创建虚拟环境: %ENV_PATH%
    python -m venv "%ENV_PATH%"
    if !errorlevel! neq 0 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)

echo.
echo 🔄 激活虚拟环境...
call "%ENV_PATH%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo ❌ 激活虚拟环境失败
    pause
    exit /b 1
)

echo 📋 安装依赖包...
if exist requirements.txt (
    pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo ❌ 安装依赖包失败
        pause
        exit /b 1
    )
) else (
    echo ⚠️  未找到requirements.txt，手动安装必要包...
    pip install gradio requests
)

echo.
echo 🔍 检查端口占用...
netstat -an | findstr ":%PORT%" >nul
if %errorlevel% equ 0 (
    echo ⚠️  端口 %PORT% 已被占用，尝试使用其他端口
    set /a PORT=%PORT%+1
)

echo.
echo 🌐 检查网络连接...
ping -n 1 8.8.8.8 >nul
if %errorlevel% neq 0 (
    echo ⚠️  网络连接异常，某些功能可能无法使用
)

echo.
echo 🚀 启动StoryGenius...
echo 访问地址: http://localhost:%PORT%

REM 获取本机IP地址
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /C:"IPv4"') do (
    set LOCAL_IP=%%i
    set LOCAL_IP=!LOCAL_IP: =!
    goto :found_ip
)
:found_ip
if defined LOCAL_IP (
    echo 局域网访问: http://!LOCAL_IP!:%PORT%
) else (
    echo 局域网访问: http://0.0.0.0:%PORT%
)

echo.
echo 按 Ctrl+C 停止服务
echo 浏览器将自动打开...

REM 设置环境变量
set PYTHONPATH=%cd%
set GRADIO_SERVER_PORT=%PORT%

REM 启动应用
python run.py

echo.
echo 👋 StoryGenius已关闭
pause