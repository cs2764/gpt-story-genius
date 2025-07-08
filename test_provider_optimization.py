#!/usr/bin/env python3
"""
测试AI提供商设置逻辑优化
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_manager import EnhancedConfigManager
from providers import ProviderConfig
import run

def test_provider_filtering():
    """测试提供商过滤功能"""
    print("🧪 测试AI提供商过滤功能...")
    
    # 初始化配置管理器
    config_manager = EnhancedConfigManager()
    
    # 清理现有配置，重新开始
    print("📝 创建测试配置...")
    
    # 只为OpenRouter设置API密钥
    config_manager.provider_manager.update_provider_config(
        'openrouter',
        api_key='sk-test-key-12345678901234567890',
        base_url='https://openrouter.ai/api/v1'
    )
    
    # 为DeepSeek设置API密钥
    config_manager.provider_manager.update_provider_config(
        'deepseek', 
        api_key='sk-test-deepseek-key-123456789'
    )
    
    print("✅ 测试配置创建完成")
    
    # 测试获取可用提供商
    print("\n🔍 测试获取可用提供商列表...")
    available_providers, current_provider = run.get_available_providers()
    print(f"可用提供商: {available_providers}")
    print(f"当前提供商: {current_provider}")
    
    # 验证结果
    expected_providers = ['DeepSeek', 'OpenRouter']
    if set(available_providers) == set(expected_providers):
        print("✅ 提供商过滤测试通过")
    else:
        print(f"❌ 提供商过滤测试失败: 期望 {expected_providers}, 实际 {available_providers}")
    
    # 测试check_providers函数
    print("\n🔍 测试check_providers函数...")
    has_providers = run.check_providers()
    print(f"有可用提供商: {has_providers}")
    
    if has_providers:
        print("✅ check_providers测试通过")
    else:
        print("❌ check_providers测试失败")
    
    # 测试状态获取
    print("\n🔍 测试获取提供商状态...")
    status = run.get_provider_status()
    print("提供商状态:")
    print(status)
    
    # 测试刷新功能
    print("\n🔍 测试刷新功能...")
    try:
        result = run.refresh_providers_and_status()
        print("✅ 刷新功能测试通过")
        print(f"刷新结果数量: {len(result)}")
    except Exception as e:
        print(f"❌ 刷新功能测试失败: {e}")
    
    print("\n🎉 所有测试完成!")

if __name__ == "__main__":
    test_provider_filtering()