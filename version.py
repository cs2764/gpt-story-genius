"""版本信息模块"""

__version__ = "2.1.0"
__version_info__ = (2, 1, 0)

# 版本发布信息
VERSION_INFO = {
    "version": __version__,
    "release_date": "2025-01-10",
    "codename": "Enhanced Writing Style",
    "description": "多AI提供商智能小说创作平台 - 写作风格增强版",
    "major_features": [
        "支持8个AI提供商（DeepSeek、阿里云、智谱AI、Gemini、OpenRouter、LM Studio、Claude、Grok）",
        "完整写作风格支持（剧情、大纲、故事线、正文全流程）",
        "中文大纲提示词优化",
        "提供商模型自动匹配修复",
        "实时监控与成本追踪",
        "智能配置管理系统"
    ]
}

def get_version():
    """获取版本号"""
    return __version__

def get_version_info():
    """获取详细版本信息"""
    return VERSION_INFO