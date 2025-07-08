#!/usr/bin/env python3
"""
测试模型选择功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_manager import EnhancedConfigManager
from providers import ProviderConfig
from write_story_enhanced import StoryWriter
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_model_selection():
    """测试模型选择功能"""
    print("🧪 测试模型选择功能...")
    
    # 初始化
    config_manager = EnhancedConfigManager()
    writer = StoryWriter()
    
    # 测试OpenRouter配置
    print("\n🔍 测试OpenRouter API密钥验证...")
    
    # 设置一个无效的API密钥
    config_manager.provider_manager.update_provider_config(
        'openrouter',
        api_key='sk-test-invalid-key',
        base_url='https://openrouter.ai/api/v1'
    )
    
    # 切换到OpenRouter
    config_manager.provider_manager.switch_provider('openrouter')
    
    # 测试模型设置
    print("\n🔍 测试模型设置功能...")
    test_model = "openai/gpt-3.5-turbo"
    writer.current_model = test_model
    print(f"设置测试模型: {test_model}")
    
    # 测试create_completion_with_monitoring方法
    print("\n🔍 测试API调用模型传递...")
    test_messages = [
        {"role": "system", "content": "你是一个测试助手"},
        {"role": "user", "content": "请简单回复：测试"}
    ]
    
    try:
        # 这应该会因为无效的API密钥而失败，但会显示正确的错误信息
        response = writer.create_completion_with_monitoring(test_messages)
        print("✅ API调用成功")
    except ValueError as e:
        if "OpenRouter API密钥无效" in str(e):
            print("✅ API密钥验证测试通过 - 正确识别无效密钥")
        else:
            print(f"❌ 未预期的错误: {e}")
    except Exception as e:
        print(f"🔍 API调用失败（预期）: {e}")
    
    # 测试LM Studio配置
    print("\n🔍 测试LM Studio配置...")
    
    # 设置LM Studio配置
    config_manager.provider_manager.update_provider_config(
        'lmstudio',
        api_key='',  # LM Studio通常不需要API密钥
        base_url='http://localhost:1234/v1'
    )
    
    # 测试获取LM Studio模型
    lmstudio_provider = config_manager.provider_manager.get_provider('lmstudio')
    models = lmstudio_provider.get_models()
    print(f"LM Studio 可用模型: {models}")
    
    if models:
        test_model = models[0]
        writer.current_model = test_model
        print(f"✅ LM Studio模型设置测试通过: {test_model}")
    else:
        print("⚠️ LM Studio未运行或无可用模型")
    
    print("\n🎉 模型选择功能测试完成!")

def test_api_error_handling():
    """测试API错误处理"""
    print("\n🧪 测试API错误处理...")
    
    config_manager = EnhancedConfigManager()
    
    # 测试OpenRouter提供商
    openrouter_provider = config_manager.provider_manager.get_provider('openrouter')
    
    # 测试不同的错误情况
    test_cases = [
        {"api_key": "", "expected": "OpenRouter API密钥无效"},
        {"api_key": "sk-short", "expected": "OpenRouter API密钥无效"},
        {"api_key": "sk-test-invalid-key-12345678901234567890", "expected": "OpenRouter API密钥无效或已过期"}
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\n测试案例 {i+1}: API密钥 = '{case['api_key']}'")
        
        # 设置API密钥
        openrouter_provider.config.api_key = case['api_key']
        
        try:
            test_messages = [{"role": "user", "content": "test"}]
            response = openrouter_provider.create_completion(test_messages, "openai/gpt-3.5-turbo")
            print("❌ 应该失败但成功了")
        except ValueError as e:
            if case['expected'] in str(e):
                print(f"✅ 错误处理正确: {e}")
            else:
                print(f"❌ 错误信息不匹配: {e}")
        except Exception as e:
            print(f"🔍 其他错误: {e}")
    
    print("\n🎉 API错误处理测试完成!")

if __name__ == "__main__":
    test_model_selection()
    test_api_error_handling()