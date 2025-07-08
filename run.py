
import gradio as gr
import logging
import os
import time
from config_manager import EnhancedConfigManager
from config_ui import ConfigUI
from version import get_version, get_version_info

# Try to import optional dependencies
try:
    from write_story_enhanced import write_fantasy_novel, StoryWriter
    from author import create_cover_image, create_epub
    HAS_STORY_WRITER = True
except ImportError as e:
    print(f"⚠️ Story writer dependencies not available: {e}")
    HAS_STORY_WRITER = False
    
    # Create dummy functions for missing dependencies
    def write_fantasy_novel(*args, **kwargs):
        raise gr.Error("Story writer dependencies not installed. Please install required packages.")
    
    def create_cover_image(*args, **kwargs):
        return ""
    
    def create_epub(*args, **kwargs):
        return ""
    
    class StoryWriter:
        def write_fantasy_novel(self, *args, **kwargs):
            raise gr.Error("Story writer dependencies not installed. Please install required packages.")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化配置管理器
config_manager = EnhancedConfigManager()
config_ui = ConfigUI()

# 检查是否有可用的提供商
def check_providers():
    """检查提供商配置"""
    status = config_manager.provider_manager.get_provider_status()
    available_providers = [name for name, data in status.items() if data.get('api_key_set', False)]
    return len(available_providers) > 0


def generate_novel(prompt, num_chapters, writing_style, provider_name, model_name):
    # 调用GPT和Claude API，生成小说结果
    # prompt = "A kingdom hidden deep in the forest, where every tree is a portal to another world."
    # num_chapters = 2
    # writing_style = "Clear and easily understandable, similar to a young adult novel. Lots of dialogue."
    # model_name = "gpt-3.5-turbo-16k"
    if not prompt or not writing_style:
        raise gr.Error("提示词和写作风格是必填项")
    if num_chapters < 1:
        raise gr.Error("章节数必须大于等于1")
    
    # 检查提供商配置
    if not check_providers():
        raise gr.Error("请先在配置页面设置至少一个AI提供商的API密钥")

    num_chapters = int(num_chapters)
    
    # 转换提供商显示名称为内部键
    provider_map = {
        'DeepSeek': 'deepseek',
        '阿里云通义千问': 'alicloud', 
        '智谱AI GLM': 'zhipu',
        'Google Gemini': 'gemini',
        'OpenRouter': 'openrouter',
        'LM Studio': 'lmstudio',
        'Claude': 'claude'
    }
    provider_key = provider_map.get(provider_name, provider_name.lower())
    
    # 使用增强的小说创作器
    writer = StoryWriter()
    _, title, chapters, chapter_titles = writer.write_fantasy_novel(
        prompt, num_chapters, writing_style, provider_key, model_name
    )

    # 用chapter_titles中的正文取代章节说明
    for i, chapter in enumerate(chapters):
        chapter_number_and_title = list(chapter_titles[i].keys())[0]
        chapter_titles[i] = {chapter_number_and_title: chapter}

    # 暂时跳过封面生成（功能保留，以后完善）
    image_url = None
    print("封面生成功能已暂时禁用")

    # 生成小说 EPUB 文件（不使用封面）
    file_url = create_epub(title, 'AI', chapter_titles, cover_image_path=None)
    print(f"Novel URL: {file_url}")

    # novel, file_path = write_fantasy_novel(prompt, num_chapters, writing_style)
    return { "image_url": image_url, "file_url": file_url }


