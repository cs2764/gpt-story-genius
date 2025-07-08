#!/usr/bin/env python3
"""
测试提供商API调用功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_manager import EnhancedConfigManager
from providers import ProviderConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_openrouter_error_handling():
    """测试OpenRouter错误处理"""
    print("🧪 测试OpenRouter API错误处理...")
    
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
    
    print("\n🎉 OpenRouter错误处理测试完成!")

def test_lmstudio_connection():
    """测试LM Studio连接"""
    print("\n🧪 测试LM Studio连接...")
    
    config_manager = EnhancedConfigManager()
    
    # 获取LM Studio提供商
    lmstudio_provider = config_manager.provider_manager.get_provider('lmstudio')
    
    # 测试连接
    is_connected = lmstudio_provider.test_connection()
    print(f"LM Studio 连接状态: {'✅ 已连接' if is_connected else '❌ 未连接'}")
    
    if is_connected:
        # 获取模型列表
        models = lmstudio_provider.get_models()
        print(f"可用模型: {models}")
        
        if models:
            # 测试模型调用
            test_model = models[0]
            print(f"测试模型: {test_model}")
            
            try:
                test_messages = [{"role": "user", "content": "Hello"}]
                response = lmstudio_provider.create_completion(test_messages, test_model)
                print("✅ LM Studio API调用测试成功")
                print(f"响应格式: {type(response)}")
                if isinstance(response, dict) and 'choices' in response:
                    print("✅ 响应格式正确")
                else:
                    print(f"⚠️ 响应格式: {response}")
            except Exception as e:
                print(f"❌ LM Studio API调用失败: {e}")
        else:
            print("⚠️ 无可用模型")
    else:
        print("⚠️ LM Studio未运行")
    
    print("\n🎉 LM Studio测试完成!")

def test_config_manager_model_passing():
    """测试配置管理器的模型传递"""
    print("\n🧪 测试配置管理器模型传递...")
    
    config_manager = EnhancedConfigManager()
    
    # 测试create_completion_with_monitoring方法
    test_messages = [{"role": "user", "content": "test"}]
    
    # 测试带模型参数的调用
    try:
        response = config_manager.create_completion_with_monitoring(
            messages=test_messages,
            model="test-model",
            provider_name="lmstudio"
        )
        print("✅ 模型参数传递测试成功")
    except Exception as e:
        print(f"🔍 模型参数传递测试失败（预期）: {e}")
        # 检查错误是否包含模型信息
        if "test-model" in str(e):
            print("✅ 模型参数正确传递到API调用")
        else:
            print("❌ 模型参数传递可能有问题")
    
    print("\n🎉 配置管理器测试完成!")

if __name__ == "__main__":
    test_openrouter_error_handling()
    test_lmstudio_connection()
    test_config_manager_model_passing()