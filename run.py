
import gradio as gr
import logging
import os
import time
import datetime
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

def save_novel_to_output(title, chapters, chapter_titles, provider_name, model_name, total_words, novel_id):
    """保存完整小说到output文件夹"""
    try:
        # 创建output文件夹
        output_dir = os.path.join(os.getcwd(), "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"📁 创建输出目录: {output_dir}")
        
        # 生成文件名（使用时间戳避免重名）
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = title.replace(" ", "_").replace("/", "_").replace("\\", "_")
        filename = f"{safe_title}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # 构建完整小说内容
        novel_content = f"""
===============================================================================
                            {title}
===============================================================================

📚 小说信息:
• 标题: {title}
• 章节数: {len(chapters)}
• 总字数: {total_words:,}字
• 平均每章: {total_words//len(chapters):,}字
• 创作时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• AI提供商: {provider_name}
• 使用模型: {model_name}
• 小说ID: {novel_id}

===============================================================================
                                目录
===============================================================================

"""
        
        # 添加目录
        for i, chapter_title_dict in enumerate(chapter_titles):
            chapter_title = list(chapter_title_dict.keys())[0]
            novel_content += f"第{i+1}章: {chapter_title}\n"
        
        novel_content += "\n"
        
        # 添加章节内容
        for i, chapter in enumerate(chapters):
            chapter_title = list(chapter_titles[i].keys())[0]
            chapter_content = chapter
            
            novel_content += f"""
===============================================================================
                            {chapter_title}
===============================================================================

{chapter_content}

"""
        
        # 添加结尾信息
        novel_content += f"""
===============================================================================
                              创作完成
===============================================================================

📊 创作统计:
• 完成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• 总字数: {total_words:,}字
• 章节数: {len(chapters)}章
• AI提供商: {provider_name}
• 使用模型: {model_name}

感谢使用 StoryGenius AI 小说创作平台!
项目地址: https://github.com/Crossme0809/gpt-story-genius
"""
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(novel_content)
        
        logger.info(f"📄 小说已保存到: {filepath}")
        logger.info(f"📊 保存文件大小: {os.path.getsize(filepath)} 字节")
        
        # 创建章节文件夹并保存各章节
        chapters_dir = os.path.join(output_dir, f"{safe_title}_{timestamp}_chapters")
        os.makedirs(chapters_dir, exist_ok=True)
        
        chapter_files = []
        for i, chapter in enumerate(chapters):
            chapter_title = list(chapter_titles[i].keys())[0]
            safe_chapter_title = chapter_title.replace(" ", "_").replace("/", "_").replace("\\", "_")
            chapter_filename = f"第{i+1:02d}章_{safe_chapter_title}.txt"
            chapter_filepath = os.path.join(chapters_dir, chapter_filename)
            
            chapter_content = f"""
{chapter_title}

{chapter}

---
字数: {len(chapter)}字
创作时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            with open(chapter_filepath, 'w', encoding='utf-8') as f:
                f.write(chapter_content)
            
            chapter_files.append(chapter_filename)
        
        logger.info(f"📁 章节文件已保存到: {chapters_dir}")
        
        # 同时保存一个JSON元数据文件
        metadata_filename = f"{safe_title}_{timestamp}_metadata.json"
        metadata_filepath = os.path.join(output_dir, metadata_filename)
        
        import json
        metadata = {
            "title": title,
            "chapters": len(chapters),
            "total_words": total_words,
            "average_words_per_chapter": total_words // len(chapters),
            "created_time": datetime.datetime.now().isoformat(),
            "provider": provider_name,
            "model": model_name,
            "novel_id": novel_id,
            "chapter_titles": [list(ct.keys())[0] for ct in chapter_titles],
            "text_file": filename,
            "chapters_directory": f"{safe_title}_{timestamp}_chapters",
            "chapter_files": chapter_files,
            "generated_by": "StoryGenius AI",
            "version": get_version()
        }
        
        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📋 元数据已保存到: {metadata_filepath}")
        
        return filepath
        
    except Exception as e:
        logger.error(f"❌ 保存小说到输出文件夹失败: {e}")
        return None

def save_generation_process(generation_log, safe_title, timestamp):
    """保存生成过程到文件"""
    try:
        output_dir = os.path.join(os.getcwd(), "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存为Markdown格式
        md_filename = f"{safe_title}_{timestamp}_生成过程.md"
        md_filepath = os.path.join(output_dir, md_filename)
        
        # 构建Markdown内容
        md_content = f"""# 📝 小说生成过程记录

## 📊 基本信息
- **开始时间**: {generation_log['start_time']}
- **用户提示**: {generation_log['user_prompt']}
- **章节数**: {generation_log['num_chapters']}
- **写作风格**: {generation_log['writing_style']}
- **AI提供商**: {generation_log['provider']}
- **使用模型**: {generation_log['model']}

---

## 🎭 情节生成阶段

### 📝 候选情节
"""
        
        for i, plot in enumerate(generation_log['plots']):
            if plot.strip():
                md_content += f"{i+1}. {plot.strip()}\n\n"
        
        if generation_log['selected_plot']:
            md_content += f"""
### ✅ 选定情节
{generation_log['selected_plot']}

"""
        
        if generation_log['improved_plot']:
            md_content += f"""
### 🔄 优化后情节
{generation_log['improved_plot']}

"""
        
        if generation_log['title']:
            md_content += f"""
---

## 📖 小说标题
**{generation_log['title']}**

"""
        
        if generation_log['storyline']:
            md_content += f"""
---

## 📋 故事线
```json
{generation_log['storyline']}
```

"""
        
        # 章节生成过程
        if generation_log['chapters']:
            md_content += """
---

## 📚 章节生成过程

"""
            for chapter_info in generation_log['chapters']:
                md_content += f"""
### {chapter_info['title']}
- **生成时间**: {chapter_info['timestamp']}
- **字数**: {chapter_info['word_count']:,}字
- **Token消耗**: {chapter_info.get('tokens', 0):,}
- **生成时长**: {chapter_info.get('duration', 0):.2f}秒

"""
                if chapter_info.get('content_preview'):
                    md_content += f"""
**内容预览**:
{chapter_info['content_preview']}...

"""
        
        # 章节摘要
        if generation_log['summaries']:
            md_content += """
---

## 📄 章节摘要

"""
            for i, summary in enumerate(generation_log['summaries']):
                md_content += f"""
### 第{i+1}章摘要
{summary}

"""
        
        # 生成步骤记录
        if generation_log['steps']:
            md_content += """
---

## 🔄 详细步骤记录

"""
            for step in generation_log['steps']:
                md_content += f"""
### {step['step_name']}
- **时间**: {step['timestamp']}
- **描述**: {step.get('description', '')}
- **耗时**: {step.get('duration', 0):.2f}秒

"""
        
        md_content += f"""
---

## 📊 生成完成
- **完成时间**: {datetime.datetime.now().isoformat()}
- **总耗时**: {(datetime.datetime.now() - datetime.datetime.fromisoformat(generation_log['start_time'])).total_seconds():.2f}秒
- **生成工具**: StoryGenius AI v{get_version()}
"""
        
        # 保存文件
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"📋 生成过程已保存到: {md_filepath}")
        return md_filepath
        
    except Exception as e:
        logger.error(f"❌ 保存生成过程失败: {e}")
        return None

def update_generation_log(generation_log, step_name, **kwargs):
    """更新生成过程记录"""
    step_record = {
        "step_name": step_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "description": kwargs.get('description', ''),
        "duration": kwargs.get('duration', 0)
    }
    generation_log['steps'].append(step_record)
    
    # 根据步骤类型更新相应字段
    if 'plots' in kwargs:
        generation_log['plots'] = kwargs['plots']
    if 'selected_plot' in kwargs:
        generation_log['selected_plot'] = kwargs['selected_plot']
    if 'improved_plot' in kwargs:
        generation_log['improved_plot'] = kwargs['improved_plot']
    if 'title' in kwargs:
        generation_log['title'] = kwargs['title']
    if 'storyline' in kwargs:
        generation_log['storyline'] = kwargs['storyline']
    if 'chapter_info' in kwargs:
        generation_log['chapters'].append(kwargs['chapter_info'])
    if 'summary' in kwargs:
        generation_log['summaries'].append(kwargs['summary'])
    
    return generation_log


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
        'Claude': 'claude',
        'Grok': 'grok'
    }
    provider_key = provider_map.get(provider_name, provider_name.lower())
    
    # 使用增强的小说创作器
    writer = StoryWriter()
    _, title, chapters, chapter_titles, chapter_tokens_list = writer.write_fantasy_novel(
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


def generate_output_with_progress(prompt, num_chapters, writing_style, provider_name, model_name):
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
            'Claude': 'claude',
            'Grok': 'grok'
        }
        provider_key = provider_map.get(provider_name, provider_name.lower())
        
        # 生成阶段进度计算（增加摘要生成步骤和文件保存步骤）
        total_steps = 5 + num_chapters + (num_chapters - 1) + 2  # 情节生成、选择、改进、标题、故事线 + 各章节 + 摘要生成（除最后一章）+ EPUB生成 + 文本保存
        current_step = 0
        current_words = 0
        
        # 创建生成过程记录
        generation_log = {
            "start_time": datetime.datetime.now().isoformat(),
            "user_prompt": prompt,
            "num_chapters": num_chapters,
            "writing_style": writing_style,
            "provider": provider_name,
            "model": model_name,
            "steps": [],
            "plots": [],
            "selected_plot": "",
            "improved_plot": "",
            "title": "",
            "storyline": "",
            "chapters": [],
            "summaries": []
        }
        
        # 定义进度回调函数
        def progress_callback(step_name, step_desc="", chapter_completed=None, chapter_content="", token_info=None, generation_info=None):
            nonlocal current_step, current_words
            current_step += 1
            if chapter_content:
                current_words += len(str(chapter_content))
            
            progress_percent = int((current_step / total_steps) * 100)
            
            stats = {
                "已生成章节": chapter_completed if chapter_completed is not None else 0,
                "预计总章节": num_chapters,
                "生成进度": f"{progress_percent}%",
                "当前字数": current_words
            }
            
            # 构建详细的生成状态信息
            detailed_status = f"🔄 {step_name}\n\n"
            
            # 创建文字进度条
            progress_bar_length = 20
            filled_length = int(progress_bar_length * progress_percent / 100)
            progress_bar = "█" * filled_length + "░" * (progress_bar_length - filled_length)
            detailed_status += f"📊 总体进度: {progress_percent}% [{progress_bar}]\n"
            detailed_status += f"📈 步骤进度: {current_step}/{total_steps} 步骤\n"
            
            # 章节进度条
            if num_chapters > 0:
                chapter_progress_percent = int((chapter_completed if chapter_completed is not None else 0) / num_chapters * 100)
                chapter_filled = int(progress_bar_length * chapter_progress_percent / 100)
                chapter_progress_bar = "█" * chapter_filled + "░" * (progress_bar_length - chapter_filled)
                detailed_status += f"📚 章节进度: {chapter_progress_percent}% [{chapter_progress_bar}]\n"
                detailed_status += f"📖 章节状态: {chapter_completed if chapter_completed is not None else 0}/{num_chapters} 章\n"
            
            detailed_status += f"🔢 字数统计: {current_words:,}字\n"
            detailed_status += f"💡 当前步骤: {step_name}\n"
            
            if step_desc:
                detailed_status += f"📋 步骤描述: {step_desc}\n"
            
            if token_info:
                detailed_status += f"\n🔢 Token统计:\n"
                detailed_status += f"  • 输入Token: {token_info.get('input_tokens', 0):,}\n"
                detailed_status += f"  • 输出Token: {token_info.get('output_tokens', 0):,}\n"
                detailed_status += f"  • 总Token: {token_info.get('total_tokens', 0):,}\n"
            
            # 添加生成过程信息
            if generation_info:
                detailed_status += f"\n📋 生成信息:\n"
                if 'plots_count' in generation_info:
                    detailed_status += f"  • 候选情节数: {generation_info['plots_count']}\n"
                if 'title' in generation_info:
                    detailed_status += f"  • 小说标题: {generation_info['title']}\n"
                if 'storyline_ready' in generation_info:
                    detailed_status += f"  • 故事线: {'已生成' if generation_info['storyline_ready'] else '生成中'}\n"
            
            # 构建章节完成情况
            if chapter_completed is not None and chapter_completed > 0:
                chapter_info = f"📖 已完成章节: {chapter_completed}/{num_chapters}\n\n"
                chapter_info += f"✅ 第{chapter_completed}章创作完成\n"
                if chapter_content:
                    chapter_preview = str(chapter_content)[:200] + "..." if len(str(chapter_content)) > 200 else str(chapter_content)
                    chapter_info += f"📝 内容预览:\n{chapter_preview}\n\n"
                    chapter_info += f"📊 本章字数: {len(str(chapter_content))}字\n"
                
                if token_info:
                    chapter_info += f"🔢 本章Token消耗: {token_info.get('total_tokens', 0):,}\n"
                
                # 如果有多个章节，显示总体进度
                if chapter_completed > 1:
                    chapter_info += f"\n📈 总体进度: {(chapter_completed/num_chapters)*100:.1f}%"
            else:
                chapter_info = f"📖 准备开始章节创作...\n\n"
                chapter_info += f"📋 计划章节数: {num_chapters}\n"
                chapter_info += f"📝 当前阶段: {step_name}"
            
            # 简化的日志信息
            log_msg = f"📝 {step_name}"
            if chapter_completed is not None:
                log_msg += f" - 已完成第{chapter_completed}章"
                if token_info:
                    log_msg += f" (Token: {token_info.get('total_tokens', 0):,})"
            
            # 构建生成过程显示信息
            process_info = f"🔍 生成过程追踪\n\n"
            process_info += f"📊 当前步骤: {step_name}\n"
            process_info += f"⏰ 时间: {datetime.datetime.now().strftime('%H:%M:%S')}\n\n"
            
            if generation_log['plots']:
                process_info += f"🎭 候选情节: {len(generation_log['plots'])}个\n"
            if generation_log['selected_plot']:
                process_info += f"✅ 选定情节: {generation_log['selected_plot'][:50]}...\n"
            if generation_log['title']:
                process_info += f"📖 小说标题: {generation_log['title']}\n"
            if generation_log['chapters']:
                process_info += f"📚 已完成章节: {len(generation_log['chapters'])}/{num_chapters}\n"
            if generation_log['summaries']:
                process_info += f"📄 生成摘要: {len(generation_log['summaries'])}个\n"
            
            return (detailed_status, chapter_info, stats, log_msg, process_info, None, None)
        
        # 初始状态
        initial_detailed_status = f"🔄 初始化中...\n\n📊 当前进度: 0% (0/{total_steps})\n📚 章节状态: 0/{num_chapters}\n🔢 字数统计: 0字\n💡 当前步骤: 准备开始\n📋 步骤描述: 正在初始化小说创作系统"
        initial_chapter_info = f"📖 准备开始章节创作...\n\n📋 计划章节数: {num_chapters}\n📝 当前阶段: 系统初始化\n🎯 提供商: {provider_name}\n🤖 模型: {model_name}"
        initial_process_info = f"🔍 生成过程追踪\n\n📊 当前步骤: 初始化\n⏰ 时间: {datetime.datetime.now().strftime('%H:%M:%S')}\n\n📋 即将开始小说创作过程..."
        yield (initial_detailed_status, initial_chapter_info, {"已生成章节": 0, "预计总章节": num_chapters, "生成进度": "0%", "当前字数": 0}, "🚀 开始创作小说", initial_process_info, None, None)
        
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
        
        # 更新生成日志
        update_generation_log(generation_log, "生成情节", description="生成多个候选情节", plots=plots)
        logger.info(f"🎭 成功生成 {len(plots)} 个候选情节")
        
        yield progress_callback("选择最佳情节", "从候选情节中选择最优方案")
        best_plot = writer.select_most_engaging(plots)
        
        # 更新生成日志
        update_generation_log(generation_log, "选择最佳情节", description="从候选情节中选择最优方案", selected_plot=best_plot)
        logger.info(f"✅ 已选择最佳情节: {best_plot[:100]}...")
        
        yield progress_callback("优化情节", "进一步完善和优化情节")
        improved_plot = writer.improve_plot(best_plot)
        
        # 更新生成日志
        update_generation_log(generation_log, "优化情节", description="进一步完善和优化情节", improved_plot=improved_plot)
        logger.info(f"🔄 情节优化完成: {improved_plot[:100]}...")
        
        yield progress_callback("生成标题", "为小说生成吸引人的标题")
        title = writer.get_title(improved_plot)
        
        # 更新生成日志
        update_generation_log(generation_log, "生成标题", description="为小说生成吸引人的标题", title=title)
        logger.info(f"📖 小说标题已生成: {title}")
        
        yield progress_callback("生成故事线", "创建详细的章节大纲")
        storyline = writer.generate_storyline(improved_plot, num_chapters)
        
        # 更新生成日志
        update_generation_log(generation_log, "生成故事线", description="创建详细的章节大纲", storyline=storyline)
        logger.info(f"📋 故事线已生成: {len(storyline)} 字符")
        
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
        
        # 生成唯一的小说ID用于Token优化
        from config import generate_uuid
        novel_id = generate_uuid()
        
        # 写第一章
        yield progress_callback("写作第一章", f"正在创作: {list(chapter_titles[0].keys())[0]}")
        first_chapter_start_time = time.time()
        first_chapter, first_chapter_tokens = writer.write_first_chapter(storyline, str(chapter_titles[0]), writing_style)
        first_chapter_duration = time.time() - first_chapter_start_time
        chapters.append(first_chapter)
        
        # 保存第一章和摘要
        from config import save_novel_chapter, save_chapter_summary
        first_chapter_title = list(chapter_titles[0])[0]
        save_novel_chapter(novel_id, 0, first_chapter_title, first_chapter)
        first_chapter_summary = writer.summarize_chapter(first_chapter, first_chapter_title)
        save_chapter_summary(novel_id, 0, first_chapter_summary)
        
        # 更新生成日志
        chapter_info = {
            "title": first_chapter_title,
            "timestamp": datetime.datetime.now().isoformat(),
            "word_count": len(first_chapter),
            "tokens": first_chapter_tokens.get('total_tokens', 0),
            "duration": first_chapter_duration,
            "content_preview": first_chapter[:200]
        }
        update_generation_log(generation_log, "第一章完成", description="第一章创作完成", chapter_info=chapter_info, summary=first_chapter_summary)
        logger.info(f"📝 第一章《{first_chapter_title}》创作完成，字数: {len(first_chapter)}")
        
        yield progress_callback("第一章完成", "第一章创作完成", 1, first_chapter, first_chapter_tokens)
        
        # 写其余章节 - 使用Token优化
        for i in range(num_chapters - 1):
            current_chapter_index = i + 1
            chapter_title = list(chapter_titles[i + 1].keys())[0]
            yield progress_callback(f"写作第{i+2}章", f"正在创作: {chapter_title}")
            
            # 构建优化的上下文
            optimized_context = writer.build_optimized_context(novel_id, current_chapter_index, recent_chapters_count=2)
            
            chapter, chapter_tokens = writer.write_chapter(optimized_context, storyline, str(chapter_titles[i + 1]))
            
            # 检查章节长度
            if len(str(chapter)) < 100:
                yield progress_callback(f"重写第{i+2}章", "章节长度不足，正在重新生成")
                chapter, chapter_tokens = writer.write_chapter(optimized_context, storyline, str(chapter_titles[i + 1]))
            
            chapters.append(chapter)
            
            # 保存章节
            save_novel_chapter(novel_id, current_chapter_index, chapter_title, chapter)
            
            # 生成并保存摘要（除了最后一章）
            chapter_summary = None
            if current_chapter_index < num_chapters - 1:
                chapter_summary = writer.summarize_chapter(chapter, chapter_title)
                save_chapter_summary(novel_id, current_chapter_index, chapter_summary)
            
            # 更新生成日志
            chapter_info = {
                "title": chapter_title,
                "timestamp": datetime.datetime.now().isoformat(),
                "word_count": len(chapter),
                "tokens": chapter_tokens.get('total_tokens', 0),
                "duration": 0,  # 可以添加计时
                "content_preview": chapter[:200]
            }
            update_generation_log(generation_log, f"第{i+2}章完成", description=f"第{i+2}章创作完成", chapter_info=chapter_info, summary=chapter_summary)
            logger.info(f"📝 第{i+2}章《{chapter_title}》创作完成，字数: {len(chapter)}")
            
            yield progress_callback(f"第{i+2}章完成", f"第{i+2}章创作完成", i+2, chapter, chapter_tokens)

        # 用chapter_titles中的正文取代章节说明
        for i, chapter in enumerate(chapters):
            chapter_number_and_title = list(chapter_titles[i].keys())[0]
            chapter_titles[i] = {chapter_number_and_title: chapter}

        # 生成EPUB文件
        yield progress_callback("生成EPUB文件", "正在创建电子书文件")
        file_url = create_epub(title, 'AI', chapter_titles, cover_image_path=None)
        
        # 保存完整小说到output文件夹
        yield progress_callback("保存小说文件", "正在保存完整小说到output文件夹")
        total_words = sum(len(str(chapter)) for chapter in chapters)
        saved_filepath = save_novel_to_output(title, chapters, chapter_titles, provider_name, model_name, total_words, novel_id)
        
        # 保存生成过程文件
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = title.replace(" ", "_").replace("/", "_").replace("\\", "_")
        generation_log['end_time'] = datetime.datetime.now().isoformat()
        process_filepath = save_generation_process(generation_log, safe_title, timestamp)
        
        # 完成
        final_stats = {
            "已生成章节": len(chapters), 
            "预计总章节": num_chapters, 
            "生成进度": "100%", 
            "当前字数": total_words,
            "小说标题": title
        }
        
        # 更新最终状态信息，包含保存路径
        save_info = f"\n📁 文本文件: {saved_filepath}" if saved_filepath else "\n⚠️ 文本文件保存失败"
        process_info = f"\n📋 生成过程: {process_filepath}" if process_filepath else "\n⚠️ 生成过程保存失败"
        
        final_detailed_status = f"✅ 小说创作完成!\n\n📊 最终进度: 100% ({total_steps}/{total_steps})\n📚 章节状态: {len(chapters)}/{num_chapters} 全部完成\n🔢 总字数: {total_words:,}字\n💡 当前步骤: 创作完成\n📋 小说标题: {title}\n🎉 状态: 创作成功{save_info}{process_info}"
        
        final_chapter_info = f"📖 所有章节创作完成!\n\n✅ 成功完成: {len(chapters)}章\n📊 总字数: {total_words:,}字\n📚 平均每章: {total_words//len(chapters):,}字\n📖 EPUB文件已生成\n🎯 小说标题: {title}{save_info}{process_info}"
        
        final_log = f"✅ 小说《{title}》生成完成\n📚 共{len(chapters)}章，总字数：{total_words}字\n📖 EPUB文件已生成\n📁 文本文件已保存到output文件夹\n📋 生成过程已保存"
        
        final_process_info = f"🔍 生成过程完成\n\n📊 最终统计:\n• 候选情节: {len(generation_log['plots'])}个\n• 完成章节: {len(generation_log['chapters'])}/{num_chapters}\n• 生成摘要: {len(generation_log['summaries'])}个\n• 总步骤: {len(generation_log['steps'])}步\n• 创作时长: {(datetime.datetime.now() - datetime.datetime.fromisoformat(generation_log['start_time'])).total_seconds():.2f}秒\n\n📁 所有文件已保存到output文件夹"
        
        yield (final_detailed_status, final_chapter_info, final_stats, final_log, final_process_info, None, file_url)
        
    except Exception as e:
        logger.error(f"生成小说时发生错误: {e}")
        
        # 保存部分生成过程（如果有的话）
        if 'generation_log' in locals():
            try:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_title = generation_log.get('title', 'Failed_Novel').replace(" ", "_").replace("/", "_").replace("\\", "_")
                generation_log['end_time'] = datetime.datetime.now().isoformat()
                generation_log['error'] = str(e)
                save_generation_process(generation_log, f"{safe_title}_FAILED", timestamp)
                logger.info("📋 已保存部分生成过程到文件")
            except:
                logger.error("❌ 无法保存错误时的生成过程")
        
        error_detailed_status = f"❌ 生成失败!\n\n📊 进度状态: 错误\n📚 章节状态: 生成中断\n🔢 字数统计: {current_words:,}字\n💡 当前步骤: 发生错误\n📋 错误信息: {str(e)[:100]}...\n⚠️ 状态: 创作失败"
        error_chapter_info = f"❌ 创作过程中断!\n\n🚫 错误类型: 系统异常\n📝 错误详情: {str(e)[:150]}...\n🔄 建议: 请检查配置后重试"
        error_process_info = f"🔍 生成过程中断\n\n❌ 错误发生\n⏰ 时间: {datetime.datetime.now().strftime('%H:%M:%S')}\n🚫 错误信息: {str(e)[:100]}...\n\n📋 部分生成过程已保存到output文件夹"
        error_msg = f"❌ 生成失败: {str(e)}"
        yield (error_detailed_status, error_chapter_info, {"已生成章节": 0, "预计总章节": 0, "生成进度": "错误", "当前字数": 0}, error_msg, error_process_info, None, None)
        raise gr.Error(str(e))

def generate_outline_with_progress(prompt, num_chapters, writing_style, provider_name, model_name):
    """带进度显示的小说大纲生成函数"""
    try:
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
            'Claude': 'claude',
            'Grok': 'grok'
        }
        provider_key = provider_map.get(provider_name, provider_name.lower())
        
        # 更新状态栏 - 开始生成
        start_time = datetime.datetime.now()
        detailed_status = f"🔄 正在生成大纲...\n\n📊 当前进度: 开始生成\n📚 计划章节: {num_chapters}章\n🤖 AI提供商: {provider_name}\n🎯 使用模型: {model_name}\n💡 当前步骤: 大纲生成中\n📋 步骤描述: 正在创建小说大纲和故事结构"
        
        chapter_info = f"📖 大纲生成中...\n\n📋 计划章节数: {num_chapters}\n🎯 提供商: {provider_name}\n🤖 模型: {model_name}\n📝 当前阶段: 大纲创建\n⏰ 开始时间: {start_time.strftime('%H:%M:%S')}"
        
        generation_stats = {"已生成章节": 0, "预计总章节": num_chapters, "生成进度": "大纲生成中", "当前字数": 0}
        
        log_msg = f"🎯 开始生成大纲 - 提供商: {provider_name}, 模型: {model_name}"
        
        process_info = f"🔍 大纲生成过程\n\n📊 当前步骤: 大纲生成\n⏰ 开始时间: {start_time.strftime('%H:%M:%S')}\n🎯 提供商: {provider_name}\n🤖 模型: {model_name}\n\n📋 正在生成完整的小说大纲..."
        
        # 先yield初始状态
        yield (
            "", 
            "", 
            "", 
            "", 
            "", 
            gr.update(visible=False),
            detailed_status,
            chapter_info,
            generation_stats,
            log_msg,
            process_info
        )
        
        # 使用增强的小说创作器生成大纲
        writer = StoryWriter()
        
        # 设置提供商和模型
        if provider_key:
            writer.config_manager.provider_manager.switch_provider(provider_key)
        if model_name:
            writer.current_model = model_name
            
        logger.info(f"🎯 开始生成大纲 - 提供商: {provider_name}, 模型: {model_name}")
        
        outline_data = writer.generate_complete_outline(prompt, num_chapters, writing_style)
        
        # 验证返回数据
        required_keys = ["title", "plot", "character_list", "story_outline", "storyline"]
        for key in required_keys:
            if key not in outline_data:
                logger.error(f"❌ 大纲数据缺少必要键: {key}")
                raise gr.Error(f"生成的大纲数据不完整，缺少: {key}")
        
        logger.info(f"✅ 大纲生成成功 - 标题: {outline_data['title']}")
        
        # 更新状态栏 - 完成生成
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 估算总字数
        total_outline_words = len(outline_data["plot"]) + len(outline_data["character_list"]) + len(outline_data["story_outline"]) + len(outline_data["storyline"])
        
        success_detailed_status = f"✅ 大纲生成完成!\n\n📊 生成进度: 100% 完成\n📚 计划章节: {num_chapters}章\n🤖 AI提供商: {provider_name}\n🎯 使用模型: {model_name}\n💡 当前步骤: 大纲生成完成\n📋 小说标题: {outline_data['title']}\n🔢 大纲字数: {total_outline_words:,}字\n⏱️ 生成耗时: {duration:.2f}秒"
        
        success_chapter_info = f"📖 大纲生成成功!\n\n✅ 小说标题: {outline_data['title']}\n📋 计划章节: {num_chapters}章\n🔢 大纲总字数: {total_outline_words:,}字\n⏱️ 生成耗时: {duration:.2f}秒\n🎯 提供商: {provider_name}\n🤖 模型: {model_name}\n\n📚 现在可以开始创作小说了!"
        
        success_stats = {"已生成章节": 0, "预计总章节": num_chapters, "生成进度": "大纲完成", "当前字数": total_outline_words}
        
        success_log = f"✅ 大纲生成完成 - 标题: {outline_data['title'][:50]}{'...' if len(outline_data['title']) > 50 else ''}, 耗时: {duration:.2f}秒"
        
        success_process_info = f"🔍 大纲生成完成\n\n📊 最终状态: 成功完成\n⏰ 完成时间: {end_time.strftime('%H:%M:%S')}\n⏱️ 总耗时: {duration:.2f}秒\n\n📋 生成内容:\n• 小说标题: {outline_data['title']}\n• 情节梗概: {len(outline_data['plot'])}字\n• 人物列表: {len(outline_data['character_list'])}字\n• 故事大纲: {len(outline_data['story_outline'])}字\n• 详细故事线: {len(outline_data['storyline'])}字\n\n✅ 大纲创建成功，可以开始创作小说!"
        
        yield (
            outline_data["title"],
            outline_data["plot"], 
            outline_data["character_list"],
            outline_data["story_outline"],
            outline_data["storyline"],
            gr.update(visible=True),  # 显示开始创作按钮
            success_detailed_status,
            success_chapter_info,
            success_stats,
            success_log,
            success_process_info
        )
        
    except Exception as e:
        logger.error(f"❌ 大纲生成失败: {e}")
        
        # 更新状态栏 - 错误状态
        error_detailed_status = f"❌ 大纲生成失败!\n\n📊 生成进度: 错误\n📚 计划章节: {num_chapters}章\n🤖 AI提供商: {provider_name}\n🎯 使用模型: {model_name}\n💡 当前步骤: 生成失败\n📋 错误信息: {str(e)[:100]}...\n⚠️ 状态: 大纲生成失败"
        
        error_chapter_info = f"❌ 大纲生成失败!\n\n🚫 错误类型: 大纲生成异常\n📝 错误详情: {str(e)[:150]}...\n🔄 建议: 请检查配置后重试\n🎯 提供商: {provider_name}\n🤖 模型: {model_name}"
        
        error_stats = {"已生成章节": 0, "预计总章节": 0, "生成进度": "错误", "当前字数": 0}
        
        error_log = f"❌ 大纲生成失败: {str(e)}"
        
        error_process_info = f"🔍 大纲生成失败\n\n❌ 错误发生\n⏰ 时间: {datetime.datetime.now().strftime('%H:%M:%S')}\n🚫 错误信息: {str(e)[:100]}...\n🎯 提供商: {provider_name}\n🤖 模型: {model_name}\n\n🔄 请检查配置后重试"
        
        # 返回空值和隐藏按钮，同时更新状态栏
        yield (
            "", 
            "", 
            "", 
            "", 
            "", 
            gr.update(visible=False),
            error_detailed_status,
            error_chapter_info,
            error_stats,
            error_log,
            error_process_info
        )

def generate_novel_from_outline(title, plot, character_list, story_outline, storyline, 
                               num_chapters, writing_style, provider_name, model_name):
    """基于大纲生成小说（带进度追踪）"""
    logger.info(f"📝 开始基于大纲生成小说：{title}")
    
    # 构建大纲数据
    outline_data = {
        "title": title,
        "plot": plot,
        "character_list": character_list,
        "story_outline": story_outline,
        "storyline": storyline
    }
    
    # 转换提供商显示名称为内部键
    provider_map = {
        'DeepSeek': 'deepseek',
        '阿里云通义千问': 'alicloud', 
        '智谱AI GLM': 'zhipu',
        'Google Gemini': 'gemini',
        'OpenRouter': 'openrouter',
        'LM Studio': 'lmstudio',
        'Claude': 'claude',
        'Grok': 'grok'
    }
    provider_key = provider_map.get(provider_name, provider_name.lower())
    
    # 进度追踪变量
    current_step = 0
    total_steps = num_chapters + 3  # 章节数 + 初始化 + 保存 + 生成EPUB
    completed_chapters = []
    total_words = 0
    
    def progress_callback(step_name, current_chapter=None, chapter_content=None, is_completed=False):
        nonlocal current_step, completed_chapters, total_words
        
        if is_completed:
            current_step += 1
            if chapter_content:
                completed_chapters.append(current_chapter)
                total_words += len(chapter_content)
        
        # 计算进度
        progress = int((current_step / total_steps) * 100)
        
        # 更新详细生成状态
        status_lines = [
            f"🔄 小说生成进度: {progress}% ({current_step}/{total_steps})",
            f"📚 当前步骤: {step_name}",
            f"📝 已完成章节: {len(completed_chapters)}/{num_chapters}",
            f"📊 当前字数: {total_words:,}字"
        ]
        
        if current_chapter:
            status_lines.append(f"✍️ 正在处理: {current_chapter}")
        
        generation_status_text = "\n".join(status_lines)
        
        # 更新章节进度
        if completed_chapters:
            chapter_progress_text = f"✅ 已完成章节 ({len(completed_chapters)}/{num_chapters}):\n"
            for i, chapter in enumerate(completed_chapters[-10:], 1):  # 只显示最近10章
                chapter_progress_text += f"{i}. {chapter}\n"
            if len(completed_chapters) > 10:
                chapter_progress_text += f"... 及其他 {len(completed_chapters) - 10} 章\n"
        else:
            chapter_progress_text = "📝 正在准备章节创作..."
        
        # 更新统计信息
        stats = {
            "已生成章节": len(completed_chapters),
            "预计总章节": num_chapters,
            "生成进度": f"{progress}%",
            "当前字数": total_words,
            "当前步骤": step_name
        }
        
        return generation_status_text, chapter_progress_text, stats
    
    # 初始化状态
    status_text, progress_text, stats = progress_callback("初始化小说生成器...")
    
    try:
        # 使用增强的小说创作器
        writer = StoryWriter()
        
        # 添加进度回调到写作器
        def chapter_progress_callback(chapter_index, chapter_title, chapter_content):
            return progress_callback(
                f"正在创作第{chapter_index + 1}章",
                chapter_title,
                chapter_content,
                is_completed=True
            )
        
        # 修改写作器以支持进度回调
        progress_callback("正在生成章节内容...")
        _, title, chapters, chapter_titles, chapter_tokens_list = writer.write_novel_from_outline(
            outline_data, num_chapters, writing_style, provider_key, model_name
        )
        
        # 模拟章节完成进度（因为write_novel_from_outline不直接支持回调）
        for i, chapter in enumerate(chapters):
            # 安全地获取章节标题
            try:
                if isinstance(chapter_titles[i], dict):
                    chapter_title = list(chapter_titles[i].keys())[0]
                elif isinstance(chapter_titles[i], str):
                    chapter_title = chapter_titles[i]
                else:
                    chapter_title = f"第{i + 1}章"
            except (IndexError, KeyError, TypeError) as e:
                logger.warning(f"获取第{i + 1}章标题失败: {e}")
                chapter_title = f"第{i + 1}章"
            
            progress_callback(
                f"完成第{i + 1}章创作",
                chapter_title,
                chapter,
                is_completed=True
            )
        
        # 用chapter_titles中的正文取代章节说明
        for i, chapter in enumerate(chapters):
            try:
                if isinstance(chapter_titles[i], dict):
                    chapter_number_and_title = list(chapter_titles[i].keys())[0]
                    chapter_titles[i] = {chapter_number_and_title: chapter}
                elif isinstance(chapter_titles[i], str):
                    # 如果是字符串，创建字典结构
                    chapter_titles[i] = {chapter_titles[i]: chapter}
                else:
                    # 创建默认结构
                    chapter_titles[i] = {f"第{i + 1}章": chapter}
            except (IndexError, KeyError, TypeError) as e:
                logger.warning(f"处理第{i + 1}章标题失败: {e}")
                chapter_titles[i] = {f"第{i + 1}章": chapter}
        
        progress_callback("正在生成EPUB文件...")
        
        # 暂时跳过封面生成（功能保留，以后完善）
        image_url = None
        logger.info("封面生成功能已暂时禁用")
        
        # 生成小说 EPUB 文件（不使用封面）
        file_url = create_epub(title, 'AI', chapter_titles, cover_image_path=None)
        logger.info(f"Novel URL: {file_url}")
        
        # 保存到output文件夹
        progress_callback("正在保存小说文件...")
        novel_id = f"outline_{int(time.time())}"
        save_novel_to_output(title, chapters, chapter_titles, provider_name, model_name, total_words, novel_id)
        
        # 最终状态更新
        final_status, final_progress, final_stats = progress_callback("✅ 小说生成完成！", is_completed=True)
        
        logger.info(f"✅ 小说《{title}》生成完成，共{len(chapters)}章，{total_words:,}字")
        
        return (
            image_url,
            file_url,
            final_status,
            final_progress,
            final_stats
        )
        
    except Exception as e:
        error_message = f"❌ 小说生成失败: {str(e)}"
        logger.error(error_message)
        return (
            None,
            None,
            error_message,
            "生成失败",
            {"错误": str(e)}
        )

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
        'claude': 'Claude',
        'grok': 'Grok'
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
    """获取当前提供商的模型列表和默认模型"""
    try:
        # 获取实际可用的提供商，而不是配置中的当前提供商
        available_providers, current_provider_display = get_available_providers()
        
        # 转换显示名称为键
        provider_map = {
            'DeepSeek': 'deepseek',
            '阿里云通义千问': 'alicloud', 
            '智谱AI GLM': 'zhipu',
            'Google Gemini': 'gemini',
            'OpenRouter': 'openrouter',
            'LM Studio': 'lmstudio',
            'Claude': 'claude',
            'Grok': 'grok'
        }
        
        current_provider_key = provider_map.get(current_provider_display, 'deepseek')
        models = config_manager.provider_manager.get_models_for_provider(current_provider_key)
        if models:
            # 获取默认模型
            default_model = config_manager.provider_manager.get_default_model(current_provider_key)
            # 如果默认模型存在且在模型列表中，使用默认模型；否则使用第一个模型
            selected_model = default_model if default_model in models else models[0]
            return models, selected_model
        return ["默认模型"], "默认模型"
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        return ["默认模型"], "默认模型"

default_idea, default_style = get_default_values()
available_providers, current_provider = get_available_providers()
available_models, selected_model = get_models_for_current_provider()

version_info = get_version_info()
app_title = f"🎭 StoryGenius：AI智能小说创作平台 v{get_version()}"
app_description = f"""
### 🌟 欢迎使用StoryGenius AI小说创作平台

**版本**: {version_info['version']} ({version_info['codename']}) | **发布日期**: {version_info['release_date']}

支持8个AI提供商：**DeepSeek** | **阿里云** | **智谱AI** | **Google Gemini** | **OpenRouter** | **LM Studio** | **Claude** | **Grok**

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
            'Claude': 'claude',
            'Grok': 'grok'
        }
        
        provider_key = provider_map.get(provider_name)
        if provider_key:
            models = config_manager.provider_manager.get_models_for_provider(provider_key)
            if models:
                # 获取默认模型
                default_model = config_manager.provider_manager.get_default_model(provider_key)
                # 如果默认模型存在且在模型列表中，使用默认模型；否则使用第一个模型
                selected_model = default_model if default_model in models else models[0]
                return gr.update(choices=models, value=selected_model)
        
        return gr.update(choices=["默认模型"], value="默认模型")
    except Exception as e:
        logger.error(f"更新模型列表失败: {e}")
        return gr.update(choices=["默认模型"], value="默认模型")