def generate_output_with_progress(prompt, num_chapters, writing_style, provider_name, model_name, progress=gr.Progress()):
    """带进度显示的小说生成函数"""
    try:
        # 验证输入
        if not prompt or not writing_style:
            raise gr.Error("提示词和写作风格是必填项")
        if num_chapters < 1:
            raise gr.Error("章节数必须大于等于1")
        
        # 检查提供商配置
        if not check_providers():
            raise gr.Error("请先在配置页面设置至少一个AI提供商的API密钥")

        num_chapters = int(num_chapters)
        
        # 转换提供商显示名称为内部键
        provider_map = {
            'DeepSeek': 'deepseek',
            '阿里云通义千问': 'alicloud', 
            '智谱AI GLM': 'zhipu',
            'Google Gemini': 'gemini',
            'OpenRouter': 'openrouter',
            'LM Studio': 'lmstudio',
            'Claude': 'claude'
        }
        provider_key = provider_map.get(provider_name, provider_name.lower())
        
        # 生成阶段进度计算
        total_steps = 5 + num_chapters  # 情节生成、选择、改进、标题、故事线 + 各章节
        current_step = 0
        current_words = 0
        
        # 定义进度回调函数
        def progress_callback(step_name, step_desc="", chapter_completed=None, chapter_content=""):
            nonlocal current_step, current_words
            current_step += 1
            if chapter_content:
                current_words += len(str(chapter_content))
            
            progress_percent = int((current_step / total_steps) * 100)
            progress(current_step / total_steps, desc=step_name)
            
            stats = {
                "已生成章节": chapter_completed if chapter_completed is not None else 0,
                "预计总章节": num_chapters,
                "生成进度": f"{progress_percent}%",
                "当前字数": current_words
            }
            
            log_msg = f"📝 {step_name}"
            if chapter_completed is not None:
                log_msg += f" - 已完成第{chapter_completed}章"
            
            return (step_name, step_desc, stats, "生成中...", log_msg, None, None)
        
        # 初始状态
        yield ("初始化中...", "准备开始生成", {"已生成章节": 0, "预计总章节": num_chapters, "生成进度": "0%", "当前字数": 0}, "开始生成", "🚀 开始创作小说", None, None)
        
        # 使用增强的小说创作器
        writer = StoryWriter()
        
        # 设置提供商和模型
        if provider_key:
            try:
                writer.config_manager.provider_manager.switch_provider(provider_key)
                logger.info(f"切换到提供商：{provider_key}")
            except Exception as e:
                logger.warning(f"切换提供商失败：{e}")
        
        if model_name:
            writer.current_model = model_name
            logger.info(f"设置使用模型：{model_name}")
        
        # 手动执行各个步骤并更新进度
        yield progress_callback("生成情节", "正在生成多个候选情节")
        plots = writer.generate_plots(prompt)
        
        yield progress_callback("选择最佳情节", "从候选情节中选择最优方案")
        best_plot = writer.select_most_engaging(plots)
        
        yield progress_callback("优化情节", "进一步完善和优化情节")
        improved_plot = writer.improve_plot(best_plot)
        
        yield progress_callback("生成标题", "为小说生成吸引人的标题")
        title = writer.get_title(improved_plot)
        
        yield progress_callback("生成故事线", "创建详细的章节大纲")
        storyline = writer.generate_storyline(improved_plot, num_chapters)
        
        # 解析章节标题
        import ast
        try:
            chapter_titles = ast.literal_eval(storyline)
        except Exception as e:
            logger.error(f"解析故事线失败: {e}")
            chapter_titles = [
                {f"Chapter {i+1} - 第{i+1}章": f"第{i+1}章内容"}
                for i in range(num_chapters)
            ]
        
        # 创建章节列表
        chapters = []
        
        # 写第一章
        yield progress_callback("写作第一章", f"正在创作: {list(chapter_titles[0].keys())[0]}")
        first_chapter = writer.write_first_chapter(storyline, str(chapter_titles[0]), writing_style)
        chapters.append(first_chapter)
        yield progress_callback("第一章完成", "第一章创作完成", 1, first_chapter)
        
        # 写其余章节
        novel = f"故事线:\n{storyline}\n\n第一章:\n{first_chapter}\n"
        
        for i in range(num_chapters - 1):
            chapter_title = list(chapter_titles[i + 1].keys())[0]
            yield progress_callback(f"写作第{i+2}章", f"正在创作: {chapter_title}")
            
            chapter = writer.write_chapter(novel, storyline, str(chapter_titles[i + 1]))
            
            # 检查章节长度
            if len(str(chapter)) < 100:
                yield progress_callback(f"重写第{i+2}章", "章节长度不足，正在重新生成")
                chapter = writer.write_chapter(novel, storyline, str(chapter_titles[i + 1]))
            
            chapters.append(chapter)
            novel += f"第{i + 2}章:\n{chapter}\n"
            yield progress_callback(f"第{i+2}章完成", f"第{i+2}章创作完成", i+2, chapter)

        # 用chapter_titles中的正文取代章节说明
        for i, chapter in enumerate(chapters):
            chapter_number_and_title = list(chapter_titles[i].keys())[0]
            chapter_titles[i] = {chapter_number_and_title: chapter}

        # 生成EPUB文件
        yield progress_callback("生成EPUB文件", "正在创建电子书文件")
        file_url = create_epub(title, 'AI', chapter_titles, cover_image_path=None)
        
        # 获取成本信息
        summary = config_manager.get_monitoring_summary(1)  # 最近1小时
        cost_info = f"总成本: ${summary['total_cost']:.4f} | 调用次数: {summary['total_calls']}"
        
        # 完成
        total_words = sum(len(str(chapter)) for chapter in chapters)
        final_stats = {
            "已生成章节": len(chapters), 
            "预计总章节": num_chapters, 
            "生成进度": "100%", 
            "当前字数": total_words,
            "小说标题": title
        }
        
        final_log = f"✅ 小说《{title}》生成完成\n📚 共{len(chapters)}章，总字数：{total_words}字\n💰 成本：${summary['total_cost']:.4f}\n📖 EPUB文件已生成"
        
        yield ("生成完成!", "所有章节创作完成", final_stats, cost_info, final_log, None, file_url)
        
    except Exception as e:
        logger.error(f"生成小说时发生错误: {e}")
        error_msg = f"❌ 生成失败: {str(e)}"
        yield ("生成失败", "发生错误", {"已生成章节": 0, "预计总章节": 0, "生成进度": "错误", "当前字数": 0}, "生成失败", error_msg, None, None)
        raise gr.Error(str(e))

