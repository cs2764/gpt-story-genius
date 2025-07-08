import json
import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from providers import ProviderManager, ProviderConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APICallMetrics:
    """API调用指标"""
    timestamp: float
    provider: str
    model: str
    tokens_used: int
    response_time: float
    cost: float
    success: bool
    error_message: str = ""

@dataclass
class DefaultIdeasConfig:
    """默认想法配置"""
    enabled: bool = False
    default_idea: str = ""
    default_writing_style: str = ""
    default_polish_requirements: str = ""

@dataclass
class SystemConfig:
    """系统配置"""
    auto_save: bool = True
    cache_models: bool = True
    debug_mode: bool = False
    max_retries: int = 3
    timeout: int = 30
    enable_monitoring: bool = True
    enable_cost_tracking: bool = True

class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_api_key(api_key: str, provider_name: str) -> bool:
        """验证API密钥格式"""
        if not api_key:
            return False
        
        # 基本格式验证
        validation_rules = {
            'deepseek': lambda key: key.startswith('sk-') and len(key) > 20,
            'alicloud': lambda key: len(key) > 20,
            'zhipu': lambda key: len(key) > 20,
            'gemini': lambda key: len(key) > 20,
            'openrouter': lambda key: key.startswith('sk-') and len(key) > 20,
            'claude': lambda key: key.startswith('sk-') and len(key) > 20
        }
        
        if provider_name in validation_rules:
            return validation_rules[provider_name](api_key)
        return len(api_key) > 10  # 通用验证
    
    @staticmethod
    def validate_base_url(url: str) -> bool:
        """验证Base URL格式"""
        if not url:
            return True  # 空URL使用默认值
        return url.startswith(('http://', 'https://'))
    
    @staticmethod
    def validate_config(config: ProviderConfig) -> List[str]:
        """验证提供商配置"""
        errors = []
        
        if not config.name:
            errors.append("提供商名称不能为空")
        
        if config.api_key and not ConfigValidator.validate_api_key(config.api_key, config.name.lower()):
            errors.append(f"API密钥格式不正确: {config.name}")
        
        if config.base_url and not ConfigValidator.validate_base_url(config.base_url):
            errors.append(f"Base URL格式不正确: {config.base_url}")
        
        return errors

class MonitoringManager:
    """监控管理器"""
    
    def __init__(self, config_file: str = "monitoring_data.json"):
        self.config_file = config_file
        self.metrics: List[APICallMetrics] = []
        self.load_metrics()
    
    def load_metrics(self):
        """加载监控数据"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metrics = [APICallMetrics(**metric) for metric in data.get('metrics', [])]
            except Exception as e:
                logger.error(f"加载监控数据失败: {e}")
                self.metrics = []
    
    def save_metrics(self):
        """保存监控数据"""
        try:
            data = {
                'metrics': [asdict(metric) for metric in self.metrics[-1000:]]  # 只保存最近1000条
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存监控数据失败: {e}")
    
    def record_api_call(self, provider: str, model: str, tokens_used: int, 
                       response_time: float, cost: float, success: bool, 
                       error_message: str = ""):
        """记录API调用"""
        metric = APICallMetrics(
            timestamp=time.time(),
            provider=provider,
            model=model,
            tokens_used=tokens_used,
            response_time=response_time,
            cost=cost,
            success=success,
            error_message=error_message
        )
        self.metrics.append(metric)
        self.save_metrics()
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取监控摘要"""
        cutoff_time = time.time() - (hours * 3600)
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_cost': 0,
                'total_tokens': 0,
                'average_response_time': 0,
                'provider_stats': {}
            }
        
        total_calls = len(recent_metrics)
        successful_calls = sum(1 for m in recent_metrics if m.success)
        failed_calls = total_calls - successful_calls
        total_cost = sum(m.cost for m in recent_metrics)
        total_tokens = sum(m.tokens_used for m in recent_metrics)
        avg_response_time = sum(m.response_time for m in recent_metrics) / total_calls
        
        # 按提供商统计
        provider_stats = {}
        for metric in recent_metrics:
            if metric.provider not in provider_stats:
                provider_stats[metric.provider] = {
                    'calls': 0,
                    'successful': 0,
                    'cost': 0,
                    'tokens': 0,
                    'avg_response_time': 0
                }
            
            stats = provider_stats[metric.provider]
            stats['calls'] += 1
            if metric.success:
                stats['successful'] += 1
            stats['cost'] += metric.cost
            stats['tokens'] += metric.tokens_used
            stats['avg_response_time'] += metric.response_time
        
        # 计算平均响应时间
        for provider, stats in provider_stats.items():
            if stats['calls'] > 0:
                stats['avg_response_time'] /= stats['calls']
        
        return {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'average_response_time': avg_response_time,
            'provider_stats': provider_stats
        }

