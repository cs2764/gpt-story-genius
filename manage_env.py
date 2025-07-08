#!/usr/bin/env python3
"""
StoryGenius 虚拟环境管理工具
支持创建、删除、重建虚拟环境以及依赖管理
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path
import json

class EnvironmentManager:
    """虚拟环境管理器"""
    
    def __init__(self):
        self.env_name = "venv"
        self.python_version = "3.9"
        self.system = platform.system().lower()
        self.project_dir = Path(__file__).parent
        self.env_path = self.project_dir / self.env_name
        
    def run_command(self, command, check=True, capture_output=False):
        """运行系统命令"""
        try:
            if capture_output:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    check=check, 
                    capture_output=True, 
                    text=True
                )
                return result.stdout.strip()
            else:
                subprocess.run(command, shell=True, check=check)
                return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 命令执行失败: {command}")
            print(f"错误信息: {e}")
            return False
    
    def check_python(self):
        """检查Python是否安装"""
        try:
            result = self.run_command("python3 --version", capture_output=True)
            print(f"✅ 检测到Python: {result}")
            return True
        except:
            try:
                result = self.run_command("python --version", capture_output=True)
                print(f"✅ 检测到Python: {result}")
                return True
            except:
                print("❌ 未找到Python命令")
                print("请先安装Python 3.8+:")
                if self.system == "windows":
                    print("  下载地址: https://www.python.org/downloads/")
                elif self.system == "darwin":
                    print("  安装命令: brew install python")
                elif self.system == "linux":
                    print("  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip")
                    print("  CentOS/RHEL: sudo yum install python3 python3-pip")
                return False
    
    def env_exists(self):
        """检查虚拟环境是否存在"""
        return self.env_path.exists() and (self.env_path / "pyvenv.cfg").exists()
    
    def create_environment(self):
        """创建虚拟环境"""
        print(f"🔧 创建虚拟环境: {self.env_path}")
        
        if self.env_exists():
            print(f"⚠️  虚拟环境 {self.env_path} 已存在")
            choice = input("是否删除并重建? (y/N): ").lower()
            if choice == 'y':
                self.delete_environment()
            else:
                print("取消创建")
                return False
        
        # 创建环境
        python_cmd = "python3" if self.system != "windows" else "python"
        command = f"{python_cmd} -m venv {self.env_path}"
        if self.run_command(command):
            print(f"✅ 虚拟环境 {self.env_path} 创建成功")
            return True
        else:
            print(f"❌ 虚拟环境 {self.env_path} 创建失败")
            return False
    
    def delete_environment(self):
        """删除虚拟环境"""
        print(f"🗑️  删除虚拟环境: {self.env_path}")
        
        if not self.env_exists():
            print(f"⚠️  虚拟环境 {self.env_path} 不存在")
            return True
        
        # 确认删除
        choice = input(f"确认删除虚拟环境 {self.env_path}? (y/N): ").lower()
        if choice != 'y':
            print("取消删除")
            return False
        
        # 删除环境目录
        try:
            import shutil
            shutil.rmtree(self.env_path)
            print(f"✅ 虚拟环境 {self.env_path} 删除成功")
            return True
        except Exception as e:
            print(f"❌ 虚拟环境 {self.env_path} 删除失败: {e}")
            return False
    
    def install_dependencies(self):
        """安装依赖包"""
        print("📦 安装项目依赖...")
        
        if not self.env_exists():
            print(f"❌ 虚拟环境 {self.env_path} 不存在，请先创建")
            return False
        
        # 获取pip路径
        if self.system == "windows":
            pip_path = self.env_path / "Scripts" / "pip.exe"
        else:
            pip_path = self.env_path / "bin" / "pip"
        
        # 检查requirements.txt
        requirements_file = self.project_dir / "requirements.txt"
        if requirements_file.exists():
            print("📋 从requirements.txt安装依赖...")
            command = f"{pip_path} install -r {requirements_file}"
        else:
            print("📋 安装基础依赖包...")
            packages = [
                "gradio>=4.0.0",
                "requests",
                "python-dotenv",
                "Pillow",
                "ebooklib"
            ]
            command = f"{pip_path} install {' '.join(packages)}"
        
        if self.run_command(command):
            print("✅ 依赖安装成功")
            return True
        else:
            print("❌ 依赖安装失败")
            return False
    
    def generate_requirements(self):
        """生成requirements.txt文件"""
        print("📝 生成requirements.txt文件...")
        
        if not self.env_exists():
            print(f"❌ 虚拟环境 {self.env_path} 不存在")
            return False
        
        # 获取pip路径
        if self.system == "windows":
            pip_path = self.env_path / "Scripts" / "pip.exe"
        else:
            pip_path = self.env_path / "bin" / "pip"
        
        # 生成requirements.txt
        requirements_file = self.project_dir / "requirements.txt"
        command = f"{pip_path} freeze > {requirements_file}"
        
        if self.run_command(command):
            print("✅ requirements.txt生成成功")
            return True
        else:
            print("❌ requirements.txt生成失败")
            return False
    
    def update_environment(self):
        """更新虚拟环境"""
        print("🔄 更新虚拟环境...")
        
        if not self.env_exists():
            print(f"❌ 虚拟环境 {self.env_path} 不存在")
            return False
        
        # 获取pip路径
        if self.system == "windows":
            pip_path = self.env_path / "Scripts" / "pip.exe"
        else:
            pip_path = self.env_path / "bin" / "pip"
        
        # 更新pip
        print("更新pip...")
        self.run_command(f"{pip_path} install --upgrade pip")
        
        # 更新依赖
        if self.install_dependencies():
            print("✅ 虚拟环境更新成功")
            return True
        else:
            print("❌ 虚拟环境更新失败")
            return False
    
    def list_environments(self):
        """列出项目虚拟环境信息"""
        print("📋 项目虚拟环境信息:")
        print(f"  环境路径: {self.env_path}")
        print(f"  环境存在: {'是' if self.env_exists() else '否'}")
        if self.env_exists():
            print(f"  Python版本: {self.get_python_version()}")
    
    def get_python_version(self):
        """获取虚拟环境中的Python版本"""
        try:
            if self.system == "windows":
                python_path = self.env_path / "Scripts" / "python.exe"
            else:
                python_path = self.env_path / "bin" / "python"
            
            result = self.run_command(f"{python_path} --version", capture_output=True)
            return result
        except:
            return "未知"
    
    def environment_info(self):
        """显示环境信息"""
        print(f"🔍 环境信息:")
        print(f"  项目目录: {self.project_dir}")
        print(f"  环境路径: {self.env_path}")
        print(f"  目标Python版本: {self.python_version}")
        print(f"  操作系统: {self.system}")
        print(f"  环境存在: {'是' if self.env_exists() else '否'}")
        
        if self.env_exists():
            print(f"  实际Python版本: {self.get_python_version()}")
            print("\n📦 已安装的包:")
            if self.system == "windows":
                pip_path = self.env_path / "Scripts" / "pip.exe"
            else:
                pip_path = self.env_path / "bin" / "pip"
            self.run_command(f"{pip_path} list")
    
    def clean_cache(self):
        """清理缓存"""
        print("🧹 清理pip缓存...")
        
        if self.env_exists():
            # 清理虚拟环境的pip缓存
            if self.system == "windows":
                pip_path = self.env_path / "Scripts" / "pip.exe"
            else:
                pip_path = self.env_path / "bin" / "pip"
            self.run_command(f"{pip_path} cache purge")
        
        # 清理全局pip缓存
        self.run_command("pip cache purge")
        
        print("✅ 缓存清理完成")
    
    def backup_environment(self):
        """备份环境配置"""
        print("💾 备份环境配置...")
        
        if not self.env_exists():
            print(f"❌ 虚拟环境 {self.env_path} 不存在")
            return False
        
        # 生成requirements.txt作为备份
        if self.generate_requirements():
            print(f"✅ 环境配置已备份到: requirements.txt")
            return True
        else:
            print("❌ 环境配置备份失败")
            return False
    
    def restore_environment(self, backup_file):
        """从备份恢复环境"""
        print(f"🔄 从备份恢复环境: {backup_file}")
        
        backup_path = Path(backup_file)
        if not backup_path.exists():
            print(f"❌ 备份文件不存在: {backup_file}")
            return False
        
        # 重新创建环境
        if self.env_exists():
            self.delete_environment()
        
        if not self.create_environment():
            return False
        
        # 从requirements.txt恢复依赖
        if self.system == "windows":
            pip_path = self.env_path / "Scripts" / "pip.exe"
        else:
            pip_path = self.env_path / "bin" / "pip"
        
        command = f"{pip_path} install -r {backup_file}"
        if self.run_command(command):
            print("✅ 环境恢复成功")
            return True
        else:
            print("❌ 环境恢复失败")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="StoryGenius 虚拟环境管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python manage_env.py create          # 创建虚拟环境
  python manage_env.py delete          # 删除虚拟环境
  python manage_env.py install         # 安装依赖
  python manage_env.py update          # 更新环境
  python manage_env.py info            # 显示环境信息
  python manage_env.py backup          # 备份环境
  python manage_env.py clean           # 清理缓存
        """
    )
    
    parser.add_argument(
        'action',
        choices=[
            'create', 'delete', 'install', 'update', 'list', 
            'info', 'clean', 'backup', 'restore', 'requirements'
        ],
        help='要执行的操作'
    )
    
    parser.add_argument(
        '--backup-file',
        help='备份文件路径（用于restore操作）'
    )
    
    args = parser.parse_args()
    
    # 创建环境管理器
    manager = EnvironmentManager()
    
    print("===========================================")
    print("     🎭 StoryGenius 环境管理工具")
    print("===========================================")
    print()
    
    # 检查Python
    if not manager.check_python():
        sys.exit(1)
    
    # 执行操作
    success = True
    
    if args.action == 'create':
        success = manager.create_environment()
        if success:
            success = manager.install_dependencies()
    
    elif args.action == 'delete':
        success = manager.delete_environment()
    
    elif args.action == 'install':
        success = manager.install_dependencies()
    
    elif args.action == 'update':
        success = manager.update_environment()
    
    elif args.action == 'list':
        manager.list_environments()
    
    elif args.action == 'info':
        manager.environment_info()
    
    elif args.action == 'clean':
        manager.clean_cache()
    
    elif args.action == 'backup':
        success = manager.backup_environment()
    
    elif args.action == 'restore':
        if not args.backup_file:
            print("❌ 请指定备份文件: --backup-file <文件路径>")
            success = False
        else:
            success = manager.restore_environment(args.backup_file)
    
    elif args.action == 'requirements':
        success = manager.generate_requirements()
    
    if success:
        print("\n✅ 操作完成")
    else:
        print("\n❌ 操作失败")
        sys.exit(1)

if __name__ == "__main__":
    main()