def generate_output(prompt, num_chapters, writing_style, provider_name, model_name):
    """兼容原版的生成函数"""
    try:
        output = generate_novel(prompt, num_chapters, writing_style, provider_name, model_name)
        return (output["image_url"], output["file_url"])
    except Exception as e:
        raise gr.Error(str(e))


def get_default_values():
    """获取默认值"""
    if config_manager.default_ideas_config.enabled:
        return (
            config_manager.default_ideas_config.default_idea or "一个被遗忘的小岛，上面有一座古老的灯塔。当灯塔亮起时，岛上的生物就会发生奇异的变化。",
            config_manager.default_ideas_config.default_writing_style or "紧张刺激，类似于青少年恐怖小说。有很多对话和内心独白"
        )
    return (
        "一个被遗忘的小岛，上面有一座古老的灯塔。当灯塔亮起时，岛上的生物就会发生奇异的变化。",
        "紧张刺激，类似于青少年恐怖小说。有很多对话和内心独白"
    )

def get_available_providers():
    """获取可用的提供商列表（只显示有API密钥的）"""
    provider_names = {
        'deepseek': 'DeepSeek',
        'alicloud': '阿里云通义千问',
        'zhipu': '智谱AI GLM',
        'gemini': 'Google Gemini',
        'openrouter': 'OpenRouter',
        'lmstudio': 'LM Studio',
        'claude': 'Claude'
    }
    
    # 获取提供商状态，只返回有API密钥的
    status = config_manager.provider_manager.get_provider_status()
    available_keys = [key for key, data in status.items() if data.get('api_key_set', False)]
    available_names = [provider_names[key] for key in available_keys if key in provider_names]
    
    # 如果没有可用提供商，返回所有提供商（用于初始化）
    if not available_names:
        available_names = list(provider_names.values())
    
    # 选择默认提供商
    current_provider = config_manager.provider_manager.get_current_provider_name()
    default_provider = provider_names.get(current_provider, 'DeepSeek')
    if default_provider not in available_names and available_names:
        default_provider = available_names[0]
    
    return available_names, default_provider

