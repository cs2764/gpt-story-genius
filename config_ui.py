import gradio as gr
import json
import time
from typing import Dict, List, Tuple, Any
from config_manager import EnhancedConfigManager
from providers import ProviderConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigUI:
    """配置界面类"""
    
    def __init__(self):
        self.config_manager = EnhancedConfigManager()
        self.provider_names = {
            'deepseek': 'DeepSeek',
            'alicloud': '阿里云通义千问',
            'zhipu': '智谱AI GLM',
            'gemini': 'Google Gemini',
            'openrouter': 'OpenRouter',
            'lmstudio': 'LM Studio',
            'claude': 'Claude',
            'grok': 'Grok'
        }
    
    def create_provider_config_tab(self) -> gr.Tab:
        """创建提供商配置选项卡"""
        with gr.Tab("🔧 AI提供商配置") as tab:
            gr.Markdown("## AI提供商配置管理")
            
            with gr.Row():
                with gr.Column(scale=1):
                    # 提供商选择
                    provider_dropdown = gr.Dropdown(
                        choices=list(self.provider_names.values()),
                        value=self.provider_names.get(self.config_manager.provider_manager.get_current_provider_name(), 'DeepSeek'),
                        label="选择AI提供商",
                        interactive=True
                    )
                    
                    # 当前提供商状态
                    current_provider_info = gr.Textbox(
                        label="当前提供商",
                        value=self.get_current_provider_info(),
                        interactive=False
                    )
                    
                    # 刷新按钮
                    refresh_btn = gr.Button("🔄 刷新状态", variant="secondary")
                
                with gr.Column(scale=2):
                    # API密钥输入
                    api_key_input = gr.Textbox(
                        label="API密钥",
                        placeholder="请输入API密钥",
                        type="password",
                        interactive=True
                    )
                    
                    # Base URL输入
                    base_url_input = gr.Textbox(
                        label="Base URL (可选)",
                        placeholder="留空使用默认URL",
                        interactive=True
                    )
                    
                    # 系统提示词
                    system_prompt_input = gr.Textbox(
                        label="系统提示词 (可选)",
                        placeholder="自定义系统提示词",
                        lines=3,
                        interactive=True
                    )
                    
                    # 配置按钮
                    with gr.Row():
                        save_config_btn = gr.Button("💾 保存配置", variant="primary")
                        test_connection_btn = gr.Button("🔗 测试连接", variant="secondary")
            
            # 模型选择区域
            with gr.Row():
                with gr.Column():
                    available_models = gr.Dropdown(
                        label="可用模型",
                        choices=[],
                        multiselect=False,
                        interactive=True
                    )
                    
                    refresh_models_btn = gr.Button("🔄 刷新模型列表")
                
                with gr.Column():
                    default_model_dropdown = gr.Dropdown(
                        label="默认模型",
                        choices=[],
                        multiselect=False,
                        interactive=True
                    )
                    
                    set_default_model_btn = gr.Button("🔧 设置为默认模型", variant="secondary")
                    
                    model_info = gr.Textbox(
                        label="模型信息",
                        value="",
                        interactive=False,
                        lines=3
                    )
            
            # 状态显示区域
            with gr.Row():
                connection_status = gr.Textbox(
                    label="连接状态",
                    value="",
                    interactive=False
                )
                
                config_status = gr.Textbox(
                    label="配置状态",
                    value="",
                    interactive=False
                )
            
            # 事件处理
            def on_provider_change(provider_display_name):
                """提供商变更事件"""
                provider_key = self.get_provider_key(provider_display_name)
                if provider_key:
                    provider = self.config_manager.provider_manager.get_provider(provider_key)
                    models = self.get_models_for_provider(provider_key)
                    default_model = provider.config.default_model or (models[0] if models else "")
                    return (
                        provider.config.api_key or "",
                        provider.config.base_url or "",
                        provider.config.system_prompt or "",
                        models,
                        default_model,
                        f"当前选择: {provider_display_name}\n默认模型: {default_model or '未设置'}"
                    )
                return "", "", "", [], "", ""
            
            def on_save_config(provider_display_name, api_key, base_url, system_prompt):
                """保存配置事件"""
                try:
                    provider_key = self.get_provider_key(provider_display_name)
                    if provider_key:
                        self.config_manager.provider_manager.update_provider_config(
                            provider_key,
                            api_key=api_key,
                            base_url=base_url,
                            system_prompt=system_prompt
                        )
                        return "✅ 配置已保存"
                    return "❌ 未知的提供商"
                except Exception as e:
                    return f"❌ 保存失败: {str(e)}"
            
            def on_test_connection(provider_display_name):
                """测试连接事件"""
                try:
                    provider_key = self.get_provider_key(provider_display_name)
                    if provider_key:
                        provider = self.config_manager.provider_manager.get_provider(provider_key)
                        if provider.test_connection():
                            return "✅ 连接成功"
                        else:
                            return "❌ 连接失败"
                    return "❌ 未知的提供商"
                except Exception as e:
                    return f"❌ 测试失败: {str(e)}"
            
            def on_refresh_models(provider_display_name):
                """刷新模型列表"""
                provider_key = self.get_provider_key(provider_display_name)
                if provider_key:
                    models = self.get_models_for_provider(provider_key)
                    return gr.update(choices=models), gr.update(choices=models)
                return gr.update(choices=[]), gr.update(choices=[])
            
            def on_set_default_model(provider_display_name, selected_model):
                """设置默认模型"""
                try:
                    provider_key = self.get_provider_key(provider_display_name)
                    if provider_key and selected_model:
                        self.config_manager.provider_manager.set_default_model(provider_key, selected_model)
                        return f"✅ 已设置 {selected_model} 为默认模型"
                    return "❌ 请选择一个模型"
                except Exception as e:
                    return f"❌ 设置失败: {str(e)}"
            
            # 绑定事件
            provider_dropdown.change(
                on_provider_change,
                inputs=[provider_dropdown],
                outputs=[api_key_input, base_url_input, system_prompt_input, available_models, default_model_dropdown, current_provider_info]
            )
            
            save_config_btn.click(
                on_save_config,
                inputs=[provider_dropdown, api_key_input, base_url_input, system_prompt_input],
                outputs=[config_status]
            )
            
            test_connection_btn.click(
                on_test_connection,
                inputs=[provider_dropdown],
                outputs=[connection_status]
            )
            
            
            refresh_models_btn.click(
                on_refresh_models,
                inputs=[provider_dropdown],
                outputs=[available_models, default_model_dropdown]
            )
            
            set_default_model_btn.click(
                on_set_default_model,
                inputs=[provider_dropdown, default_model_dropdown],
                outputs=[config_status]
            )
            
            refresh_btn.click(
                lambda: self.get_current_provider_info(),
                outputs=[current_provider_info]
            )
        
        return tab
    
    def create_monitoring_tab(self) -> gr.Tab:
        """创建监控选项卡"""
        with gr.Tab("📊 监控与调试") as tab:
            gr.Markdown("## API调用监控与调试")
            
            with gr.Row():
                with gr.Column():
                    # 时间范围选择
                    time_range = gr.Dropdown(
                        choices=["1小时", "6小时", "24小时", "7天"],
                        value="24小时",
                        label="时间范围"
                    )
                    
                    refresh_monitoring_btn = gr.Button("🔄 刷新监控数据")
                
                with gr.Column():
                    # 监控开关
                    enable_monitoring = gr.Checkbox(
                        label="启用监控",
                        value=self.config_manager.system_config.enable_monitoring
                    )
                    
                    enable_cost_tracking = gr.Checkbox(
                        label="启用成本追踪",
                        value=self.config_manager.system_config.enable_cost_tracking
                    )
            
            # 监控摘要
            with gr.Row():
                with gr.Column():
                    total_calls = gr.Number(
                        label="总调用次数",
                        value=0,
                        interactive=False
                    )
                    
                    success_rate = gr.Number(
                        label="成功率 (%)",
                        value=0,
                        interactive=False
                    )
                
                with gr.Column():
                    total_cost = gr.Number(
                        label="总成本 ($)",
                        value=0,
                        interactive=False
                    )
                    
                    avg_response_time = gr.Number(
                        label="平均响应时间 (秒)",
                        value=0,
                        interactive=False
                    )
            
            # 提供商统计
            provider_stats = gr.Dataframe(
                headers=["提供商", "调用次数", "成功率", "成本", "平均响应时间"],
                datatype=["str", "number", "number", "number", "number"],
                label="提供商统计"
            )
            
            # 调试信息
            debug_info = gr.JSON(
                label="调试信息",
                value={}
            )
            
            def update_monitoring_data(time_range_str):
                """更新监控数据"""
                try:
                    hours_map = {"1小时": 1, "6小时": 6, "24小时": 24, "7天": 168}
                    hours = hours_map.get(time_range_str, 24)
                    
                    summary = self.config_manager.get_monitoring_summary(hours)
                    
                    # 计算成功率
                    success_rate_val = 0
                    if summary['total_calls'] > 0:
                        success_rate_val = (summary['successful_calls'] / summary['total_calls']) * 100
                    
                    # 提供商统计表格
                    provider_data = []
                    for provider, stats in summary['provider_stats'].items():
                        provider_success_rate = 0
                        if stats['calls'] > 0:
                            provider_success_rate = (stats['successful'] / stats['calls']) * 100
                        
                        provider_data.append([
                            self.provider_names.get(provider, provider),
                            stats['calls'],
                            round(provider_success_rate, 2),
                            round(stats['cost'], 4),
                            round(stats['avg_response_time'], 3)
                        ])
                    
                    # 调试信息
                    debug_data = self.config_manager.get_debug_info()
                    
                    return (
                        summary['total_calls'],
                        round(success_rate_val, 2),
                        round(summary['total_cost'], 4),
                        round(summary['average_response_time'], 3),
                        provider_data,
                        debug_data
                    )
                except Exception as e:
                    logger.error(f"更新监控数据失败: {e}")
                    return 0, 0, 0, 0, [], {"error": str(e)}
            
            def update_system_config(monitoring_enabled, cost_tracking_enabled):
                """更新系统配置"""
                try:
                    self.config_manager.system_config.enable_monitoring = monitoring_enabled
                    self.config_manager.system_config.enable_cost_tracking = cost_tracking_enabled
                    self.config_manager.save_system_config()
                    return "✅ 系统配置已保存"
                except Exception as e:
                    return f"❌ 保存失败: {str(e)}"
            
            # 绑定事件
            refresh_monitoring_btn.click(
                update_monitoring_data,
                inputs=[time_range],
                outputs=[total_calls, success_rate, total_cost, avg_response_time, provider_stats, debug_info]
            )
            
            time_range.change(
                update_monitoring_data,
                inputs=[time_range],
                outputs=[total_calls, success_rate, total_cost, avg_response_time, provider_stats, debug_info]
            )
            
            enable_monitoring.change(
                update_system_config,
                inputs=[enable_monitoring, enable_cost_tracking],
                outputs=[]
            )
            
            enable_cost_tracking.change(
                update_system_config,
                inputs=[enable_monitoring, enable_cost_tracking],
                outputs=[]
            )
        
        return tab
    
    def create_default_ideas_tab(self) -> gr.Tab:
        """创建默认提示词设定选项卡"""
        with gr.Tab("📝 默认提示词设定") as tab:
            gr.Markdown("## 默认提示词设定界面")
            
            # 启用开关
            enable_default_ideas = gr.Checkbox(
                label="启用自定义默认提示词",
                value=self.config_manager.default_ideas_config.enabled
            )
            
            # 配置输入
            with gr.Column():
                default_idea_input = gr.Textbox(
                    label="默认小说提示词",
                    placeholder="输入默认的小说提示词...",
                    lines=3,
                    value=self.config_manager.default_ideas_config.default_idea,
                    interactive=True
                )
                
                default_writing_style = gr.Textbox(
                    label="默认写作风格",
                    placeholder="输入默认的AI写作风格...",
                    lines=3,
                    value=self.config_manager.default_ideas_config.default_writing_style,
                    interactive=True
                )
            
            # 操作按钮
            with gr.Row():
                save_ideas_btn = gr.Button("💾 保存配置", variant="primary")
                reset_ideas_btn = gr.Button("🔄 重置配置", variant="secondary")
            
            # 状态显示
            ideas_status = gr.Textbox(
                label="配置状态",
                value="",
                interactive=False
            )
            
            def save_default_ideas(enabled, idea, writing_style):
                """保存默认提示词配置"""
                try:
                    self.config_manager.default_ideas_config.enabled = enabled
                    self.config_manager.default_ideas_config.default_idea = idea
                    self.config_manager.default_ideas_config.default_writing_style = writing_style
                    self.config_manager.save_default_ideas_config()
                    return "✅ 默认提示词配置已保存"
                except Exception as e:
                    return f"❌ 保存失败: {str(e)}"
            
            def reset_default_ideas():
                """重置默认提示词配置"""
                try:
                    self.config_manager.default_ideas_config.enabled = False
                    self.config_manager.default_ideas_config.default_idea = ""
                    self.config_manager.default_ideas_config.default_writing_style = ""
                    self.config_manager.save_default_ideas_config()
                    return (
                        False, "", "",
                        "✅ 默认提示词配置已重置"
                    )
                except Exception as e:
                    return (
                        False, "", "",
                        f"❌ 重置失败: {str(e)}"
                    )
            
            # 绑定事件
            save_ideas_btn.click(
                save_default_ideas,
                inputs=[enable_default_ideas, default_idea_input, default_writing_style],
                outputs=[ideas_status]
            )
            
            reset_ideas_btn.click(
                reset_default_ideas,
                outputs=[enable_default_ideas, default_idea_input, default_writing_style, ideas_status]
            )
        
        return tab
    
    def create_openrouter_tab(self) -> gr.Tab:
        """创建OpenRouter深度集成选项卡"""
        with gr.Tab("🌐 OpenRouter深度集成") as tab:
            gr.Markdown("## OpenRouter模型管理")
            gr.Markdown("**注意：** 模型列表已过滤，只显示 OpenAI、Google、DeepSeek、Qwen 和 Grok 的主要模型")
            
            with gr.Row():
                with gr.Column():
                    # 提供商过滤
                    provider_filter = gr.Dropdown(
                        choices=["全部", "OpenAI", "Google", "Qwen", "DeepSeek", "Grok", "Anthropic"],
                        value="全部",
                        label="按提供商过滤"
                    )
                    
                    refresh_openrouter_btn = gr.Button("🔄 刷新OpenRouter模型")
                
                with gr.Column():
                    # 模型搜索
                    model_search = gr.Textbox(
                        label="搜索模型",
                        placeholder="输入模型名称搜索...",
                        interactive=True
                    )
            
            # 模型列表
            openrouter_models = gr.Dataframe(
                headers=["模型ID", "提供商", "描述", "状态"],
                datatype=["str", "str", "str", "str"],
                label="OpenRouter模型列表"
            )
            
            # 模型详情
            model_details = gr.JSON(
                label="模型详情",
                value={}
            )
            
            def refresh_openrouter_models(provider_filter_val, search_term):
                """刷新OpenRouter模型列表"""
                try:
                    openrouter_provider = self.config_manager.provider_manager.get_provider('openrouter')
                    
                    # 获取过滤后的模型
                    if provider_filter_val == "全部":
                        models = openrouter_provider.get_models()
                    else:
                        models = openrouter_provider.filter_models_by_provider(provider_filter_val.lower())
                    
                    # 搜索过滤
                    if search_term:
                        models = [m for m in models if search_term.lower() in m.lower()]
                    
                    # 构建表格数据
                    model_data = []
                    for model in models[:50]:  # 限制显示数量
                        provider_name = "未知"
                        if "/" in model:
                            provider_name = model.split("/")[0]
                        elif any(prefix in model for prefix in ["gpt-", "o1-"]):
                            provider_name = "OpenAI"
                        elif "gemini" in model:
                            provider_name = "Google"
                        
                        model_data.append([
                            model,
                            provider_name,
                            f"模型: {model}",
                            "可用" if model else "不可用"
                        ])
                    
                    return model_data
                except Exception as e:
                    logger.error(f"刷新OpenRouter模型失败: {e}")
                    return []
            
            # 绑定事件
            refresh_openrouter_btn.click(
                refresh_openrouter_models,
                inputs=[provider_filter, model_search],
                outputs=[openrouter_models]
            )
            
            provider_filter.change(
                refresh_openrouter_models,
                inputs=[provider_filter, model_search],
                outputs=[openrouter_models]
            )
            
            model_search.change(
                refresh_openrouter_models,
                inputs=[provider_filter, model_search],
                outputs=[openrouter_models]
            )
        
        return tab
    
    def get_provider_key(self, display_name: str) -> str:
        """根据显示名称获取提供商键"""
        for key, name in self.provider_names.items():
            if name == display_name:
                return key
        return ""
    
    def get_current_provider_info(self) -> str:
        """获取当前提供商信息"""
        try:
            current_key = self.config_manager.provider_manager.get_current_provider_name()
            current_name = self.provider_names.get(current_key, current_key)
            provider = self.config_manager.provider_manager.get_provider(current_key)
            
            status = "✅ 已连接" if provider.test_connection() else "❌ 未连接"
            api_key_status = "✅ 已设置" if provider.config.api_key else "❌ 未设置"
            
            return f"当前: {current_name}\n连接状态: {status}\nAPI密钥: {api_key_status}"
        except Exception as e:
            return f"获取信息失败: {str(e)}"
    
    def get_models_for_provider(self, provider_key: str) -> List[str]:
        """获取提供商的模型列表"""
        try:
            return self.config_manager.provider_manager.get_models_for_provider(provider_key)
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []
    
    def create_config_interface(self) -> gr.Blocks:
        """创建配置界面"""
        with gr.Blocks(
            title="StoryGenius 配置管理",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px !important;
            }
            .tab-nav {
                font-size: 16px !important;
            }
            """
        ) as interface:
            gr.Markdown("# 🎛️ StoryGenius 配置管理中心")
            
            # 创建各个选项卡
            with gr.Tabs():
                self.create_provider_config_tab()
                self.create_monitoring_tab()
                self.create_default_ideas_tab()
                self.create_openrouter_tab()
                
                # 系统配置选项卡
                with gr.Tab("⚙️ 系统设置"):
                    gr.Markdown("## 系统配置")
                    
                    with gr.Row():
                        with gr.Column():
                            auto_save = gr.Checkbox(
                                label="自动保存配置",
                                value=self.config_manager.system_config.auto_save
                            )
                            
                            cache_models = gr.Checkbox(
                                label="缓存模型列表",
                                value=self.config_manager.system_config.cache_models
                            )
                            
                            debug_mode = gr.Checkbox(
                                label="调试模式",
                                value=self.config_manager.system_config.debug_mode
                            )
                        
                        with gr.Column():
                            max_retries = gr.Slider(
                                label="最大重试次数",
                                minimum=1,
                                maximum=10,
                                value=self.config_manager.system_config.max_retries,
                                step=1
                            )
                            
                            timeout = gr.Slider(
                                label="超时时间 (秒)",
                                minimum=10,
                                maximum=120,
                                value=self.config_manager.system_config.timeout,
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
                            self.config_manager.system_config.auto_save = auto_save_val
                            self.config_manager.system_config.cache_models = cache_models_val
                            self.config_manager.system_config.debug_mode = debug_mode_val
                            self.config_manager.system_config.max_retries = int(max_retries_val)
                            self.config_manager.system_config.timeout = int(timeout_val)
                            self.config_manager.save_system_config()
                            return "✅ 系统设置已保存"
                        except Exception as e:
                            return f"❌ 保存失败: {str(e)}"
                    
                    def export_config():
                        """导出配置"""
                        try:
                            export_path = f"config_backup_{int(time.time())}.json"
                            self.config_manager.export_config(export_path)
                            return f"✅ 配置已导出到: {export_path}"
                        except Exception as e:
                            return f"❌ 导出失败: {str(e)}"
                    
                    def import_config(file_path):
                        """导入配置"""
                        try:
                            if file_path:
                                self.config_manager.import_config(file_path)
                                return "✅ 配置已导入"
                            return "❌ 请选择配置文件"
                        except Exception as e:
                            return f"❌ 导入失败: {str(e)}"
                    
                    def reset_all_config():
                        """重置所有配置"""
                        try:
                            self.config_manager.reset_config()
                            return "✅ 所有配置已重置"
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
        
        return interface