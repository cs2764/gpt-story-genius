import json
import os
import requests
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProviderConfig:
    """AI提供商配置类"""
    name: str
    api_key: str = ""
    base_url: str = ""
    models: List[str] = None
    system_prompt: str = ""
    enabled: bool = True
    default_model: str = ""
    
    def __post_init__(self):
        if self.models is None:
            self.models = []

class AIProvider(ABC):
    """AI提供商基类"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.models_cache = []
        self.last_update = 0
        self.cache_duration = 300  # 5分钟缓存
        
    @abstractmethod
    def get_models(self) -> List[str]:
        """获取模型列表"""
        pass
        
    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接"""
        pass
        
    @abstractmethod
    def create_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        """创建聊天完成"""
        pass
        
    def _should_refresh_cache(self) -> bool:
        """判断是否需要刷新缓存"""
        return time.time() - self.last_update > self.cache_duration
    
    def _update_cache(self, models: List[str]):
        """更新缓存"""
        self.models_cache = models
        self.last_update = time.time()

class DeepSeekProvider(AIProvider):
    """DeepSeek提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.config.base_url = self.config.base_url or "https://api.deepseek.com/v1"
    
    def get_models(self) -> List[str]:
        if not self._should_refresh_cache() and self.models_cache:
            return self.models_cache
            
        try:
            # DeepSeek模型列表API是公开的，不需要API密钥
            response = requests.get(
                f"{self.config.base_url}/models",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            models = [model["id"] for model in data.get("data", [])]
            self._update_cache(models)
            return models
        except Exception as e:
            logger.warning(f"DeepSeek获取模型列表失败，使用默认模型: {e}")
            # 出错时跳过，不重试，使用默认模型
            default_models = ["deepseek-chat", "deepseek-reasoner"]
            self._update_cache(default_models)
            return default_models
    
    def test_connection(self) -> bool:
        # 如果没有API密钥，返回False
        if not self.config.api_key or self.config.api_key.strip() == "":
            return False
        try:
            # 测试简单的API调用来验证API密钥
            response = requests.post(
                f"{self.config.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def create_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        max_retries = 2
        retry_delay = 5  # 5秒延迟
        
        for attempt in range(max_retries + 1):  # 总共尝试3次（原始调用 + 2次重试）
            try:
                if attempt > 0:
                    logger.info(f"DeepSeek API 第{attempt}次重试...")
                
                response = requests.post(
                    f"{self.config.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.config.api_key}"},
                    json={
                        "model": model,
                        "messages": messages,
                        **kwargs
                    },
                    timeout=60
                )
                
                # 处理特定的HTTP状态码错误
                if response.status_code in [403, 429, 500, 502, 503, 504]:
                    error_msg = f"DeepSeek API返回{response.status_code}错误"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"DeepSeek API {response.status_code}错误重试{max_retries}次后仍然失败，程序停止")
                        raise ValueError(f"{error_msg} 已重试{max_retries}次，程序停止。")
                
                response.raise_for_status()
                if attempt > 0:
                    logger.info(f"DeepSeek API 第{attempt}次重试成功")
                return response.json()
                
            except requests.exceptions.RequestException as e:
                error_msg = f"DeepSeek API网络请求失败: {e}"
                if attempt < max_retries:
                    logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"DeepSeek API网络错误重试{max_retries}次后仍然失败，程序停止")
                    raise ValueError(f"DeepSeek API调用失败: {str(e)} 已重试{max_retries}次，程序停止。")
            except Exception as e:
                error_msg = f"DeepSeek API调用失败: {e}"
                if attempt < max_retries:
                    logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"DeepSeek API未知错误重试{max_retries}次后仍然失败，程序停止")
                    raise ValueError(f"DeepSeek API调用失败: {str(e)} 已重试{max_retries}次，程序停止。")

class AliCloudProvider(AIProvider):
    """阿里云通义千问提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.config.base_url = self.config.base_url or "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    
    def get_models(self) -> List[str]:
        # 阿里云通义千问的最新模型列表（官方文档中的可用模型）
        if not self._should_refresh_cache() and self.models_cache:
            return self.models_cache
            
        logger.info("阿里云使用已知模型列表（基于官方文档）")
        known_models = [
            "qwen-max", "qwen-plus", "qwen-turbo", "qwen-long",
            "qwen-max-0428", "qwen-max-0403", "qwen-max-0107",
            "qwen-plus-0828", "qwen-turbo-0828", "qwen-vl-plus",
            "qwen-vl-max", "qwen-audio-turbo", "qwen-audio-chat"
        ]
        self._update_cache(known_models)
        return known_models
    
    def test_connection(self) -> bool:
        try:
            response = requests.post(
                f"{self.config.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json={
                    "model": "qwen-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                }
            )
            return response.status_code == 200
        except:
            return False
    
    def create_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        try:
            response = requests.post(
                f"{self.config.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    **kwargs
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"阿里云API调用失败: {e}")
            raise