def get_models_for_current_provider():
    """获取当前提供商的模型列表"""
    try:
        current_provider = config_manager.provider_manager.get_current_provider_name()
        models = config_manager.provider_manager.get_models_for_provider(current_provider)
        return models if models else ["默认模型"]
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        return ["默认模型"]

default_idea, default_style = get_default_values()
available_providers, current_provider = get_available_providers()
available_models = get_models_for_current_provider()

version_info = get_version_info()
app_title = f"🎭 StoryGenius：AI智能小说创作平台 v{get_version()}"
app_description = f"""
### 🌟 欢迎使用StoryGenius AI小说创作平台

**版本**: {version_info['version']} ({version_info['codename']}) | **发布日期**: {version_info['release_date']}

支持7个AI提供商：**DeepSeek** | **阿里云** | **智谱AI** | **Google Gemini** | **OpenRouter** | **LM Studio** | **Claude**

📝 **功能特色：**
- 🤖 多AI提供商智能切换
- 📊 实时成本监控与性能追踪  
- 🎨 自动生成精美封面
- 📚 一键导出EPUB电子书
- ⚙️ 个性化配置管理

💡 **使用提示：** 首次使用请先到"配置管理"页面设置AI提供商的API密钥
"""


def update_models_dropdown(provider_name):
    """根据提供商更新模型下拉列表"""
    try:
        # 转换显示名称为键
        provider_map = {
            'DeepSeek': 'deepseek',
            '阿里云通义千问': 'alicloud', 
            '智谱AI GLM': 'zhipu',
            'Google Gemini': 'gemini',
            'OpenRouter': 'openrouter',
            'LM Studio': 'lmstudio',
            'Claude': 'claude'
        }
        
        provider_key = provider_map.get(provider_name)
        if provider_key:
            models = config_manager.provider_manager.get_models_for_provider(provider_key)
            if models:
                return gr.update(choices=models, value=models[0])
        
        return gr.update(choices=["默认模型"], value="默认模型")
    except Exception as e:
        logger.error(f"更新模型列表失败: {e}")
        return gr.update(choices=["默认模型"], value="默认模型")

def refresh_providers_and_status():
    """刷新提供商列表和状态"""
    try:
        available_providers, current_provider = get_available_providers()
        status_text = get_provider_status()
        
        # 获取第一个可用提供商的模型
        if available_providers:
            models = update_models_dropdown(available_providers[0])
            return (
                gr.update(choices=available_providers, value=current_provider if current_provider in available_providers else available_providers[0]),
                models,
                status_text
            )
        else:
            return (
                gr.update(choices=["请先配置提供商"], value="请先配置提供商"),
                gr.update(choices=["默认模型"], value="默认模型"),
                status_text
            )
    except Exception as e:
        logger.error(f"刷新提供商列表失败: {e}")
        return (
            gr.update(choices=["配置错误"], value="配置错误"),
            gr.update(choices=["默认模型"], value="默认模型"),
            "获取状态失败"
        )

def get_provider_status():
    """获取提供商状态"""
    try:
        status = config_manager.provider_manager.get_provider_status()
        status_text = "## 🔧 AI提供商状态\n\n"
        
        for provider, data in status.items():
            provider_names = {
                'deepseek': 'DeepSeek',
                'alicloud': '阿里云通义千问',
                'zhipu': '智谱AI GLM', 
                'gemini': 'Google Gemini',
                'openrouter': 'OpenRouter',
                'lmstudio': 'LM Studio',
                'claude': 'Claude'
            }
            
            name = provider_names.get(provider, provider)
            conn_status = "✅ 已连接" if data.get('connected', False) else "❌ 未连接"
            api_status = "✅ 已设置" if data.get('api_key_set', False) else "❌ 未设置"
            models_count = data.get('models_count', 0)
            
            status_text += f"**{name}:** {conn_status} | API密钥: {api_status} | 模型数: {models_count}\n\n"
        
        return status_text
    except Exception as e:
        return f"获取状态失败: {str(e)}"