def refresh_providers_and_status():
    """刷新提供商列表和状态"""
    try:
        available_providers, current_provider = get_available_providers()
        status_text = get_provider_status()
        
        # 获取当前提供商的模型（使用正确的默认模型）
        if available_providers:
            # 使用当前提供商而不是第一个可用提供商
            provider_to_use = current_provider if current_provider in available_providers else available_providers[0]
            models = update_models_dropdown(provider_to_use)
            return (
                gr.update(choices=available_providers, value=provider_to_use),
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
                'claude': 'Claude',
                'grok': 'Grok'
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
                        value=20, 
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
                            value=selected_model,
                            label="🎯 选择模型",
                            interactive=True
                        )
                    
                    # 提供商变更时更新模型列表
                    provider_input.change(
                        update_models_dropdown,
                        inputs=[provider_input],
                        outputs=[model_input]
                    )
                    
                    # 页面加载时刷新模型列表以确保显示正确的默认模型
                    def refresh_model_on_load():
                        """页面加载时刷新模型列表"""
                        try:
                            # 使用实际可用的提供商，而不是配置中的当前提供商
                            available_providers, current_provider_display = get_available_providers()
                            return update_models_dropdown(current_provider_display)
                        except Exception as e:
                            logger.error(f"刷新模型列表失败: {e}")
                            return gr.update(choices=["默认模型"], value="默认模型")
                    
                    # 页面加载时自动刷新
                    app.load(refresh_model_on_load, outputs=[model_input])
                    
                    # 生成按钮
                    with gr.Row():
                        generate_outline_btn = gr.Button(
                            "📋 生成大纲", 
                            variant="secondary", 
                            size="lg"
                        )
                        generate_novel_btn = gr.Button(
                            "🚀 开始创作小说", 
                            variant="primary", 
                            size="lg",
                            visible=False
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
            
            # 大纲预览区域
            with gr.Group(visible=False) as outline_preview:
                gr.Markdown("## 📋 大纲预览")
                with gr.Row():
                    with gr.Column(scale=1):
                        title_preview = gr.Textbox(
                            label="📚 小说标题",
                            interactive=False,
                            lines=3
                        )
                        plot_preview = gr.Textbox(
                            label="📖 情节梗概",
                            interactive=False,
                            lines=10
                        )
                    with gr.Column(scale=1):
                        character_preview = gr.Textbox(
                            label="👥 人物列表",
                            interactive=False,
                            lines=12
                        )
                
                with gr.Row():
                    story_outline_preview = gr.Textbox(
                        label="📋 故事大纲",
                        interactive=False,
                        lines=10,
                        max_lines=20
                    )
                    storyline_preview = gr.Textbox(
                        label="📝 详细故事线",
                        interactive=False,
                        lines=10,
                        max_lines=20
                    )
            
            # 进度显示区域
            with gr.Row():
                with gr.Column(scale=2):
                    # 详细的生成状态信息
                    generation_status = gr.Textbox(
                        label="📋 详细生成状态",
                        value="🔄 等待开始小说创作...\n\n📊 当前进度: 0%\n📚 章节状态: 未开始\n🔢 字数统计: 0字\n💡 当前步骤: 准备中",
                        interactive=False,
                        lines=8,
                        max_lines=12
                    )
                    
                with gr.Column(scale=1):
                    # 章节完成情况
                    chapter_progress = gr.Textbox(
                        label="📖 章节完成情况",
                        value="暂无章节完成",
                        interactive=False,
                        lines=8,
                        max_lines=12
                    )
                    
                    # 保留一个简化的统计JSON（隐藏）
                    generation_stats = gr.JSON(
                        label="📊 生成统计",
                        value={"已生成章节": 0, "预计总章节": 0, "生成进度": "0%", "当前字数": 0},
                        visible=False
                    )
                    
            
            # 实时日志和生成过程显示
            with gr.Row():
                with gr.Column(scale=1):
                    generation_log = gr.Textbox(
                        label="📝 生成日志",
                        value="",
                        interactive=False,
                        lines=6,
                        max_lines=10
                    )
                
                with gr.Column(scale=1):
                    generation_process = gr.Textbox(
                        label="🔍 生成过程详情",
                        value="暂无生成过程信息",
                        interactive=False,
                        lines=6,
                        max_lines=10
                    )
            
            # 输出区域
            with gr.Row():
                cover_output = gr.Image(label="📖 封面图片", width=1028, height=300)
                file_output = gr.File(label="📄 EPUB文件")
            
            # 绑定事件
            generate_outline_btn.click(
                generate_outline_with_progress,
                inputs=[prompt_input, chapters_input, style_input, provider_input, model_input],
                outputs=[title_preview, plot_preview, character_preview, story_outline_preview, storyline_preview, generate_novel_btn, generation_status, chapter_progress, generation_stats, generation_log, generation_process]
            ).then(
                lambda: gr.update(visible=True),
                outputs=[outline_preview]
            )
            
            generate_novel_btn.click(
                generate_novel_from_outline,
                inputs=[title_preview, plot_preview, character_preview, story_outline_preview, storyline_preview, chapters_input, style_input, provider_input, model_input],
                outputs=[cover_output, file_output, generation_status, chapter_progress, generation_stats]
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
            | **Grok** | 实时信息，幽默风格 | grok-3-mini |
            
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