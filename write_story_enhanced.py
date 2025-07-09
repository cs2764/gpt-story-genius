import random
import os
import ast
import time
import logging
from typing import Dict, List, Tuple, Any
from config_manager import EnhancedConfigManager
from config import save_novel_chapter, generate_uuid, save_chapter_summary, load_chapter_summary, load_chapter_content

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StoryWriter:
    """增强的小说写作器"""
    
    def __init__(self):
        self.config_manager = EnhancedConfigManager()
        self.total_cost = 0.0
        self.current_model = None  # 存储当前使用的模型
    
    def estimate_tokens(self, text: str) -> int:
        """估算文本的token数量"""
        return len(text) // 4  # 粗略估算
    
    def get_token_stats(self, messages: List[Dict], response_content: str) -> Dict:
        """获取Token统计信息"""
        # 计算输入Token数
        input_text = ""
        for msg in messages:
            input_text += msg.get("content", "")
        
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(response_content)
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }
    
    def create_completion_with_monitoring(self, messages: List[Dict], **kwargs) -> Dict:
        """带监控的完成创建"""
        import time
        start_time = time.time()
        
        # 初始化变量以避免UnboundLocalError
        provider_name = "Unknown"
        model_name = "Unknown"
        
        try:
            # 获取当前提供商信息
            current_provider = self.config_manager.provider_manager.get_provider()
            provider_name = current_provider.config.name if current_provider else "Unknown"
            
            # 如果设置了当前模型，使用它
            model_name = kwargs.get('model', self.current_model)
            if self.current_model and 'model' not in kwargs:
                kwargs['model'] = self.current_model
                model_name = self.current_model
            
            # 计算输入Token数量
            input_text = ""
            for msg in messages:
                input_text += msg.get("content", "")
            estimated_input_tokens = self.estimate_tokens(input_text)
            
            # 记录API调用开始
            logger.info("=" * 80)
            logger.info(f"🚀 API调用开始")
            logger.info(f"📡 提供商: {provider_name}")
            logger.info(f"🤖 模型: {model_name}")
            logger.info(f"📊 预估输入Token: {estimated_input_tokens:,}")
            logger.info(f"💬 消息数量: {len(messages)}")
            logger.info(f"⚙️ 参数: {kwargs}")
            logger.info(f"🕐 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
            
            # 记录消息详情
            for i, msg in enumerate(messages):
                content_preview = msg.get("content", "")[:200] + "..." if len(msg.get("content", "")) > 200 else msg.get("content", "")
                logger.info(f"📝 消息{i+1} [{msg.get('role', 'unknown')}]: {content_preview}")
            
            logger.info("-" * 80)
            
            response = self.config_manager.create_completion_with_monitoring(
                messages=messages,
                **kwargs
            )
            
            # 计算响应时间和Token
            end_time = time.time()
            response_time = end_time - start_time
            response_content = self.extract_content_from_response(response)
            estimated_output_tokens = self.estimate_tokens(response_content)
            total_tokens = estimated_input_tokens + estimated_output_tokens
            
            # 记录API调用结果
            logger.info(f"✅ API调用成功")
            logger.info(f"⏱️ 响应时间: {response_time:.2f}秒")
            logger.info(f"📊 输出Token: {estimated_output_tokens:,}")
            logger.info(f"📊 总Token: {total_tokens:,}")
            logger.info(f"📄 响应长度: {len(response_content)}字符")
            logger.info(f"📝 响应预览: {response_content[:300]}...")
            logger.info("=" * 80)
            
            return response
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            logger.error("=" * 80)
            logger.error(f"❌ API调用失败")
            logger.error(f"📡 提供商: {provider_name}")
            logger.error(f"🤖 模型: {model_name}")
            logger.error(f"⏱️ 失败时间: {response_time:.2f}秒")
            logger.error(f"🚫 错误信息: {str(e)}")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            logger.error("=" * 80)
            raise
    
    def generate_plots(self, prompt: str) -> List[str]:
        """生成情节"""
        logger.info("🎭 开始生成小说情节")
        logger.info(f"📝 用户提示: {prompt}")
        
        # 获取系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是一个创意助手，专门生成引人入胜的奇幻小说情节。"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"基于这个提示生成10个奇幻小说情节：{prompt}"
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            user_content = current_provider.config.system_prompt + "\n\n" + user_content
            logger.info(f"📋 使用用户自定义系统提示词: {current_provider.config.system_prompt[:100]}...")
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        logger.info(f"📤 发送情节生成请求")
        response = self.create_completion_with_monitoring(messages)
        
        # 处理不同提供商的响应格式
        content = self.extract_content_from_response(response)
        plots = content.split('\n')
        
        logger.info(f"✅ 成功生成 {len(plots)} 个情节候选")
        for i, plot in enumerate(plots[:5]):  # 只显示前5个
            if plot.strip():
                logger.info(f"📖 情节{i+1}: {plot.strip()[:150]}...")
        
        return plots
    
    def select_most_engaging(self, plots: List[str]) -> str:
        """选择最吸引人的情节"""
        logger.info("选择最佳情节...")
        
        # 获取系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是写作奇幻小说情节的专家。"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"这里有一些可能的小说情节：{plots}\n\n现在，写出我们将采用的最终情节。它可以是其中一个，也可以是多个最佳元素的混合，或者是全新且更好的东西。最重要的是情节应该是奇妙的、独特的和引人入胜的。"
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            user_content = current_provider.config.system_prompt + "\n\n" + user_content
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.create_completion_with_monitoring(messages)
        return self.extract_content_from_response(response)
    
    def improve_plot(self, plot: str) -> str:
        """改进情节"""
        logger.info("改进情节...")
        
        # 获取系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是改进和完善故事情节的专家。"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"改进这个情节：{plot}"
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            user_content = current_provider.config.system_prompt + "\n\n" + user_content
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.create_completion_with_monitoring(messages)
        return self.extract_content_from_response(response)
    
    def get_title(self, plot: str) -> str:
        """获取标题"""
        logger.info("生成标题...")
        
        # 获取系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是一位专业作家。"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"这是情节：{plot}\n\n这本书的标题是什么？只回答标题，不要做其他事情。请用中文回答。"
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            user_content = current_provider.config.system_prompt + "\n\n" + user_content
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.create_completion_with_monitoring(messages)
        title = self.extract_content_from_response(response)
        
        # 额外清理标题，确保适合作为文件名
        return self.sanitize_filename(title)
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不安全字符"""
        import re
        
        if not filename:
            return "未命名小说"
        
        # 移除引号、书名号等
        filename = re.sub(r'["""''《》【】\\[\\]<>]', '', filename)
        
        # 移除或替换Windows文件名不允许的字符
        filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
        
        # 移除多余的空格和换行
        filename = re.sub(r'\s+', ' ', filename).strip()
        
        # 限制长度（防止路径过长）
        if len(filename) > 50:
            filename = filename[:50].strip()
        
        # 如果清理后为空，提供默认名称
        if not filename or filename.isspace():
            filename = "未命名小说"
        
        return filename
    
    def write_first_chapter(self, plot: str, first_chapter_title: str, writing_style: str) -> Tuple[str, Dict]:
        """写第一章，返回内容和Token统计"""
        logger.info("📝 开始写作第一章")
        logger.info(f"📖 章节标题: {first_chapter_title}")
        logger.info(f"✍️ 写作风格: {writing_style}")
        logger.info(f"📋 情节摘要: {plot[:200]}...")
        
        # 获取当前提供商的系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是一位世界级的奇幻小说作家。"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"这是要遵循的高级情节：{plot}\n\n写这部小说的第一章：`{first_chapter_title}`。\n\n让它变得独特、引人入胜且写得很好。\n\n以下是您应该使用的写作风格描述：`{writing_style}`\n\n只包含章节文本。无需重写章节名称。请用中文回答。"
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            user_content = current_provider.config.system_prompt + "\n\n" + user_content
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        # 第一次生成
        logger.info("📤 发送第一章初稿生成请求")
        initial_response = self.create_completion_with_monitoring(messages)
        initial_chapter = self.extract_content_from_response(initial_response)
        initial_stats = self.get_token_stats(messages, initial_chapter)
        
        logger.info(f"📊 第一章初稿完成 - 字数: {len(initial_chapter)}, Token: {initial_stats['total_tokens']:,}")
        
        # 改进章节
        logger.info("🔄 开始改进第一章")
        improvement_default_prompt = "你是一位世界级的奇幻小说作家。你的工作是拿你学生的第一章初稿，重写得更好，更详细。"
        improvement_user_content = f"这是你要求学生遵循的高级情节：{plot}\n\n这是他们写的第一章：{initial_chapter}\n\n现在，重写这部小说的第一章，要比你学生的章节好得多。它应该仍然遵循完全相同的情节，但应该更详细、更长、更引人入胜。以下是你应该使用的写作风格描述：`{writing_style}`。请用中文回答。"
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            improvement_user_content = current_provider.config.system_prompt + "\n\n" + improvement_user_content
            
        improvement_messages = [
            {"role": "system", "content": improvement_default_prompt},
            {"role": "user", "content": improvement_user_content}
        ]
        
        logger.info("📤 发送第一章改进请求")
        improved_response = self.create_completion_with_monitoring(improvement_messages)
        final_chapter = self.extract_content_from_response(improved_response)
        improvement_stats = self.get_token_stats(improvement_messages, final_chapter)
        
        # 合并Token统计
        total_stats = {
            "input_tokens": initial_stats["input_tokens"] + improvement_stats["input_tokens"],
            "output_tokens": initial_stats["output_tokens"] + improvement_stats["output_tokens"],
            "total_tokens": initial_stats["total_tokens"] + improvement_stats["total_tokens"]
        }
        
        logger.info(f"✅ 第一章创作完成!")
        logger.info(f"📊 最终统计 - 字数: {len(final_chapter)}, 总Token: {total_stats['total_tokens']:,}")
        logger.info(f"📈 改进效果 - 字数增加: {len(final_chapter) - len(initial_chapter)}, Token增加: {total_stats['total_tokens'] - initial_stats['total_tokens']:,}")
        
        return final_chapter, total_stats
    
    def write_chapter(self, previous_chapters: str, plot: str, chapter_title: str) -> Tuple[str, Dict]:
        """写章节，返回内容和Token统计"""
        logger.info(f"📝 开始写作章节：{chapter_title}")
        logger.info(f"📊 上下文长度: {len(previous_chapters)}字符")
        logger.info(f"📋 情节长度: {len(plot)}字符")
        
        # 获取当前提供商的系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是一位世界级的奇幻小说作家。"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"情节：{plot}，前面的章节：{previous_chapters}\n\n--\n\n根据情节写这部小说的下一章，并将前面的章节作为背景。这是本章的计划：{chapter_title}\n\n写得漂亮。只包含章节文本。无需重写章节名称。请用中文回答。"
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            user_content = current_provider.config.system_prompt + "\n\n" + user_content
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        try:
            logger.info("📤 发送章节生成请求")
            response = self.create_completion_with_monitoring(messages)
            chapter_content = self.extract_content_from_response(response)
            token_stats = self.get_token_stats(messages, chapter_content)
            
            logger.info(f"✅ 章节生成成功")
            logger.info(f"📊 章节统计 - 字数: {len(chapter_content)}, Token: {token_stats['total_tokens']:,}")
            
            return chapter_content, token_stats
        except Exception as e:
            logger.warning(f"❌ 第一次尝试失败，准备重试：{e}")
            logger.info("⏳ 等待10秒后重试...")
            time.sleep(10)
            
            logger.info("🔄 重试章节生成请求")
            response = self.create_completion_with_monitoring(messages)
            chapter_content = self.extract_content_from_response(response)
            token_stats = self.get_token_stats(messages, chapter_content)
            
            logger.info(f"✅ 重试成功")
            logger.info(f"📊 章节统计 - 字数: {len(chapter_content)}, Token: {token_stats['total_tokens']:,}")
            
            return chapter_content, token_stats
    
    def summarize_chapter(self, chapter_content: str, chapter_title: str) -> str:
        """生成章节摘要"""
        logger.info(f"📄 开始生成章节摘要：{chapter_title}")
        logger.info(f"📊 章节内容长度: {len(chapter_content)}字符")
        
        # 获取当前提供商的系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是一位专业的文学编辑，专门负责为小说章节创建简洁而全面的摘要。"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"""请为以下小说章节生成一个简洁但全面的摘要。摘要应该：
