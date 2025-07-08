"""版本信息模块"""

__version__ = "2.0.0"
__version_info__ = (2, 0, 0)

# 版本发布信息
VERSION_INFO = {
    "version": __version__,
    "release_date": "2025-01-08",
    "codename": "Multi-AI Genesis",
    "description": "多AI提供商智能小说创作平台",
    "major_features": [
        "支持7个AI提供商（DeepSeek、阿里云、智谱AI、Gemini、OpenRouter、LM Studio、Claude）",
        "实时监控与成本追踪",
        "智能配置管理系统",
        "OpenRouter深度集成",
        "跨平台启动解决方案",
        "虚拟环境架构优化"
    ]
}

def get_version():
    """获取版本号"""
    return __version__

def get_version_info():
    """获取详细版本信息"""
    return VERSION_INFO