class CostTracker:
    """成本追踪器"""
    
    # 模型定价信息 (每1000个token的价格，单位美元)
    MODEL_PRICING = {
        'deepseek': {
            'deepseek-chat': {'input': 0.0014, 'output': 0.0028},
            'deepseek-reasoner': {'input': 0.0055, 'output': 0.0280}
        },
        'alicloud': {
            'qwen-max': {'input': 0.02, 'output': 0.06},
            'qwen-plus': {'input': 0.008, 'output': 0.024},
            'qwen-turbo': {'input': 0.003, 'output': 0.006}
        },
        'zhipu': {
            'glm-4': {'input': 0.05, 'output': 0.05},
            'glm-4-flash': {'input': 0.001, 'output': 0.001},
            'glm-3-turbo': {'input': 0.005, 'output': 0.005}
        },
        'gemini': {
            'gemini-pro': {'input': 0.0005, 'output': 0.0015},
            'gemini-pro-vision': {'input': 0.0025, 'output': 0.0075}
        },
        'openrouter': {
            'default': {'input': 0.002, 'output': 0.006}  # 平均价格
        },
        'claude': {
            'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
            'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125}
        }
    }
    
    @staticmethod
    def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算API调用成本"""
        try:
            if provider in CostTracker.MODEL_PRICING:
                pricing = CostTracker.MODEL_PRICING[provider]
                if model in pricing:
                    model_pricing = pricing[model]
                elif 'default' in pricing:
                    model_pricing = pricing['default']
                else:
                    # 使用通用默认价格
                    model_pricing = {'input': 0.002, 'output': 0.006}
                
                input_cost = (input_tokens / 1000) * model_pricing['input']
                output_cost = (output_tokens / 1000) * model_pricing['output']
                return input_cost + output_cost
            else:
                # 未知提供商，使用默认价格
                return ((input_tokens + output_tokens) / 1000) * 0.002
        except Exception as e:
            logger.error(f"计算成本失败: {e}")
            return 0.0

class EnhancedConfigManager:
    """增强配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.ensure_config_dir()
        
        # 初始化各个管理器
        self.provider_manager = ProviderManager(
            os.path.join(self.config_dir, "provider_config.json")
        )
        self.monitoring_manager = MonitoringManager(
            os.path.join(self.config_dir, "monitoring_data.json")
        )
        
        # 加载其他配置
        self.default_ideas_config = self.load_default_ideas_config()
        self.system_config = self.load_system_config()
    
    def ensure_config_dir(self):
        """确保配置目录存在"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
    
    def load_default_ideas_config(self) -> DefaultIdeasConfig:
        """加载默认想法配置"""
        config_file = os.path.join(self.config_dir, "default_ideas.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return DefaultIdeasConfig(**data)
            except Exception as e:
                logger.error(f"加载默认想法配置失败: {e}")
        
        return DefaultIdeasConfig()
    
    def save_default_ideas_config(self):
        """保存默认想法配置"""
        config_file = os.path.join(self.config_dir, "default_ideas.json")
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.default_ideas_config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存默认想法配置失败: {e}")
    
    def load_system_config(self) -> SystemConfig:
        """加载系统配置"""
        config_file = os.path.join(self.config_dir, "system_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return SystemConfig(**data)
            except Exception as e:
                logger.error(f"加载系统配置失败: {e}")
        
        return SystemConfig()
    
    def save_system_config(self):
        """保存系统配置"""
        config_file = os.path.join(self.config_dir, "system_config.json")
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.system_config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存系统配置失败: {e}")
    
    def validate_provider_config(self, provider_name: str) -> List[str]:
        """验证提供商配置"""
        try:
            provider = self.provider_manager.get_provider(provider_name)
            return ConfigValidator.validate_config(provider.config)
        except Exception as e:
            return [f"验证配置失败: {e}"]
    
    def get_provider_status_detailed(self) -> Dict[str, Dict]:
        """获取详细的提供商状态"""
        status = self.provider_manager.get_provider_status()
        metrics = self.monitoring_manager.get_metrics_summary(24)
        
        # 添加监控数据
        for provider_name, provider_status in status.items():
            provider_metrics = metrics['provider_stats'].get(provider_name, {})
            provider_status.update({
                'recent_calls': provider_metrics.get('calls', 0),
                'success_rate': (provider_metrics.get('successful', 0) / 
                               max(provider_metrics.get('calls', 1), 1) * 100),
                'avg_response_time': provider_metrics.get('avg_response_time', 0),
                'total_cost': provider_metrics.get('cost', 0),
                'total_tokens': provider_metrics.get('tokens', 0)
            })
        
        return status
    
    def create_completion_with_monitoring(self, messages: List[Dict], 
                                        model: str = None, 
                                        provider_name: str = None,
                                        **kwargs) -> Dict:
        """带监控的完成创建"""
        start_time = time.time()
        provider_name = provider_name or self.provider_manager.get_current_provider_name()
        
        try:
            provider = self.provider_manager.get_provider(provider_name)
            
            # 如果没有指定模型，使用第一个可用模型
            if not model:
                models = provider.get_models()
                if models:
                    model = models[0]
                else:
                    raise ValueError("没有可用的模型")
            
            # 创建完成
            response = provider.create_completion(messages, model, **kwargs)
            
            # 计算指标
            response_time = time.time() - start_time
            
            # 估算token使用量
            input_tokens = sum(len(msg.get('content', '')) for msg in messages) // 4
            output_tokens = len(str(response)) // 4
            
            # 计算成本
            cost = CostTracker.calculate_cost(provider_name, model, input_tokens, output_tokens)
            
            # 记录监控数据
            if self.system_config.enable_monitoring:
                self.monitoring_manager.record_api_call(
                    provider=provider_name,
                    model=model,
                    tokens_used=input_tokens + output_tokens,
                    response_time=response_time,
                    cost=cost,
                    success=True
                )
            
            return response
            
        except Exception as e:
            # 记录失败的调用
            response_time = time.time() - start_time
            if self.system_config.enable_monitoring:
                self.monitoring_manager.record_api_call(
                    provider=provider_name,
                    model=model or "unknown",
                    tokens_used=0,
                    response_time=response_time,
                    cost=0,
                    success=False,
                    error_message=str(e)
                )
            raise
    
    def get_monitoring_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取监控摘要"""
        return self.monitoring_manager.get_metrics_summary(hours)
    
    def export_config(self, export_path: str):
        """导出配置"""
        try:
            export_data = {
                'providers': self.provider_manager.get_all_providers(),
                'current_provider': self.provider_manager.get_current_provider_name(),
                'default_ideas': asdict(self.default_ideas_config),
                'system_config': asdict(self.system_config),
                'export_time': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已导出到: {export_path}")
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            raise
    
    def import_config(self, import_path: str):
        """导入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 导入提供商配置
            if 'providers' in data:
                for name, config_data in data['providers'].items():
                    config = ProviderConfig(**config_data)
                    self.provider_manager.add_provider(name, config)
            
            # 设置当前提供商
            if 'current_provider' in data:
                self.provider_manager.switch_provider(data['current_provider'])
            
            # 导入默认想法配置
            if 'default_ideas' in data:
                self.default_ideas_config = DefaultIdeasConfig(**data['default_ideas'])
                self.save_default_ideas_config()
            
            # 导入系统配置
            if 'system_config' in data:
                self.system_config = SystemConfig(**data['system_config'])
                self.save_system_config()
            
            logger.info(f"配置已从 {import_path} 导入")
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            raise
    
    def reset_config(self):
        """重置配置"""
        try:
            # 重置提供商管理器
            self.provider_manager = ProviderManager(
                os.path.join(self.config_dir, "provider_config.json")
            )
            
            # 重置其他配置
            self.default_ideas_config = DefaultIdeasConfig()
            self.system_config = SystemConfig()
            
            # 保存重置后的配置
            self.save_default_ideas_config()
            self.save_system_config()
            
            logger.info("配置已重置")
            
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            raise
    
    def get_debug_info(self) -> Dict[str, Any]:
        """获取调试信息"""
        return {
            'config_dir': self.config_dir,
            'provider_manager_status': self.provider_manager.get_provider_status(),
            'monitoring_summary': self.monitoring_manager.get_metrics_summary(1),
            'default_ideas_config': asdict(self.default_ideas_config),
            'system_config': asdict(self.system_config),
            'config_files': {
                'provider_config': os.path.exists(os.path.join(self.config_dir, "provider_config.json")),
                'monitoring_data': os.path.exists(os.path.join(self.config_dir, "monitoring_data.json")),
                'default_ideas': os.path.exists(os.path.join(self.config_dir, "default_ideas.json")),
                'system_config': os.path.exists(os.path.join(self.config_dir, "system_config.json"))
            }
        }