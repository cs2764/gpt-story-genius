#!/usr/bin/env python3
"""
测试默认模型选择功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers import ProviderManager
from config_ui import ConfigUI
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_default_model_functionality():
    """测试默认模型功能"""
    print("🧪 测试默认模型功能...")
    
    try:
        # 测试提供商管理器
        pm = ProviderManager()
        print(f"✅ 提供商管理器初始化成功")
        print(f"📋 可用提供商: {list(pm.providers.keys())}")
        
        # 测试每个提供商的默认模型设置
        test_providers = ['deepseek', 'alicloud', 'zhipu', 'gemini', 'openrouter', 'lmstudio', 'claude']
        
        for provider_name in test_providers:
            print(f"\n📝 测试提供商: {provider_name}")
            try:
                # 获取模型列表
                models = pm.get_models_for_provider(provider_name)
                print(f"   📊 可用模型数量: {len(models)}")
                
                if models:
                    # 设置默认模型
                    first_model = models[0]
                    pm.set_default_model(provider_name, first_model)
                    print(f"   ✅ 设置默认模型: {first_model}")
                    
                    # 获取默认模型
                    default_model = pm.get_default_model(provider_name)
                    print(f"   🔍 获取默认模型: {default_model}")
                    
                    # 验证默认模型是否正确
                    if default_model == first_model:
                        print(f"   ✅ 默认模型设置验证成功")
                    else:
                        print(f"   ❌ 默认模型设置验证失败")
                else:
                    print(f"   ⚠️ 没有可用模型")
                    
            except Exception as e:
                print(f"   ❌ 测试失败: {e}")
        
        # 测试配置UI
        print(f"\n🎨 测试配置UI...")
        config_ui = ConfigUI()
        
        # 测试提供商变更事件
        provider_display_names = ['DeepSeek', '阿里云通义千问', '智谱AI GLM', 'Google Gemini', 'OpenRouter', 'LM Studio', 'Claude']
        
        for display_name in provider_display_names:
            print(f"\n🔄 测试提供商变更: {display_name}")
            try:
                # 模拟提供商变更事件
                provider_key = config_ui.get_provider_key(display_name)
                if provider_key:
                    result = config_ui.on_provider_change(display_name)
                    print(f"   ✅ 提供商变更事件处理成功")
                    print(f"   📊 返回数据项数: {len(result)}")
                else:
                    print(f"   ❌ 找不到提供商键")
            except Exception as e:
                print(f"   ❌ 测试失败: {e}")
        
        print(f"\n🎯 测试主界面函数...")
        from run import get_models_for_current_provider, update_models_dropdown
        
        # 测试获取当前提供商模型列表
        models, selected = get_models_for_current_provider()
        print(f"   📊 当前提供商模型数量: {len(models)}")
        print(f"   🎯 选择的默认模型: {selected}")
        
        # 测试模型下拉菜单更新
        for display_name in provider_display_names:
            try:
                result = update_models_dropdown(display_name)
                print(f"   ✅ {display_name} 模型下拉菜单更新成功")
                print(f"   🎯 选择的模型: {result.get('value', 'N/A')}")
            except Exception as e:
                print(f"   ❌ {display_name} 模型下拉菜单更新失败: {e}")
        
        print(f"\n🎉 所有测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_default_model_functionality()
    sys.exit(0 if success else 1)