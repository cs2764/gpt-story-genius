<h1 align="center">🎭 StoryGenius：AI智能小说创作平台</h1>

<p align="center">
    <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version">
    <img src="https://img.shields.io/badge/release-2025--01--08-green.svg" alt="Release Date">
    <img src="https://img.shields.io/badge/codename-Multi--AI%20Genesis-purple.svg" alt="Codename">
    <img src="https://img.shields.io/badge/python-3.8%2B-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

> **项目声明**  
> 本项目是对 [https://github.com/Crossme0809/gpt-story-genius](https://github.com/Crossme0809/gpt-story-genius) 的二次开发  
> 🤖 所有代码以及文档均由 Claude Code 生成

<p align="center">
    <br>
    <b>StoryGenius：多AI提供商智能小说创作平台</b><br><br>
    支持7个AI提供商，根据小说的提示词、写作风格和章节数量快速生成奇幻小说。<br>
    具备实时进度显示、成本监控、配置管理等企业级功能。<br>
</p>
<br>

![poster](https://github.com/Crossme0809/frenzy_repo/blob/main/assets/story_genius.png)
<br>


**gpt-story-genius** 是一个自动创作小说的AI，它可以在几分钟内根据用户提供的初始提示和章节数生成一整本奇幻小说，并自动打包为电子书格式。
该项目利用 **GPT-4**、**Stable Diffusion API** 和 **Anthropic API** 等一系列大模型调用组成的链来生成原创奇幻小说。<br>

此外，它还可以根据这本书创建一个原创封面，并将整本作品一次性转换为PDF或电子书格式，并且`制作成本低廉，制作一本15章的小说仅需4美元成本`，并且该工具是开源的，可以免费使用。
<br>

## 📈 版本历史

### 🎉 v2.0.0 "Multi-AI Genesis" (2025-01-08)

**重大更新** - 从单一AI提供商升级为多AI提供商智能创作平台

#### ✨ 新增功能
- 🤖 **多AI提供商支持**：支持7个主流AI提供商（DeepSeek、阿里云通义千问、智谱AI GLM、Google Gemini、OpenRouter、LM Studio、Claude）
- 📊 **实时监控系统**：API调用监控、成本追踪、性能统计
- ⚙️ **智能配置管理**：Web界面配置、API密钥验证、配置导入导出
- 🎯 **默认模型选择**：每个AI提供商可设置默认模型，自动选择最优模型
- 🌐 **OpenRouter深度集成**：400+开源和商业模型支持，智能模型筛选
- 🚀 **跨平台启动方案**：Windows/macOS/Linux统一启动脚本
- 🔄 **虚拟环境优化**：从conda环境迁移到项目本地venv

#### 🔧 技术改进
- 💡 **API调用优化**：5秒超时、智能重试、错误处理
- 🎯 **系统提示词架构**：用户提示词前置，保持默认系统提示词
- 📱 **响应式界面**：现代化Gradio界面，实时状态显示
- 🛡️ **安全性增强**：API密钥本地存储，配置隔离
- 🏗️ **代码重构**：模块化设计，提升可维护性

#### 📋 完整更新日志
- [虚拟环境架构更新](./README_VENV_UPDATE.md)
- [API调用问题修复](./API_FIXES.md)
- [AI提供商设置优化](./AI_PROVIDER_OPTIMIZATION.md)
- [升级完成总结](./UPGRADE_SUMMARY.md)

### 📚 开发文档

#### 🔗 技术文档链接
- [📋 升级完成总结](./UPGRADE_SUMMARY.md) - 完整的升级功能概述
- [🔄 虚拟环境架构更新](./README_VENV_UPDATE.md) - 从conda到venv的迁移指南
- [🛠️ API调用问题修复](./API_FIXES.md) - LM Studio和OpenRouter问题解决
- [⚙️ AI提供商设置优化](./AI_PROVIDER_OPTIMIZATION.md) - 配置管理系统优化

#### 🎯 核心架构
- **提供商管理**: `providers.py` - 统一AI提供商接口
- **配置管理**: `config_manager.py` - 增强配置管理系统
- **界面组件**: `config_ui.py` - 配置界面组件
- **创作引擎**: `write_story_enhanced.py` - 增强小说创作引擎
- **启动管理**: `start.py` - 跨平台启动器

#### 🧪 测试与验证
- **功能测试**: `test_basic_functionality.py` - 基本功能验证
- **环境管理**: `manage_env.py` - 虚拟环境管理工具
- **性能监控**: 内置API调用监控和成本追踪

---

## 快速使用

在 Google Colab 中，只需打开笔记本，添加 API 密钥，然后按顺序运行单元即可。 </br></br>
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Crossme0809/frenzyTechAI/blob/main/gpt-author/gpt_author_v2.ipynb)

在笔记本的最后一个单元格中，您可以自定义小说的提示和章节数。例如：

```python
prompt = "一个被遗忘的小岛，上面有一座古老的灯塔。当灯塔亮起时，岛上的生物就会发生奇异的变化。"
num_chapters = 10
writing_style = "紧张刺激，类似于青少年恐怖小说。有很多对话和内心独白"
novel, title, chapters, chapter_titles = write_fantasy_novel(prompt, num_chapters, writing_style)
```

这将根据给定的提示生成一本 10 章的小说。**注意——少于 7 章的提示往往会导致问题。**

## 本地部署

### 🚀 一键启动 (推荐)

#### 下载项目代码
```bash
git clone https://github.com/cs2764/gpt-story-genius.git
cd gpt-story-genius
```

#### 方式1：使用统一启动器
```bash
# 安装依赖并启动
python start.py --install-deps

# 指定端口启动
python start.py --port 8080

# 启用公网分享
python start.py --share
```

#### 方式2：使用系统特定脚本

**Windows**
```batch
# 双击运行或在命令行执行
start_windows.bat
```

**macOS**
```bash
# 在终端执行
chmod +x start_macos.sh
./start_macos.sh
```

**Linux**
```bash
# 在终端执行
chmod +x start_linux.sh
./start_linux.sh
```

#### 方式3：手动启动
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate.bat  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动应用
python run.py
```

### ⚙️ 配置AI提供商

启动成功后，访问 **http://localhost:8091** 打开 **StoryGenius** 平台：

1. 进入「⚙️ 配置管理」页面
2. 在「🔧 AI提供商配置」中选择要使用的提供商
3. 输入对应的API密钥
4. 点击「🔗 测试连接」验证配置
5. **设置默认模型**：选择模型后点击「🔧 设置为默认模型」
6. 返回「📝 小说创作」页面开始创作（会自动选择设置的默认模型）

### 🔑 支持的AI提供商

| 提供商 | 获取API密钥 | 推荐模型 | 特点 |
|--------|-------------|----------|------|
| **DeepSeek** | [platform.deepseek.com](https://platform.deepseek.com/) | deepseek-chat, deepseek-reasoner | 性价比高，中文表现优秀 |
| **阿里云通义千问** | [dashscope.aliyun.com](https://dashscope.aliyun.com/) | qwen-max, qwen-plus | 国产模型，稳定可靠 |
| **智谱AI GLM** | [open.bigmodel.cn](https://open.bigmodel.cn/) | glm-4, glm-4-flash | 创意写作能力强 |
| **Google Gemini** | [ai.google.dev](https://ai.google.dev/) | gemini-pro, gemini-pro-vision | 多模态能力强 |
| **OpenRouter** | [openrouter.ai](https://openrouter.ai/) | 各种开源模型 | 模型选择丰富，支持400+模型 |
| **LM Studio** | [lmstudio.ai](https://lmstudio.ai/) | 本地模型 | 隐私安全，本地运行 |
| **Claude** | [console.anthropic.com](https://console.anthropic.com/) | claude-3-sonnet, claude-3-haiku | 长文本处理优秀 |
<br><br>
<p>生成完的小说Epub文可以下载其文件并在 https://www.fviewer.com/view-epub 上查看，或将其安装在 Kindle 等上。（Mac上直接预览）</p>

![poster](https://github.com/Crossme0809/frenzy_repo/blob/main/assets/novel_epub.png)

## 📋 系统要求

- **Python**: 3.8+ (推荐 3.9+)
- **操作系统**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **网络**: 稳定的网络连接访问AI服务
- **存储**: 至少500MB可用空间

## 🎯 使用建议

1. **首次使用**：请先到配置管理页面设置API密钥
2. **章节控制**：建议章节数控制在2-15章（成本考虑）
3. **模型选择**：根据需求选择合适的AI提供商和模型
4. **默认模型设置**：为每个提供商设置默认模型，提升使用体验
5. **成本控制**：使用监控功能跟踪API调用成本

## 🔧 故障排除

### 常见问题
- **连接失败**：检查API密钥和网络连接
- **生成中断**：查看错误信息，可能是配额不足
- **模型无法加载**：尝试刷新或更换提供商
- **端口占用**：使用`--port`参数指定其他端口

### 获取支持
- 查看 [开发文档](#-开发文档) 了解技术细节
- 检查 [版本历史](#-版本历史) 了解更新内容
- 提交 Issue 报告问题或建议

## 🤝 贡献

欢迎提交Pull Request和Issue，共同完善StoryGenius平台！

### 贡献指南
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 原项目：[gpt-author](https://github.com/mshumer/gpt-author) by [@mattshumer_](https://twitter.com/mattshumer_)
- 二次开发基础：[gpt-story-genius](https://github.com/Crossme0809/gpt-story-genius)
- 开发工具：所有代码均由 Claude Code 生成

## 📊 项目统计

- **版本**: 2.0.0 (Multi-AI Genesis)
- **发布日期**: 2025-01-08
- **开发周期**: 24小时
- **代码行数**: 6000+ 行
- **支持提供商**: 7个
- **总开发成本**: $26.26

---

<p align="center">
    <b>🎭 StoryGenius v2.0.0 - 让AI为您创作精彩小说！</b><br>
    Made with ❤️ by Claude Code
</p>