1. 保留关键情节发展
2. 记录重要人物动向和对话要点
3. 突出与整体故事发展相关的重要细节
4. 长度控制在200-300字之间
5. 用中文回答

章节标题：{chapter_title}

章节内容：
{chapter_content}

请生成摘要："""
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            user_content = current_provider.config.system_prompt + "\n\n" + user_content
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        try:
            logger.info("📤 发送摘要生成请求")
            response = self.create_completion_with_monitoring(messages)
            summary = self.extract_content_from_response(response)
            
            logger.info(f"✅ 摘要生成成功")
            logger.info(f"📊 摘要长度: {len(summary)}字符")
            logger.info(f"📝 摘要预览: {summary[:100]}...")
            
            return summary
        except Exception as e:
            logger.warning(f"❌ 摘要生成失败，使用备用方案：{e}")
            # 备用方案：从章节内容提取前几句作为摘要
            sentences = chapter_content.split('。')
            summary = '。'.join(sentences[:3]) + '。'
            backup_summary = f"【{chapter_title}】\n{summary}"
            
            logger.info(f"🔄 使用备用摘要方案")
            logger.info(f"📊 备用摘要长度: {len(backup_summary)}字符")
            
            return backup_summary
    
    def build_optimized_context(self, novel_id: str, current_chapter_index: int, recent_chapters_count: int = 1, summary_chapters_count: int = 5) -> str:
        """构建优化的上下文，使用过去5章摘要+过去1章全文"""
        logger.info(f"🔧 开始构建优化上下文")
        logger.info(f"📖 当前章节索引: {current_chapter_index}")
        logger.info(f"📚 保留全文的最近章节数: {recent_chapters_count}")
        logger.info(f"📋 保留摘要的章节数: {summary_chapters_count}")
        
        context_parts = []
        total_full_text_chars = 0
        total_summary_chars = 0
        
        # 如果章节数较少，直接使用全文
        if current_chapter_index <= recent_chapters_count:
            logger.info(f"📋 使用全文模式（章节数 <= {recent_chapters_count}）")
            for i in range(current_chapter_index):
                chapter_content = load_chapter_content(novel_id, i)
                if chapter_content:
                    context_parts.append(f"第{i+1}章:\n{chapter_content}")
                    total_full_text_chars += len(chapter_content)
                    logger.info(f"📄 加载第{i+1}章全文: {len(chapter_content)}字符")
        else:
            logger.info(f"🔄 使用优化模式（过去{summary_chapters_count}章摘要+过去{recent_chapters_count}章全文）")
            
            # 计算要包含的章节范围
            total_context_chapters = summary_chapters_count + recent_chapters_count
            start_chapter_index = max(0, current_chapter_index - total_context_chapters)
            summary_end_index = max(0, current_chapter_index - recent_chapters_count)
            
            logger.info(f"📄 章节范围: 第{start_chapter_index+1}-{current_chapter_index}章")
            logger.info(f"📋 摘要章节: 第{start_chapter_index+1}-{summary_end_index}章")
            logger.info(f"📖 全文章节: 第{summary_end_index+1}-{current_chapter_index}章")
            
            # 添加摘要章节（过去5章，不包括最近1章）
            for i in range(start_chapter_index, summary_end_index):
                summary = load_chapter_summary(novel_id, i)
                if summary:
                    context_parts.append(f"第{i+1}章摘要:\n{summary}")
                    total_summary_chars += len(summary)
                    logger.info(f"📋 加载第{i+1}章摘要: {len(summary)}字符")
                else:
                    # 如果没有摘要，使用全文的前几句
                    logger.warning(f"⚠️ 第{i+1}章摘要缺失，使用简化摘要")
                    chapter_content = load_chapter_content(novel_id, i)
                    if chapter_content:
                        sentences = chapter_content.split('。')
                        brief_summary = '。'.join(sentences[:2]) + '。'
                        context_parts.append(f"第{i+1}章摘要:\n{brief_summary}")
                        total_summary_chars += len(brief_summary)
                        logger.info(f"🔄 生成第{i+1}章简化摘要: {len(brief_summary)}字符")
            
            # 添加全文章节（过去1章）
            for i in range(summary_end_index, current_chapter_index):
                chapter_content = load_chapter_content(novel_id, i)
                if chapter_content:
                    context_parts.append(f"第{i+1}章:\n{chapter_content}")
                    total_full_text_chars += len(chapter_content)
                    logger.info(f"📄 加载第{i+1}章全文: {len(chapter_content)}字符")
        
        # 构建最终上下文
        if context_parts:
            final_context = "\n\n".join(context_parts)
            
            # 统计信息
            total_chars = len(final_context)
            estimated_tokens = self.estimate_tokens(final_context)
            
            logger.info(f"✅ 上下文构建完成")
            logger.info(f"📊 上下文统计:")
            logger.info(f"  • 总字符数: {total_chars:,}")
            logger.info(f"  • 全文字符数: {total_full_text_chars:,}")
            logger.info(f"  • 摘要字符数: {total_summary_chars:,}")
            logger.info(f"  • 预估Token: {estimated_tokens:,}")
            
            if total_summary_chars > 0:
                reduction_percent = (total_summary_chars / (total_full_text_chars + total_summary_chars)) * 100
                logger.info(f"  • Token优化比例: {reduction_percent:.1f}% 使用摘要")
            
            return final_context
        else:
            logger.warning("⚠️ 无可用上下文，返回默认开始")
            return "故事开始..."
    
    def generate_storyline(self, prompt: str, num_chapters: int) -> str:
        """生成故事线"""
        logger.info("生成包含章节和高级细节的故事线...")
        
        json_format = """[{"Chapter CHAPTER_NUMBER_HERE - CHAPTER_TITLE_GOES_HERE": 
        "CHAPTER_OVERVIEW_AND_DETAILS_GOES_HERE"}, ...]"""
        
        # 获取系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是一位世界级的奇幻小说作家。你的工作是为奇幻小说写一个详细的故事线，包括章节。不要太华丽——你要用尽可能少的词来传达信息。但这些词应该包含大量信息。请用中文回答"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f'基于这个情节写一个包含{num_chapters}章和高级细节的精彩故事线：{prompt}。\n\n按照这种字典列表格式{json_format}。请用中文回答。响应内容必须是标准JSON格式，没有任何前缀和特殊符号。'
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            user_content = current_provider.config.system_prompt + "\n\n" + user_content
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.create_completion_with_monitoring(messages)
        initial_storyline = self.extract_content_from_response(response)
        
        # 改进故事线
        improvement_user_content = f"这是他们写的故事线草稿：{initial_storyline}\n\n现在，用中文重写故事线，要比你学生的版本好得多。它应该有相同的章节数，但应该在尽可能多的方面得到改进。记住按照这种字典列表格式{json_format}。请用中文回答，只返回JSON内容，没有任何前缀。"
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            improvement_user_content = current_provider.config.system_prompt + "\n\n" + improvement_user_content
            
        improvement_messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": improvement_user_content}
        ]
        
        improved_response = self.create_completion_with_monitoring(improvement_messages)
        return self.extract_content_from_response(improved_response)
    
    def extract_content_from_response(self, response: Dict) -> str:
        """从不同提供商的响应中提取内容"""
        try:
            content = ""
            
            # OpenAI格式
            if 'choices' in response:
                content = response['choices'][0]['message']['content']
            
            # Claude格式
            elif 'content' in response:
                if isinstance(response['content'], list):
                    content = response['content'][0]['text']
                else:
                    content = response['content']
            
            # Gemini格式
            elif 'candidates' in response:
                content = response['candidates'][0]['content']['parts'][0]['text']
            
            # 通用格式
            elif 'text' in response:
                content = response['text']
            
            # 如果都不匹配，尝试转换为字符串
            else:
                content = str(response)
            
            # 清理思考模式标签和其他不需要的内容
            return self.clean_response_content(content)
            
        except Exception as e:
            logger.error(f"提取响应内容失败: {e}")
            return str(response)
    
    def clean_response_content(self, content: str) -> str:
        """清理响应内容，移除思考标签等不必要内容"""
        if not isinstance(content, str):
            content = str(content)
        
        import re
        
        # 移除思考标签 <think>...</think> 和 <\\think>
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        content = re.sub(r'<\\think>', '', content)
        content = re.sub(r'<think>', '', content)
        content = re.sub(r'</think>', '', content)
        
        # 移除其他可能的XML标签
        content = re.sub(r'<[^>]+>', '', content)
        
        # 移除多余的换行和空格
        content = re.sub(r'\n+', '\n', content)
        content = content.strip()
        
        return content
    
    def write_fantasy_novel(self, prompt: str, num_chapters: int, writing_style: str, 
                           provider_name: str = None, model_name: str = None) -> Tuple[str, str, List[str], List[Dict]]:
        """写奇幻小说"""
        logger.info(f"开始创作小说，章节数：{num_chapters}")
        
        # 如果指定了提供商，切换到该提供商
        if provider_name:
            try:
                self.config_manager.provider_manager.switch_provider(provider_name)
                logger.info(f"切换到提供商：{provider_name}")
            except Exception as e:
                logger.warning(f"切换提供商失败：{e}")
        
        # 设置当前使用的模型
        if model_name:
            self.current_model = model_name
            logger.info(f"设置使用模型：{model_name}")
        else:
            self.current_model = None
        
        # 生成唯一的小说ID
        novel_id = generate_uuid()
        
        try:
            # 应用默认想法配置
            if self.config_manager.default_ideas_config.enabled:
                if self.config_manager.default_ideas_config.default_idea:
                    prompt = self.config_manager.default_ideas_config.default_idea
                if self.config_manager.default_ideas_config.default_writing_style:
                    writing_style = self.config_manager.default_ideas_config.default_writing_style
            
            # 生成情节
            plots = self.generate_plots(prompt)
            logger.info(f'生成的情节: {plots}')
            
            best_plot = self.select_most_engaging(plots)
            logger.info(f'选择的最佳情节: {best_plot}')
            
            improved_plot = self.improve_plot(best_plot)
            logger.info(f'改进的情节: {improved_plot}')
            time.sleep(5)  # 减少等待时间
            
            title = self.get_title(improved_plot)
            logger.info(f'生成的标题: {title}')
            
            storyline = self.generate_storyline(improved_plot, num_chapters)
            logger.info(f'生成的故事线: {storyline}')
            
            # 解析章节标题
            try:
                chapter_titles = ast.literal_eval(storyline)
            except Exception as e:
                logger.error(f"解析故事线失败: {e}")
                # 创建默认章节结构
                chapter_titles = [
                    {f"Chapter {i+1} - 第{i+1}章": f"第{i+1}章内容"}
                    for i in range(num_chapters)
                ]
            
            logger.info(f'章节标题: {chapter_titles}')
            
            # 写第一章
            first_chapter, first_chapter_tokens = self.write_first_chapter(storyline, str(chapter_titles[0]), writing_style.strip())
            logger.info(f'第一章已完成 - 输入Token: {first_chapter_tokens["input_tokens"]}, 输出Token: {first_chapter_tokens["output_tokens"]}')
            
            # 保存第一章
            save_novel_chapter(novel_id, 0, list(chapter_titles[0])[0], first_chapter)
            
            # 生成第一章摘要
            first_chapter_title = list(chapter_titles[0])[0]
            first_chapter_summary = self.summarize_chapter(first_chapter, first_chapter_title)
            save_chapter_summary(novel_id, 0, first_chapter_summary)
            logger.info('第一章摘要已生成')
            
            chapters = [first_chapter]
            chapter_tokens_list = [first_chapter_tokens]  # 存储每章的Token统计
            
            # 写其余章节 - 使用优化的上下文构建
            for i in range(num_chapters - 1):
                current_chapter_index = i + 1  # 当前要写的章节索引（0-based）
                logger.info(f"正在写第 {current_chapter_index + 1} 章...")
                time.sleep(10)  # 减少等待时间
                
                # 构建优化的上下文（使用过去5章摘要 + 过去1章全文）
                optimized_context = self.build_optimized_context(novel_id, current_chapter_index, recent_chapters_count=1, summary_chapters_count=5)
                
                # 写章节时使用优化的上下文而不是完整的novel字符串
                chapter, chapter_tokens = self.write_chapter(optimized_context, storyline, str(chapter_titles[i + 1]))
                
                # 检查章节长度
                if len(str(chapter)) < 100:
                    logger.warning('章节长度不足，重新生成...')
                    time.sleep(10)
                    chapter, chapter_tokens = self.write_chapter(optimized_context, storyline, str(chapter_titles[i + 1]))
                
                chapters.append(chapter)
                chapter_tokens_list.append(chapter_tokens)
                logger.info(f'第{current_chapter_index + 1}章已完成 - 输入Token: {chapter_tokens["input_tokens"]}, 输出Token: {chapter_tokens["output_tokens"]}')
                
                # 保存章节
                chapter_title = list(chapter_titles[i + 1])[0]
                save_novel_chapter(novel_id, current_chapter_index, chapter_title, chapter)
                
                # 生成并保存章节摘要（除了最后一章）
                if current_chapter_index < num_chapters - 1:  # 不是最后一章
                    chapter_summary = self.summarize_chapter(chapter, chapter_title)
                    save_chapter_summary(novel_id, current_chapter_index, chapter_summary)
                    logger.info(f'第{current_chapter_index + 1}章摘要已生成')
            
            # 获取监控摘要
            summary = self.config_manager.get_monitoring_summary(1)  # 最近1小时
            logger.info(f"创作完成，总成本：${summary['total_cost']:.4f}")
            
            # 为了向后兼容，构建完整的novel字符串
            novel = f"故事线:\n{storyline}\n\n"
            for i, chapter in enumerate(chapters):
                novel += f"第{i+1}章:\n{chapter}\n\n"
            
            return novel, title, chapters, chapter_titles, chapter_tokens_list
            
        except Exception as e:
            logger.error(f"创作小说时发生错误: {e}")
            raise

# 向后兼容的函数
def write_fantasy_novel(prompt: str, num_chapters: int, writing_style: str, 
                       claude_true=False, model_name="gpt-3.5-turbo-16k") -> Tuple[str, str, List[str], List[Dict]]:
    """向后兼容的小说创作函数"""
    writer = StoryWriter()
    
    # 根据claude_true参数选择提供商
    if claude_true:
        provider_name = "claude"
    else:
        provider_name = None  # 使用当前配置的提供商
    
    # 调用新版本函数，但只返回前4个元素以保持向后兼容
    result = writer.write_fantasy_novel(prompt, num_chapters, writing_style, provider_name, model_name)
    return result[:4]  # 只返回 novel, title, chapters, chapter_titles