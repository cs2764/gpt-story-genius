#!/bin/bash

# StoryGenius Linux启动脚本
# 使用conda创建虚拟环境并运行应用

set -e

echo "==========================================="
echo "     🎭 StoryGenius AI小说创作平台"
echo "==========================================="
echo

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 设置变量
ENV_NAME="venv"
ENV_PATH="$(pwd)/$ENV_NAME"
PYTHON_VERSION="3.9"
PORT=8091

# 检查系统架构
ARCH=$(uname -m)
echo -e "${BLUE}系统架构: $ARCH${NC}"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到python3命令${NC}"
    echo "请先安装Python 3.8+"
    echo
    echo "安装方法："
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-venv python3-pip"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    echo "  Arch: sudo pacman -S python python-pip"
    exit 1
fi

echo -e "${BLUE}📦 检查虚拟环境...${NC}"

# 检查虚拟环境是否存在
if [ -d "$ENV_PATH" ]; then
    echo -e "${GREEN}✅ 虚拟环境已存在: $ENV_PATH${NC}"
else
    echo -e "${YELLOW}🔧 创建虚拟环境: $ENV_PATH${NC}"
    python3 -m venv "$ENV_PATH"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 虚拟环境创建成功${NC}"
    else
        echo -e "${RED}❌ 创建虚拟环境失败${NC}"
        exit 1
    fi
fi

echo
echo -e "${BLUE}🔄 激活虚拟环境...${NC}"

# 激活虚拟环境
source "$ENV_PATH/bin/activate"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 虚拟环境激活成功${NC}"
else
    echo -e "${RED}❌ 激活虚拟环境失败${NC}"
    exit 1
fi

echo -e "${BLUE}📋 安装依赖包...${NC}"

# 更新pip
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 依赖包安装成功${NC}"
    else
        echo -e "${RED}❌ 安装依赖包失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  未找到requirements.txt，手动安装必要包...${NC}"
    pip install gradio requests
fi

echo
echo -e "${BLUE}🔍 检查端口占用...${NC}"
if ss -tuln | grep -q ":$PORT "; then
    echo -e "${YELLOW}⚠️  端口 $PORT 已被占用，尝试使用其他端口${NC}"
    PORT=$((PORT + 1))
fi

echo
echo -e "${BLUE}🌐 检查网络连接...${NC}"
if ping -c 1 8.8.8.8 &> /dev/null; then
    echo -e "${GREEN}✅ 网络连接正常${NC}"
else
    echo -e "${YELLOW}⚠️  网络连接异常，某些功能可能无法使用${NC}"
fi

echo
echo -e "${BLUE}🔧 检查系统依赖...${NC}"

# 检查是否有图形界面
if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    echo -e "${GREEN}✅ 检测到图形界面${NC}"
    GRAPHICAL=true
else
    echo -e "${YELLOW}⚠️  未检测到图形界面，运行在无头模式${NC}"
    GRAPHICAL=false
fi

# 检查防火墙状态
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        echo -e "${YELLOW}⚠️  UFW防火墙已启用，可能需要开放端口 $PORT${NC}"
        echo "如需局域网访问，请运行: sudo ufw allow $PORT"
    fi
fi

echo
echo -e "${BLUE}🚀 启动StoryGenius...${NC}"
echo -e "${GREEN}本地访问: http://localhost:$PORT${NC}"
echo -e "${GREEN}局域网访问: http://0.0.0.0:$PORT${NC}"

# 获取本机IP地址
LOCAL_IP=$(hostname -I | awk '{print $1}')
if [ -n "$LOCAL_IP" ]; then
    echo -e "${GREEN}局域网IP访问: http://$LOCAL_IP:$PORT${NC}"
fi

echo
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"

# 设置环境变量
export PYTHONPATH="$(pwd)"
export GRADIO_SERVER_PORT=$PORT

# 如果有图形界面，尝试自动打开浏览器
if [ "$GRAPHICAL" = true ]; then
    (sleep 3 && {
        if command -v xdg-open &> /dev/null; then
            xdg-open "http://localhost:$PORT" 2>/dev/null
        elif command -v firefox &> /dev/null; then
            firefox "http://localhost:$PORT" 2>/dev/null
        elif command -v google-chrome &> /dev/null; then
            google-chrome "http://localhost:$PORT" 2>/dev/null
        fi
    }) &
fi

# 启动应用
python run.py

echo
echo -e "${GREEN}👋 StoryGenius已关闭${NC}"