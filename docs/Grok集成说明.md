# Grok API 集成说明

## 概述

StoryGenius AI小说创作平台现已完全支持**Grok API (x.ai)**，为用户提供了另一个强大的AI创作选择。Grok是由xAI公司开发的大语言模型，以其幽默风格和实时信息处理能力著称。

## 🚀 新功能特点

### 1. 完整的Grok API支持
- **最新模型**: grok-3-mini（轻量级）, grok-3（完整版）
- **基础模型**: grok-beta（标准对话模型）
- **视觉模型**: grok-vision-beta（多模态支持）
- **历史版本**: grok-2-1212, grok-2-vision-1212, grok-2-public

### 2. 增强的错误处理
- **智能重试机制**: 自动重试2次，每次间隔5秒
- **详细错误识别**: 针对不同HTTP状态码的具体错误说明
- **错误恢复**: 对可恢复错误（403、408、429、502、503）自动重试

### 3. 成本监控支持
- **实时成本计算**: 基于官方定价的Token成本估算
- **模型差异化定价**: 不同模型的精确定价
- **成本追踪**: 与现有监控系统完全集成

## 📋 配置步骤

### 1. 获取API密钥
1. 访问 [x.ai控制台](https://console.x.ai/)
2. 注册/登录账户
3. 创建新的API密钥
4. 复制格式为 `xai-xxxxxxxxxxxxxxxxxxxxxxxx` 的密钥

### 2. 在StoryGenius中配置
1. 运行 `python run.py`
2. 选择 **"2. 配置AI提供商"**
3. 选择 **"8. Grok"**
4. 输入API密钥
5. 选择默认模型（推荐：`grok-beta`）

### 3. 使用Grok进行创作
1. 在主界面选择AI提供商：**"Grok"**
2. 选择合适的模型
3. 开始创作小说

## 🤖 模型选择指南

### 基础文本生成
- **grok-3-mini**: 最新轻量级模型，性价比最高（推荐）
- **grok-3**: 最新完整模型，性能强劲
- **grok-beta**: 适合标准小说创作，平衡性能和成本

### 多模态创作（如果需要图像理解）
- **grok-vision-beta**: 支持图像理解的多模态模型
- **grok-2-vision-1212**: 历史多模态版本

### 成本敏感用户
- **grok-3-mini**: 最新轻量级版本，成本最低（$0.0015/1K input tokens）
- **grok-3**: 新完整版本，性价比优秀（$0.002/1K input tokens）

## 💰 成本信息

| 模型 | 输入成本 ($/1K tokens) | 输出成本 ($/1K tokens) |
|------|----------------------|----------------------|
| grok-3-mini | $0.0015 | $0.0075 |
| grok-3 | $0.002 | $0.01 |
| grok-beta | $0.005 | $0.015 |
| grok-vision-beta | $0.01 | $0.03 |
| grok-2-1212 | $0.002 | $0.01 |
| grok-2-vision-1212 | $0.006 | $0.02 |

*注：以上价格仅为预估，实际价格请参考官方文档*

## 🔧 技术特性

### 1. API兼容性
- **OpenAI兼容**: 使用标准的OpenAI API格式
- **Base URL**: `https://api.x.ai/v1`
- **认证方式**: Bearer Token

### 2. 错误处理机制
```python
# 支持的错误码处理
- 400: 请求格式错误
- 401: API密钥无效  
- 402: 账户余额不足
- 403: 内容审核被拒绝（自动重试）
- 408: 请求超时（自动重试）
- 429: 请求频率限制（自动重试）
- 502: 服务器网关错误（自动重试）
- 503: 服务暂时不可用（自动重试）
```

### 3. 监控集成
- **Token使用追踪**: 实时监控输入/输出Token数量
- **成本计算**: 基于模型的精确成本估算
- **性能监控**: 响应时间和成功率统计
- **错误日志**: 详细的错误信息记录

## 📖 使用示例

### 基础API调用
```python
from config_manager import EnhancedConfigManager

# 初始化配置管理器
config_manager = EnhancedConfigManager()

# 切换到Grok提供商
config_manager.provider_manager.switch_provider('grok')

# 创建聊天完成
messages = [
    {"role": "user", "content": "写一个关于时间旅行的科幻小说开头"}
]

try:
    response = config_manager.create_completion_with_monitoring(
        messages=messages,
        model="grok-beta",
        max_tokens=1000,
        temperature=0.7
    )
    print("生成的内容:", response)
except Exception as e:
    print(f"错误: {e}")
```

### 小说创作流程
```python
from write_story_enhanced import StoryWriter

# 创建小说写作器
writer = StoryWriter()

# 切换到Grok
writer.config_manager.provider_manager.switch_provider('grok')
writer.current_model = "grok-beta"

# 生成小说大纲
outline = writer.generate_complete_outline(
    prompt="一个关于AI觉醒的科幻故事",
    num_chapters=10,
    writing_style="科幻，富有想象力，对话丰富"
)

print("大纲生成完成:", outline['title'])
```

## ⚠️ 注意事项

### 1. API密钥安全
- 请妥善保管您的API密钥
- 不要在代码中硬编码API密钥
- 定期检查API密钥的使用情况

### 2. 成本控制
- Grok的多模态模型成本较高，请根据需要选择
- 建议先用基础模型测试，确认效果后再选择高级模型
- 利用监控功能实时追踪成本

### 3. 内容审核
- Grok有内容审核机制，某些内容可能被拒绝
- 系统会自动重试，但如果持续被拒绝请调整内容
- 避免包含可能违规的内容

### 4. 请求频率
- 注意API的频率限制
- 系统会自动处理429错误并重试
- 如频繁遇到频率限制，可适当降低并发请求

## 🆚 与其他提供商的对比

| 特性 | Grok | DeepSeek | Claude | OpenRouter |
|------|------|----------|--------|------------|
| 成本 | 中等 | 低 | 高 | 中等 |
| 中文支持 | 良好 | 优秀 | 良好 | 中等 |
| 创意能力 | 优秀 | 良好 | 优秀 | 中等 |
| 幽默风格 | 优秀 | 中等 | 良好 | 中等 |
| 多模态 | 支持 | 不支持 | 支持 | 部分支持 |
| 实时信息 | 优秀 | 不支持 | 不支持 | 中等 |

## 🚀 最佳实践

### 1. 模型选择策略
- **日常创作**: 推荐使用 `grok-3-mini`（性价比最高）
- **高质量创作**: 使用 `grok-3`（最新完整版）
- **成本敏感**: 优先选择 `grok-3-mini`（成本最低）
- **需要图像**: 选择 `grok-vision-beta`
- **传统稳定**: 可以使用 `grok-beta`

### 2. 提示词优化
- Grok擅长幽默和创意写作，可以在提示词中明确要求
- 利用其实时信息能力，可以要求加入最新的科技元素
- 明确指定写作风格和语调，Grok能很好地适应

### 3. 错误处理
- 利用系统的自动重试机制，无需手动处理大部分错误
- 如遇到持续的403错误，检查内容是否符合使用政策
- 监控成本使用，避免意外的高额费用

## 🔄 版本更新

### v2.1.0 (2025-01-10)
- ✅ 添加完整的Grok API支持
- ✅ 实现智能错误处理和重试机制
- ✅ 集成成本监控和性能追踪
- ✅ 更新UI界面和文档

## 📞 支持与反馈

如果在使用Grok API过程中遇到问题：

1. **检查配置**: 确认API密钥正确设置
2. **查看日志**: 检查错误日志获取详细信息
3. **参考文档**: 查阅 [x.ai官方文档](https://docs.x.ai/docs/api-reference)
4. **社区支持**: 在项目GitHub页面提交Issue

---

**StoryGenius团队**  
*让AI创作更简单、更智能、更有趣*