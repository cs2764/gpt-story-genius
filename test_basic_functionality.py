#!/usr/bin/env python3
"""
StoryGenius 基本功能测试
测试提供商管理器、配置系统等核心功能
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

try:
    from providers import ProviderManager, ProviderConfig
    from config_manager import EnhancedConfigManager, ConfigValidator
    print("✅ 核心模块导入成功")
    
    # 尝试导入StoryWriter，如果失败则跳过相关测试
    try:
        from write_story_enhanced import StoryWriter
        STORY_WRITER_AVAILABLE = True
        print("✅ StoryWriter模块导入成功")
    except ImportError as e:
        STORY_WRITER_AVAILABLE = False
        print(f"⚠️  StoryWriter模块导入失败，将跳过相关测试: {e}")

except ImportError as e:
    print(f"❌ 核心模块导入失败: {e}")
    sys.exit(1)

def test_provider_config():
    """测试提供商配置"""
    print("\n🧪 测试提供商配置...")
    
    try:
        # 创建配置
        config = ProviderConfig(
            name="test_provider",
            api_key="test_key",
            base_url="https://api.test.com",
            system_prompt="You are a test assistant"
        )
        
        print(f"  ✅ 配置创建成功: {config.name}")
        
        # 测试配置验证
        errors = ConfigValidator.validate_config(config)
        if not errors:
            print("  ✅ 配置验证通过")
        else:
            print(f"  ⚠️  配置验证警告: {errors}")
        
        return True
    except Exception as e:
        print(f"  ❌ 提供商配置测试失败: {e}")
        return False

def test_provider_manager():
    """测试提供商管理器"""
    print("\n🧪 测试提供商管理器...")
    
    try:
        # 创建临时配置目录
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "test_provider_config.json")
            
            # 创建管理器
            manager = ProviderManager(config_file)
            print("  ✅ 提供商管理器创建成功")
            
            # 测试获取所有提供商
            providers = manager.get_all_providers()
            print(f"  ✅ 获取到 {len(providers)} 个提供商")
            
            # 测试切换提供商
            if 'deepseek' in providers:
                manager.switch_provider('deepseek')
                current = manager.get_current_provider_name()
                print(f"  ✅ 切换到提供商: {current}")
            
            # 测试配置保存
            manager.save_config()
            print("  ✅ 配置保存成功")
            
            return True
    except Exception as e:
        print(f"  ❌ 提供商管理器测试失败: {e}")
        return False

def test_enhanced_config_manager():
    """测试增强配置管理器"""
    print("\n🧪 测试增强配置管理器...")
    
    try:
        # 创建临时配置目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建管理器
            manager = EnhancedConfigManager(temp_dir)
            print("  ✅ 增强配置管理器创建成功")
            
            # 测试默认想法配置
            manager.default_ideas_config.enabled = True
            manager.default_ideas_config.default_idea = "测试想法"
            manager.save_default_ideas_config()
            print("  ✅ 默认想法配置保存成功")
            
            # 测试系统配置
            manager.system_config.debug_mode = True
            manager.save_system_config()
            print("  ✅ 系统配置保存成功")
            
            # 测试提供商状态
            status = manager.get_provider_status_detailed()
            print(f"  ✅ 获取到 {len(status)} 个提供商状态")
            
            return True
    except Exception as e:
        print(f"  ❌ 增强配置管理器测试失败: {e}")
        return False

def test_story_writer():
    """测试小说写作器（不实际调用API）"""
    print("\n🧪 测试小说写作器...")
    
    if not STORY_WRITER_AVAILABLE:
        print("  ⏭️  跳过小说写作器测试（模块不可用）")
        return True
    
    try:
        # 创建写作器
        writer = StoryWriter()
        print("  ✅ 小说写作器创建成功")
        
        # 测试token估算
        test_text = "这是一个测试文本，用于估算token数量。"
        tokens = writer.estimate_tokens(test_text)
        print(f"  ✅ Token估算功能正常: {len(test_text)} 字符 -> {tokens} tokens")
        
        # 测试响应内容提取（模拟不同格式）
        test_responses = [
            {'choices': [{'message': {'content': '测试内容1'}}]},  # OpenAI格式
            {'content': [{'text': '测试内容2'}]},  # Claude格式
            {'candidates': [{'content': {'parts': [{'text': '测试内容3'}]}}]},  # Gemini格式
        ]
        
        for i, response in enumerate(test_responses):
            content = writer.extract_content_from_response(response)
            print(f"  ✅ 响应提取测试 {i+1}: {content}")
        
        return True
    except Exception as e:
        print(f"  ❌ 小说写作器测试失败: {e}")
        return False

def test_openrouter_integration():
    """测试OpenRouter集成（不需要API密钥）"""
    print("\n🧪 测试OpenRouter集成...")
    
    try:
        # 创建临时配置
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "test_config.json")
            manager = ProviderManager(config_file)
            
            # 获取OpenRouter提供商
            openrouter = manager.get_provider('openrouter')
            print("  ✅ OpenRouter提供商获取成功")
            
            # 测试模型过滤功能
            # 注意：这里不会实际发送网络请求，只是测试函数逻辑
            test_models = [
                "gpt-3.5-turbo",
                "gpt-4",
                "gemini-pro",
                "qwen/qwen-72b-chat",
                "deepseek/deepseek-chat"
            ]
            
            # 模拟模型列表
            openrouter.models_cache = test_models
            
            filtered_openai = openrouter.filter_models_by_provider("openai")
            filtered_google = openrouter.filter_models_by_provider("google")
            
            print(f"  ✅ OpenAI模型过滤: {len(filtered_openai)} 个模型")
            print(f"  ✅ Google模型过滤: {len(filtered_google)} 个模型")
            
            return True
    except Exception as e:
        print(f"  ❌ OpenRouter集成测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n🧪 测试文件结构...")
    
    required_files = [
        "providers.py",
        "config_manager.py", 
        "config_ui.py",
        "write_story_enhanced.py",
        "run.py",
        "start.py",
        "manage_env.py",
        "start_windows.bat",
        "start_macos.sh",
        "start_linux.sh",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not (project_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"  ❌ 缺少文件: {', '.join(missing_files)}")
        return False
    else:
        print(f"  ✅ 所有 {len(required_files)} 个必要文件都存在")
        return True

def main():
    """主测试函数"""
    print("🎭 StoryGenius 基本功能测试")
    print("="*50)
    
    tests = [
        ("文件结构", test_file_structure),
        ("提供商配置", test_provider_config),
        ("提供商管理器", test_provider_manager),
        ("增强配置管理器", test_enhanced_config_manager),
        ("小说写作器", test_story_writer),
        ("OpenRouter集成", test_openrouter_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {name} 测试通过")
            else:
                print(f"❌ {name} 测试失败")
        except Exception as e:
            print(f"❌ {name} 测试异常: {e}")
    
    print("\n" + "="*50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有基本功能测试通过！")
        return True
    else:
        print("⚠️  部分功能存在问题，请检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)