class ZhipuAIProvider(AIProvider):
    """智谱AI GLM提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.config.base_url = self.config.base_url or "https://open.bigmodel.cn/api/paas/v4"
    
    def get_models(self) -> List[str]:
        # 智谱AI GLM模型列表（基于官方文档）
        if not self._should_refresh_cache() and self.models_cache:
            return self.models_cache
            
        logger.info("智谱AI使用已知模型列表（基于官方文档）")
        known_models = [
            "glm-4-plus", "glm-4-0520", "glm-4", "glm-4-air", "glm-4-airx", 
            "glm-4-flash", "glm-4-flashx", "glm-4-long", "glm-4v-plus",
            "glm-4v", "glm-3-turbo", "cogview-3-plus", "cogview-3"
        ]
        self._update_cache(known_models)
        return known_models
    
    def test_connection(self) -> bool:
        try:
            response = requests.post(
                f"{self.config.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json={
                    "model": "glm-4-flash",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                }
            )
            return response.status_code == 200
        except:
            return False
    
    def create_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        try:
            response = requests.post(
                f"{self.config.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    **kwargs
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"智谱AI API调用失败: {e}")
            raise

class GeminiProvider(AIProvider):
    """Google Gemini提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.config.base_url = self.config.base_url or "https://generativelanguage.googleapis.com/v1beta"
    
    def get_models(self) -> List[str]:
        if not self._should_refresh_cache() and self.models_cache:
            return self.models_cache
            
        try:
            # Gemini模型列表API需要API密钥，但可以先尝试公开接口
            # 如果有API密钥，使用完整API
            if self.config.api_key and self.config.api_key.strip():
                response = requests.get(
                    f"{self.config.base_url}/models",
                    params={"key": self.config.api_key},
                    timeout=5
                )
                response.raise_for_status()
                data = response.json()
                models = [model["name"].replace("models/", "") for model in data.get("models", [])]
                self._update_cache(models)
                return models
            else:
                # 无API密钥时，返回已知的公开模型
                logger.info("Gemini API密钥未设置，返回已知模型列表")
                known_models = [
                    "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro",
                    "gemini-pro", "gemini-pro-vision"
                ]
                self._update_cache(known_models)
                return known_models
        except Exception as e:
            logger.warning(f"Gemini获取模型列表失败，使用默认模型: {e}")
            # 出错时跳过，不重试，使用默认模型
            default_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
            self._update_cache(default_models)
            return default_models
    
    def test_connection(self) -> bool:
        # 如果没有API密钥，返回False
        if not self.config.api_key or self.config.api_key.strip() == "":
            return False
        try:
            # 测试Gemini API调用
            response = requests.get(
                f"{self.config.base_url}/models",
                params={"key": self.config.api_key},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def create_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        # Gemini API格式转换
        try:
            # 转换消息格式
            contents = []
            for msg in messages:
                if msg["role"] == "user":
                    contents.append({"parts": [{"text": msg["content"]}]})
                elif msg["role"] == "assistant":
                    contents.append({"parts": [{"text": msg["content"]}], "role": "model"})
            
            response = requests.post(
                f"{self.config.base_url}/models/{model}:generateContent",
                params={"key": self.config.api_key},
                json={
                    "contents": contents,
                    "generationConfig": kwargs
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            raise

class OpenRouterProvider(AIProvider):
    """OpenRouter提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.config.base_url = self.config.base_url or "https://openrouter.ai/api/v1"
    
    def get_models(self) -> List[str]:
        if not self._should_refresh_cache() and self.models_cache:
            return self.models_cache
            
        try:
            # OpenRouter无需API密钥即可获取模型列表
            response = requests.get(f"{self.config.base_url}/models", timeout=5)
            response.raise_for_status()
            data = response.json()
            all_models = [model["id"] for model in data.get("data", [])]
            
            # 默认过滤只显示主要提供商的模型
            filtered_models = self._filter_main_providers(all_models)
            self._update_cache(filtered_models)
            return filtered_models
        except Exception as e:
            logger.warning(f"OpenRouter获取模型列表失败，使用默认模型: {e}")
            # 出错时跳过，不重试，使用默认模型
            default_models = ["openai/gpt-4o", "openai/gpt-4o-mini", "deepseek/deepseek-chat", "google/gemini-pro"]
            self._update_cache(default_models)
            return default_models
    
    def _filter_main_providers(self, models: List[str]) -> List[str]:
        """过滤只显示主要提供商的模型"""
        main_provider_prefixes = [
            # OpenAI
            "openai/gpt-", "o1-",
            # Google
            "google/gemini-", "google/palm-",
            # DeepSeek
            "deepseek/",
            # Qwen/Alibaba
            "qwen/", "alibaba/",
            # Grok/xAI
            "grok-", "x-ai/grok"
        ]
        
        filtered = []
        for model in models:
            if any(model.startswith(prefix) or prefix in model.lower() for prefix in main_provider_prefixes):
                filtered.append(model)
        
        # 如果过滤后没有模型，返回前20个模型作为备选
        if not filtered:
            filtered = models[:20]
        
        return sorted(filtered)
    
    def filter_models_by_provider(self, provider_filter: str = None) -> List[str]:
        """按提供商过滤模型"""
        models = self.get_models()
        if not provider_filter:
            return models
            
        filters = {
            "openai": ["gpt-", "o1-"],
            "google": ["gemini-", "palm-"],
            "qwen": ["qwen/", "alibaba/"],
            "deepseek": ["deepseek/"],
            "grok": ["grok-", "x-ai/"]
        }
        
        if provider_filter.lower() in filters:
            prefixes = filters[provider_filter.lower()]
            return [model for model in models if any(model.startswith(prefix) for prefix in prefixes)]
        
        return models
    
    def test_connection(self) -> bool:
        # 如果没有API密钥，返回False
        if not self.config.api_key or self.config.api_key.strip() == "":
            return False
        try:
            models = self.get_models()
            return len(models) > 0
        except:
            return False
    
    def verify_model_access(self, model: str) -> bool:
        """验证模型是否可访问"""
        try:
            available_models = self.get_models()
            return model in available_models
        except:
            return False
    
    def create_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        max_retries = 2
        retry_delay = 5  # 5秒延迟
        
        for attempt in range(max_retries + 1):  # 总共尝试3次（原始调用 + 2次重试）
            try:
                # 验证API密钥格式
                if not self.config.api_key or len(self.config.api_key) < 10:
                    raise ValueError("OpenRouter API密钥无效。请在配置页面设置有效的API密钥。")
                
                # 验证模型可用性（仅第一次尝试时检查）
                if attempt == 0 and not self.verify_model_access(model):
                    logger.warning(f"模型 '{model}' 可能不在可用列表中")
                    available_models = self.get_models()[:5]  # 显示前5个可用模型
                    logger.info(f"可用模型示例: {', '.join(available_models)}")
                
                # 设置推荐的headers
                headers = {
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                }
                
                # 添加可选的应用标识headers
                if hasattr(self, 'app_name'):
                    headers["X-Title"] = self.app_name
                if hasattr(self, 'site_url'):
                    headers["HTTP-Referer"] = self.site_url
                
                if attempt > 0:
                    logger.info(f"OpenRouter API 第{attempt}次重试...")
                
                response = requests.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": messages,
                        **kwargs
                    },
                    timeout=60
                )
                
                # 尝试解析错误响应的详细信息
                error_details = ""
                try:
                    error_response = response.json()
                    if 'error' in error_response:
                        error_details = f" 详细信息: {error_response['error']}"
                        if 'metadata' in error_response:
                            metadata = error_response['metadata']
                            if 'reasons' in metadata:
                                error_details += f" 原因: {', '.join(metadata['reasons'])}"
                            if 'flagged_input' in metadata:
                                error_details += f" 被标记的输入: {metadata['flagged_input'][:100]}..."
                except:
                    pass
                
                if response.status_code == 400:
                    error_msg = f"OpenRouter请求参数错误{error_details}。请检查请求格式和参数。"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                elif response.status_code == 401:
                    error_msg = f"OpenRouter API密钥无效或已过期{error_details}。请检查您的API密钥配置。"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                elif response.status_code == 402:
                    error_msg = f"OpenRouter账户余额不足{error_details}。请充值后重试。"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                elif response.status_code == 403:
                    error_msg = f"OpenRouter内容审核被拒绝{error_details}。模型'{model}'要求内容审核，您的输入被标记。请修改输入内容。"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"OpenRouter API 403错误重试{max_retries}次后仍然失败，程序停止")
                        raise ValueError(f"{error_msg} 已重试{max_retries}次，程序停止。")
                elif response.status_code == 408:
                    error_msg = f"OpenRouter请求超时{error_details}。请求处理时间过长。"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"OpenRouter API 408错误重试{max_retries}次后仍然失败，程序停止")
                        raise ValueError(f"{error_msg} 已重试{max_retries}次，程序停止。")
                elif response.status_code == 429:
                    error_msg = f"OpenRouter API调用频率过高{error_details}。已超过速率限制。"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"OpenRouter API 429错误重试{max_retries}次后仍然失败，程序停止")
                        raise ValueError(f"{error_msg} 已重试{max_retries}次，程序停止。")
                elif response.status_code == 502:
                    error_msg = f"OpenRouter网关错误{error_details}。所选模型'{model}'可能已宕机或响应无效。"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"OpenRouter API 502错误重试{max_retries}次后仍然失败，程序停止")
                        raise ValueError(f"{error_msg} 建议尝试其他模型。已重试{max_retries}次，程序停止。")
                elif response.status_code == 503:
                    error_msg = f"OpenRouter服务不可用{error_details}。没有可用的模型提供商满足路由要求。"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"OpenRouter API 503错误重试{max_retries}次后仍然失败，程序停止")
                        raise ValueError(f"{error_msg} 建议调整模型选择。已重试{max_retries}次，程序停止。")
                
                response.raise_for_status()
                if attempt > 0:
                    logger.info(f"OpenRouter API 第{attempt}次重试成功")
                return response.json()
                
            except requests.exceptions.RequestException as e:
                error_msg = f"OpenRouter API网络请求失败: {e}"
                
                # 创建增强的异常，包含详细信息
                enhanced_exception = ValueError(f"OpenRouter API调用失败: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    enhanced_exception.error_code = getattr(e.response, 'status_code', 0)
                    try:
                        enhanced_exception.error_details = e.response.text
                    except:
                        enhanced_exception.error_details = ""
                else:
                    enhanced_exception.error_code = 0
                    enhanced_exception.error_details = ""
                
                if attempt < max_retries:
                    logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"OpenRouter API网络错误重试{max_retries}次后仍然失败，程序停止")
                    enhanced_exception = ValueError(f"OpenRouter API调用失败: {str(e)} 已重试{max_retries}次，程序停止。")
                    enhanced_exception.error_code = getattr(e, 'response', {}).get('status_code', 0) if hasattr(e, 'response') else 0
                    enhanced_exception.error_details = getattr(e, 'response', {}).get('text', '') if hasattr(e, 'response') else ''
                    raise enhanced_exception
            except ValueError as e:
                # ValueError通常是配置错误，不需要重试
                # 确保包含错误详细信息
                if not hasattr(e, 'error_code'):
                    e.error_code = 0
                if not hasattr(e, 'error_details'):
                    e.error_details = ""
                raise e
            except Exception as e:
                error_msg = f"OpenRouter API调用失败: {e}"
                
                # 创建增强的异常
                enhanced_exception = ValueError(f"OpenRouter API调用失败: {str(e)}")
                enhanced_exception.error_code = 0
                enhanced_exception.error_details = ""
                
                if attempt < max_retries:
                    logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"OpenRouter API未知错误重试{max_retries}次后仍然失败，程序停止")
                    enhanced_exception = ValueError(f"OpenRouter API调用失败: {str(e)} 已重试{max_retries}次，程序停止。")
                    enhanced_exception.error_code = 0
                    enhanced_exception.error_details = str(e)
                    raise enhanced_exception

class LMStudioProvider(AIProvider):
    """LM Studio本地提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.config.base_url = self.config.base_url or "http://localhost:1234/v1"
    
    def get_models(self) -> List[str]:
        if not self._should_refresh_cache() and self.models_cache:
            return self.models_cache
            
        try:
            # LM Studio模型列表API不需要认证
            response = requests.get(f"{self.config.base_url}/models", timeout=5)
            response.raise_for_status()
            data = response.json()
            models = [model["id"] for model in data.get("data", [])]
            self._update_cache(models)
            logger.info(f"LM Studio获取到 {len(models)} 个模型")
            return models
        except Exception as e:
            logger.warning(f"LM Studio获取模型列表失败，可能未运行: {e}")
            # 出错时跳过，不重试，返回空列表
            self._update_cache([])
            return []
    
    def test_connection(self) -> bool:
        try:
            # LM Studio不需要API密钥，直接测试连接
            response = requests.get(f"{self.config.base_url}/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def create_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        try:
            response = requests.post(
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    **kwargs
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"LM Studio API调用失败: {e}")
            raise

class GrokProvider(AIProvider):
    """Grok (x.ai) 提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.config.base_url = self.config.base_url or "https://api.x.ai/v1"
    
    def get_models(self) -> List[str]:
        if not self._should_refresh_cache() and self.models_cache:
            return self.models_cache
        
        # 如果没有API密钥，直接返回默认模型
        if not self.config.api_key or self.config.api_key.strip() == "":
            logger.info("Grok API密钥未设置，使用默认模型列表")
            default_models = [
                "grok-3-mini", "grok-3",
                "grok-beta", "grok-vision-beta", 
                "grok-2-1212", "grok-2-vision-1212",
                "grok-2-public", "grok-2-vision-public"
            ]
            self._update_cache(default_models)
            return default_models
            
        try:
            response = requests.get(
                f"{self.config.base_url}/models",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            models = [model["id"] for model in data.get("data", [])]
            
            # Grok API可能返回空列表，但实际支持这些模型
            if not models:
                logger.info("Grok API返回空模型列表，使用已知可用模型")
                default_models = [
                    "grok-3-mini", "grok-3",
                    "grok-beta", "grok-vision-beta", 
                    "grok-2-1212", "grok-2-vision-1212",
                    "grok-2-public", "grok-2-vision-public"
                ]
                self._update_cache(default_models)
                return default_models
            
            self._update_cache(models)
            logger.info(f"Grok获取到 {len(models)} 个真实模型")
            return models
        except Exception as e:
            logger.warning(f"Grok获取模型列表失败，使用默认模型: {e}")
            # 使用已知的Grok模型
            default_models = [
                "grok-3-mini", "grok-3",
                "grok-beta", "grok-vision-beta", 
                "grok-2-1212", "grok-2-vision-1212",
                "grok-2-public", "grok-2-vision-public"
            ]
            self._update_cache(default_models)
            return default_models
    
    def test_connection(self) -> bool:
        if not self.config.api_key or self.config.api_key.strip() == "":
            return False
        try:
            # 测试简单的API调用
            response = requests.get(
                f"{self.config.base_url}/models",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=10
            )
            # 如果API返回200状态码，即使没有模型列表也表示连接成功
            return response.status_code == 200
        except:
            return False
    
    def create_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        max_retries = 2
        retry_delay = 5  # 5秒延迟
        
        for attempt in range(max_retries + 1):  # 总共尝试3次
            try:
                if attempt > 0:
                    logger.info(f"Grok API 第{attempt}次重试...")
                
                response = requests.post(
                    f"{self.config.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.config.api_key}"},
                    json={
                        "model": model,
                        "messages": messages,
                        **kwargs
                    },
                    timeout=120  # Grok可能需要更长时间
                )
                
                # 尝试提取详细的错误信息
                error_details = ""
                if not response.ok:
                    try:
                        error_data = response.json()
                        error_details = f" - {error_data.get('error', {}).get('message', '')}"
                    except:
                        error_details = f" - HTTP {response.status_code}"
                
                # 处理特定的HTTP状态码错误
                if response.status_code == 400:
                    error_msg = f"Grok请求格式错误{error_details}。请检查模型名称和参数格式。"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                elif response.status_code == 401:
                    error_msg = f"Grok API密钥无效{error_details}。请检查API密钥是否正确。"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                elif response.status_code == 402:
                    error_msg = f"Grok账户余额不足{error_details}。请充值后重试。"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                elif response.status_code == 403:
                    error_msg = f"Grok内容审核被拒绝{error_details}。模型要求内容审核，您的输入被标记。请修改输入内容。"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"Grok 403错误重试{max_retries}次后仍然失败，程序停止")
                        raise ValueError(f"{error_msg} 已重试{max_retries}次，程序停止。")
                elif response.status_code == 408:
                    error_msg = f"Grok请求超时{error_details}。"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"Grok 408错误重试{max_retries}次后仍然失败，程序停止")
                        raise ValueError(f"{error_msg} 已重试{max_retries}次，程序停止。")
                elif response.status_code == 429:
                    error_msg = f"Grok请求频率限制{error_details}。API调用过于频繁。"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"Grok 429错误重试{max_retries}次后仍然失败，程序停止")
                        raise ValueError(f"{error_msg} 已重试{max_retries}次，程序停止。")
                elif response.status_code == 502:
                    error_msg = f"Grok服务器网关错误{error_details}。"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"Grok 502错误重试{max_retries}次后仍然失败，程序停止")
                        raise ValueError(f"{error_msg} 已重试{max_retries}次，程序停止。")
                elif response.status_code == 503:
                    error_msg = f"Grok服务暂时不可用{error_details}。"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"Grok 503错误重试{max_retries}次后仍然失败，程序停止")
                        raise ValueError(f"{error_msg} 已重试{max_retries}次，程序停止。")
                
                response.raise_for_status()
                if attempt > 0:
                    logger.info(f"Grok API 第{attempt}次重试成功")
                return response.json()
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Grok API网络请求失败: {e}"
                if attempt < max_retries:
                    logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Grok API网络错误重试{max_retries}次后仍然失败，程序停止")
                    # 创建增强的异常对象
                    enhanced_exception = ValueError(f"Grok API调用失败: {str(e)} 已重试{max_retries}次，程序停止。")
                    enhanced_exception.error_code = 0
                    enhanced_exception.error_details = str(e)
                    raise enhanced_exception
            except Exception as e:
                error_msg = f"Grok API调用失败: {e}"
                if attempt < max_retries:
                    logger.warning(f"{error_msg} 将在{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Grok API未知错误重试{max_retries}次后仍然失败，程序停止")
                    # 创建增强的异常对象
                    enhanced_exception = ValueError(f"Grok API调用失败: {str(e)} 已重试{max_retries}次，程序停止。")
                    enhanced_exception.error_code = 0
                    enhanced_exception.error_details = str(e)
                    raise enhanced_exception

class ClaudeProvider(AIProvider):
    """Claude提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.config.base_url = self.config.base_url or "https://api.anthropic.com/v1"
    
    def get_models(self) -> List[str]:
        if not self._should_refresh_cache() and self.models_cache:
            return self.models_cache
            
        # Claude没有公开的模型列表API，返回已知模型
        logger.info("Claude使用已知模型列表（官方不提供公开API）")
        known_models = [
            "claude-3-5-sonnet-20241022", "claude-3-5-sonnet-20240620",
            "claude-3-5-haiku-20241022", "claude-3-opus-20240229", 
            "claude-3-sonnet-20240229", "claude-3-haiku-20240307"
        ]
        self._update_cache(known_models)
        return known_models
    
    def test_connection(self) -> bool:
        # 如果没有API密钥，返回False
        if not self.config.api_key or self.config.api_key.strip() == "":
            return False
        try:
            # 测试Claude API调用（使用一个简单的请求）
            response = requests.post(
                f"{self.config.base_url}/messages",
                headers={
                    "x-api-key": self.config.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def create_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        try:
            response = requests.post(
                f"{self.config.base_url}/messages",
                headers={
                    "x-api-key": self.config.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": kwargs.get("max_tokens", 1024),
                    **{k: v for k, v in kwargs.items() if k != "max_tokens"}
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Claude API调用失败: {e}")
            raise

class ProviderManager:
    """AI提供商管理器"""
    
    def __init__(self, config_file: str = "provider_config.json"):
        self.config_file = config_file
        self.providers = {}
        self.current_provider = None
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_provider = data.get('current_provider', 'deepseek')
                    
                    # 加载提供商配置
                    for provider_name, provider_data in data.get('providers', {}).items():
                        config = ProviderConfig(**provider_data)
                        self.add_provider(provider_name, config)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        default_providers = {
            'deepseek': ProviderConfig(name='DeepSeek'),
            'alicloud': ProviderConfig(name='阿里云'),
            'zhipu': ProviderConfig(name='智谱AI'),
            'gemini': ProviderConfig(name='Google Gemini'),
            'openrouter': ProviderConfig(name='OpenRouter'),
            'lmstudio': ProviderConfig(name='LM Studio'),
            'claude': ProviderConfig(name='Claude'),
            'grok': ProviderConfig(name='Grok')
        }
        
        for name, config in default_providers.items():
            self.add_provider(name, config)
        
        self.current_provider = 'deepseek'
        self.save_config()
    
    def add_provider(self, name: str, config: ProviderConfig):
        """添加提供商"""
        provider_classes = {
            'deepseek': DeepSeekProvider,
            'alicloud': AliCloudProvider,
            'zhipu': ZhipuAIProvider,
            'gemini': GeminiProvider,
            'openrouter': OpenRouterProvider,
            'lmstudio': LMStudioProvider,
            'claude': ClaudeProvider,
            'grok': GrokProvider
        }
        
        if name in provider_classes:
            self.providers[name] = provider_classes[name](config)
        else:
            logger.warning(f"未知的提供商: {name}")
    
    def get_provider(self, name: str = None) -> AIProvider:
        """获取提供商"""
        provider_name = name or self.current_provider
        if provider_name in self.providers:
            return self.providers[provider_name]
        else:
            raise ValueError(f"提供商 '{provider_name}' 不存在")
    
    def switch_provider(self, name: str):
        """切换提供商"""
        if name in self.providers:
            self.current_provider = name
            self.save_config()
            logger.info(f"切换到提供商: {name}")
        else:
            raise ValueError(f"提供商 '{name}' 不存在")
    
    def set_provider(self, name: str):
        """设置提供商（向后兼容的别名）"""
        return self.switch_provider(name)
    
    def update_provider_config(self, name: str, **kwargs):
        """更新提供商配置"""
        if name in self.providers:
            provider = self.providers[name]
            for key, value in kwargs.items():
                if hasattr(provider.config, key):
                    setattr(provider.config, key, value)
            self.save_config()
            logger.info(f"更新提供商配置: {name}")
        else:
            raise ValueError(f"提供商 '{name}' 不存在")
    
    def save_config(self):
        """保存配置文件"""
        try:
            config_data = {
                'current_provider': self.current_provider,
                'providers': {}
            }
            
            for name, provider in self.providers.items():
                config_data['providers'][name] = asdict(provider.config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def get_all_providers(self) -> Dict[str, ProviderConfig]:
        """获取所有提供商配置"""
        return {name: provider.config for name, provider in self.providers.items()}
    
    def test_all_connections(self) -> Dict[str, bool]:
        """测试所有提供商连接"""
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = provider.test_connection()
            except Exception as e:
                logger.error(f"测试 {name} 连接失败: {e}")
                results[name] = False
        return results
    
    def get_models_for_provider(self, provider_name: str) -> List[str]:
        """获取指定提供商的模型列表"""
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            # 强制刷新缓存以确保获取最新模型列表
            provider.last_update = 0
            return provider.get_models()
        return []
    
    def get_current_provider_name(self) -> str:
        """获取当前提供商名称"""
        return self.current_provider
    
    def get_provider_status(self) -> Dict[str, Dict]:
        """获取所有提供商状态"""
        status = {}
        for name, provider in self.providers.items():
            try:
                is_connected = provider.test_connection()
                models = provider.get_models()
                status[name] = {
                    'connected': is_connected,
                    'models_count': len(models),
                    'api_key_set': bool(provider.config.api_key),
                    'enabled': provider.config.enabled,
                    'default_model': provider.config.default_model
                }
            except Exception as e:
                status[name] = {
                    'connected': False,
                    'models_count': 0,
                    'api_key_set': bool(provider.config.api_key),
                    'enabled': False,
                    'error': str(e),
                    'default_model': provider.config.default_model
                }
        return status
    
    def set_default_model(self, provider_name: str, model_name: str):
        """设置提供商的默认模型"""
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            models = provider.get_models()
            if model_name in models:
                provider.config.default_model = model_name
                self.save_config()
                logger.info(f"设置 {provider_name} 默认模型为: {model_name}")
            else:
                raise ValueError(f"模型 '{model_name}' 在提供商 '{provider_name}' 中不存在")
        else:
            raise ValueError(f"提供商 '{provider_name}' 不存在")
    
    def get_default_model(self, provider_name: str) -> str:
        """获取提供商的默认模型"""
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            default_model = provider.config.default_model
            if default_model:
                models = provider.get_models()
                if default_model in models:
                    return default_model
                else:
                    # 如果默认模型不存在，返回第一个可用模型
                    if models:
                        return models[0]
            # 如果没有设置默认模型，返回第一个可用模型
            models = provider.get_models()
            return models[0] if models else ""
        return ""