# 创建主界面
with gr.Blocks(
    title=app_title,
    theme=gr.themes.Soft(),
    css="""
    .gradio-container {
        max-width: 1200px !important;
    }
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    """
) as app:
    gr.Markdown(f"# {app_title}")
    gr.Markdown(app_description)
    
    with gr.Tabs() as tabs:
        # 主创作界面
        with gr.Tab("📝 小说创作", id="main"):
            with gr.Row():
                with gr.Column(scale=2):
                    # 输入区域
                    prompt_input = gr.Textbox(
                        value=default_idea, 
                        lines=3, 
                        placeholder="请输入小说创意...", 
                        label="💡 小说提示词"
                    )
                    chapters_input = gr.Number(
                        value=2, 
                        minimum=1, 
                        maximum=500, 
                        label="📚 小说章节数"
                    )
                    style_input = gr.Textbox(
                        value=default_style, 
                        lines=3, 
                        placeholder="描述您想要的写作风格...", 
                        label="✍️ AI写作风格"
                    )
                    
                    with gr.Row():
                        provider_input = gr.Dropdown(
                            choices=available_providers,
                            value=current_provider,
                            label="🤖 选择AI提供商",
                            interactive=True
                        )
                        model_input = gr.Dropdown(
                            choices=available_models,
                            value=available_models[0] if available_models else "默认模型",
                            label="🎯 选择模型",
                            interactive=True
                        )
                    
                    # 提供商变更时更新模型列表
                    provider_input.change(
                        update_models_dropdown,
                        inputs=[provider_input],
                        outputs=[model_input]
                    )
                    
                    # 生成按钮
                    generate_btn = gr.Button(
                        "🚀 开始创作小说", 
                        variant="primary", 
                        size="lg"
                    )
                
                with gr.Column(scale=1):
                    # 状态显示
                    with gr.Group():
                        gr.Markdown("### 📊 系统状态")
                        status_display = gr.Markdown(
                            value=get_provider_status(),
                            every=10  # 每10秒更新
                        )
                        
                        refresh_status_btn = gr.Button(
                            "🔄 刷新提供商", 
                            variant="secondary"
                        )
            
            # 进度显示区域
            with gr.Row():
                with gr.Column(scale=1):
                    progress_bar = gr.Progress()
                    generation_status = gr.Textbox(
                        label="🔄 生成状态",
                        value="等待开始...",
                        interactive=False,
                        lines=2
                    )
                    
                    current_step = gr.Textbox(
                        label="📋 当前步骤",
                        value="未开始",
                        interactive=False
                    )
                
                with gr.Column(scale=1):
                    generation_stats = gr.JSON(
                        label="📊 生成统计",
                        value={"已生成章节": 0, "预计总章节": 0, "生成进度": "0%", "当前字数": 0}
                    )
                    
                    cost_info = gr.Textbox(
                        label="💰 成本信息",
                        value="暂无数据",
                        interactive=False
                    )
            
            # 实时日志显示
            with gr.Row():
                generation_log = gr.Textbox(
                    label="📝 生成日志",
                    value="",
                    interactive=False,
                    lines=6,
                    max_lines=10
                )
            
            # 输出区域
            with gr.Row():
                cover_output = gr.Image(label="📖 封面图片", width=1028, height=300)
                file_output = gr.File(label="📄 EPUB文件")
            
            # 绑定事件
            generate_btn.click(
                generate_output_with_progress,
                inputs=[prompt_input, chapters_input, style_input, provider_input, model_input],
                outputs=[generation_status, current_step, generation_stats, cost_info, generation_log, cover_output, file_output]
            )
            
            refresh_status_btn.click(
                refresh_providers_and_status,
                outputs=[provider_input, model_input, status_display]
            )
        
        # 配置管理界面
        with gr.Tab("⚙️ 配置管理", id="config"):
            gr.Markdown("# 🎛️ StoryGenius 配置管理中心")
            
            # 创建各个选项卡
            with gr.Tabs():
                config_ui.create_provider_config_tab()
                config_ui.create_monitoring_tab()
                config_ui.create_default_ideas_tab()
                config_ui.create_openrouter_tab()
                
                # 系统配置选项卡
                with gr.Tab("⚙️ 系统设置"):
                    gr.Markdown("## 系统配置")
                    
                    with gr.Row():
                        with gr.Column():
                            auto_save = gr.Checkbox(
                                label="自动保存配置",
                                value=config_manager.system_config.auto_save
                            )
                            
                            cache_models = gr.Checkbox(
                                label="缓存模型列表",
                                value=config_manager.system_config.cache_models
                            )
                            
                            debug_mode = gr.Checkbox(
                                label="调试模式",
                                value=config_manager.system_config.debug_mode
                            )
                        
                        with gr.Column():
                            max_retries = gr.Slider(
                                label="最大重试次数",
                                minimum=1,
                                maximum=10,
                                value=config_manager.system_config.max_retries,
                                step=1
                            )
                            
                            timeout = gr.Slider(
                                label="超时时间 (秒)",
                                minimum=10,
                                maximum=120,
                                value=config_manager.system_config.timeout,
                                step=5
                            )
                    
                    # 配置管理按钮
                    with gr.Row():
                        export_config_btn = gr.Button("📤 导出配置", variant="secondary")
                        import_config_btn = gr.Button("📥 导入配置", variant="secondary")
                        reset_all_btn = gr.Button("🔄 重置所有配置", variant="secondary")
                    
                    # 配置文件上传
                    config_file_upload = gr.File(
                        label="选择配置文件",
                        file_types=[".json"]
                    )
                    
                    system_status = gr.Textbox(
                        label="系统状态",
                        value="",
                        interactive=False
                    )
                    
                    def save_system_settings(auto_save_val, cache_models_val, debug_mode_val, max_retries_val, timeout_val):
                        """保存系统设置"""
                        try:
                            config_manager.system_config.auto_save = auto_save_val
                            config_manager.system_config.cache_models = cache_models_val
                            config_manager.system_config.debug_mode = debug_mode_val
                            config_manager.system_config.max_retries = int(max_retries_val)
                            config_manager.system_config.timeout = int(timeout_val)
                            config_manager.save_system_config()
                            return "✅ 系统设置已保存"
                        except Exception as e:
                            return f"❌ 保存失败: {str(e)}"
                    
                    def export_config():
                        """导出配置"""
                        try:
                            export_path = f"config_backup_{int(time.time())}.json"
                            config_manager.export_config(export_path)
                            return f"✅ 配置已导出到: {export_path}"
                        except Exception as e:
                            return f"❌ 导出失败: {str(e)}"
                    
                    def import_config(file_path):
                        """导入配置"""
                        try:
                            if file_path:
                                config_manager.import_config(file_path)
                                return "✅ 配置已导入"
                            return "❌ 请选择配置文件"
                        except Exception as e:
                            return f"❌ 导入失败: {str(e)}"
                    
                    def reset_all_config():
                        """重置所有配置"""
                        try:
                            config_manager.reset_config()
                            return "✅ 配置已重置"
                        except Exception as e:
                            return f"❌ 重置失败: {str(e)}"
                    
                    # 绑定事件
                    for component in [auto_save, cache_models, debug_mode, max_retries, timeout]:
                        component.change(
                            save_system_settings,
                            inputs=[auto_save, cache_models, debug_mode, max_retries, timeout],
                            outputs=[system_status]
                        )
                    
                    export_config_btn.click(
                        export_config,
                        outputs=[system_status]
                    )
                    
                    import_config_btn.click(
                        import_config,
                        inputs=[config_file_upload],
                        outputs=[system_status]
                    )
                    
                    reset_all_btn.click(
                        reset_all_config,
                        outputs=[system_status]
                    )
        
        # 使用说明
        with gr.Tab("📖 使用说明", id="help"):
            gr.Markdown("""
            # 📖 StoryGenius 使用指南
            
            ## 🚀 快速开始
            
            ### 1️⃣ 配置AI提供商
            - 前往 **"⚙️ 配置管理"** 页面
            - 选择您要使用的AI提供商
            - 输入对应的API密钥
            - 点击 **"测试连接"** 确认配置成功
            
            ### 2️⃣ 创作小说
            - 返回 **"📝 小说创作"** 页面
            - 输入您的小说创意
            - 设置章节数量（建议2-50章）
            - 描述写作风格
            - 选择AI提供商和模型
            - 点击 **"🚀 开始创作小说"**
            
            ## 🤖 支持的AI提供商
            
            | 提供商 | 特点 | 推荐模型 |
            |--------|------|----------|
            | **DeepSeek** | 性价比高，中文表现优秀 | deepseek-chat |
            | **阿里云** | 国产模型，稳定可靠 | qwen-max |
            | **智谱AI** | GLM系列，创意写作强 | glm-4 |
            | **Google Gemini** | 多模态能力强 | gemini-pro |
            | **OpenRouter** | 模型选择丰富 | 各种开源模型 |
            | **LM Studio** | 本地部署，隐私安全 | 本地模型 |
            | **Claude** | 长文本处理优秀 | claude-3-sonnet |
            
            ## 💡 创作技巧
            
            ### 提示词建议
            - 包含具体的设定、角色、冲突
            - 提供足够的背景信息
            - 可以指定题材：奇幻、科幻、悬疑等
            
            ### 写作风格描述
            - 明确文风：幽默、严肃、轻松等
            - 指定目标读者：青少年、成人等
            - 提及特殊要求：对话多、描述细腻等
            
            ## 📊 监控功能
            
            - **成本追踪**：实时显示API调用费用
            - **性能监控**：响应时间和成功率统计
            - **调用详情**：完整的API请求记录
            
            ## ⚠️ 注意事项
            
            - 首次使用需要配置API密钥
            - 建议章节数根据成本控制，长篇小说可能产生较高费用
            - 生成过程可能需要几分钟，请耐心等待
            - 支持配置导入/导出，便于备份
            
            ## 🔧 故障排除
            
            ### 常见问题
            1. **连接失败**：检查API密钥和网络连接
            2. **生成中断**：查看错误信息，可能是配额不足
            3. **模型无法加载**：尝试刷新或更换提供商
            
            ### 获取帮助
            - 查看调试信息："⚙️ 配置管理" → "📊 监控与调试" 
            - 导出配置备份："⚙️ 配置管理" → "⚙️ 系统设置"
            """)

# 启动应用
if __name__ == "__main__":
    import socket
    
    # 获取本机IP地址
    def get_local_ip():
        try:
            # 连接到外部地址以获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    # 查找可用端口
    def find_available_port(start_port=8091):
        """查找可用的端口"""
        for port in range(start_port, start_port + 100):  # 尝试100个端口
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        return None
    
    local_ip = get_local_ip()
    port = find_available_port()
    
    if port is None:
        print("❌ 无法找到可用端口，请手动指定端口")
        exit(1)
    
    print(f"\n🚀 StoryGenius 正在启动...")
    print(f"📍 本地访问: http://localhost:{port}")
    print(f"🌐 局域网访问: http://{local_ip}:{port}")
    print(f"⏹️  按 Ctrl+C 停止服务\n")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
        quiet=False,
        inbrowser=True  # 自动打开浏览器
    )