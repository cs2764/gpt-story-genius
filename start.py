#!/usr/bin/env python3
"""
StoryGenius 统一启动器
跨平台Python启动器，自动处理依赖、端口冲突、浏览器打开，并且支持局域网访问
"""

import os
import sys
import subprocess
import platform
import socket
import webbrowser
import time
import signal
from pathlib import Path
import argparse

class StoryGeniusLauncher:
    """StoryGenius统一启动器"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.project_dir = Path(__file__).parent
        self.default_port = 8091
        self.env_name = "storygenius"
        self.process = None
        
    def check_python_version(self):
        """检查Python版本"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("❌ Python版本过低，需要Python 3.8+")
            print(f"当前版本: {version.major}.{version.minor}.{version.micro}")
            return False
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def check_port_available(self, port):
        """检查端口是否可用"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0
        except:
            return False
    
    def find_available_port(self, start_port=8091):
        """找到可用端口"""
        port = start_port
        while port < start_port + 100:  # 最多尝试100个端口
            if self.check_port_available(port):
                return port
            port += 1
        return None
    
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            # 连接到外部地址获取本机IP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            sock.close()
            return ip
        except:
            return "127.0.0.1"
    
    def install_dependencies(self):
        """安装依赖包"""
        print("📦 检查并安装依赖包...")
        
        requirements_file = self.project_dir / "requirements.txt"
        if requirements_file.exists():
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True, capture_output=True)
                print("✅ 依赖包安装/更新完成")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ 依赖包安装失败: {e}")
                print("尝试手动安装基础包...")
                
                # 尝试安装基础包
                basic_packages = ["gradio>=4.0.0", "requests", "Pillow"]
                for package in basic_packages:
                    try:
                        subprocess.run([
                            sys.executable, "-m", "pip", "install", package
                        ], check=True, capture_output=True)
                        print(f"✅ 已安装: {package}")
                    except:
                        print(f"❌ 安装失败: {package}")
                
                return True
        else:
            print("⚠️  未找到requirements.txt文件")
            return True
    
    def check_critical_files(self):
        """检查关键文件"""
        critical_files = [
            "run.py",
            "providers.py", 
            "config_manager.py",
            "config_ui.py",
            "write_story_enhanced.py"
        ]
        
        missing_files = []
        for file in critical_files:
            if not (self.project_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ 缺少关键文件: {', '.join(missing_files)}")
            return False
        
        print("✅ 关键文件检查通过")
        return True
    
    def setup_environment(self):
        """设置环境变量"""
        os.environ["PYTHONPATH"] = str(self.project_dir)
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # 设置Gradio环境变量
        os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
        os.environ["GRADIO_SERVER_NAME"] = "0.0.0.0"
    
    def open_browser(self, url, delay=3):
        """延迟打开浏览器"""
        def open_delayed():
            time.sleep(delay)
            try:
                webbrowser.open(url)
                print(f"🌐 已尝试打开浏览器: {url}")
            except Exception as e:
                print(f"⚠️  无法自动打开浏览器: {e}")
        
        import threading
        threading.Thread(target=open_delayed, daemon=True).start()
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print("\n\n🛑 收到中断信号，正在关闭StoryGenius...")
        if self.process:
            self.process.terminate()
            self.process.wait()
        print("👋 StoryGenius已安全关闭")
        sys.exit(0)
    
    def start_application(self, port, open_browser=True, share=False):
        """启动应用"""
        print(f"🚀 启动StoryGenius (端口: {port})...")
        
        # 设置环境变量
        os.environ["GRADIO_SERVER_PORT"] = str(port)
        if share:
            os.environ["GRADIO_SHARE"] = "True"
        
        # 显示访问地址
        local_ip = self.get_local_ip()
        print("\n" + "="*50)
        print("🎭 StoryGenius AI小说创作平台已启动")
        print("="*50)
        print(f"📍 本地访问: http://localhost:{port}")
        print(f"🌐 局域网访问: http://{local_ip}:{port}")
        if share:
            print("🔗 公网分享: 启动后将显示链接")
        print("="*50)
        print("💡 提示: 首次使用请先到'配置管理'页面设置AI提供商API密钥")
        print("⚠️  按 Ctrl+C 停止服务")
        print("="*50)
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 自动打开浏览器
        if open_browser:
            self.open_browser(f"http://localhost:{port}")
        
        # 启动应用
        try:
            # 切换到项目目录
            os.chdir(self.project_dir)
            
            # 启动Python应用
            self.process = subprocess.Popen([
                sys.executable, "run.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
               universal_newlines=True, bufsize=1)
            
            # 实时输出日志
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
            
            self.process.wait()
            
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False
        
        return True
    
    def run(self, args):
        """运行启动器"""
        print("🎭 StoryGenius 统一启动器")
        print("="*40)
        
        # 检查Python版本
        if not self.check_python_version():
            return False
        
        # 检查关键文件
        if not self.check_critical_files():
            return False
        
        # 设置环境
        self.setup_environment()
        
        # 安装依赖
        if args.install_deps:
            if not self.install_dependencies():
                print("❌ 依赖安装失败，但将尝试继续运行")
        
        # 查找可用端口
        port = args.port
        if not self.check_port_available(port):
            print(f"⚠️  端口 {port} 已被占用，寻找其他可用端口...")
            port = self.find_available_port(port)
            if not port:
                print("❌ 无法找到可用端口")
                return False
            print(f"✅ 使用端口: {port}")
        
        # 启动应用
        return self.start_application(
            port=port,
            open_browser=not args.no_browser,
            share=args.share
        )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="StoryGenius AI小说创作平台统一启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python start.py                    # 默认启动
  python start.py --port 8080        # 指定端口
  python start.py --no-browser       # 不自动打开浏览器
  python start.py --share             # 启用公网分享
  python start.py --install-deps     # 安装依赖包
        """
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8091,
        help="指定端口号 (默认: 8091)"
    )
    
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="不自动打开浏览器"
    )
    
    parser.add_argument(
        "--share",
        action="store_true", 
        help="启用Gradio公网分享"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="安装/更新依赖包"
    )
    
    args = parser.parse_args()
    
    # 创建启动器并运行
    launcher = StoryGeniusLauncher()
    
    try:
        success = launcher.run(args)
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ 启动器发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()