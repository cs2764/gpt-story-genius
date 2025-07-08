import random
import os
import ast
import time
import logging
from typing import Dict, List, Tuple, Any
from config_manager import EnhancedConfigManager
from config import save_novel_chapter, generate_uuid

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
    
    def create_completion_with_monitoring(self, messages: List[Dict], **kwargs) -> Dict:
        """带监控的完成创建"""
        try:
            # 如果设置了当前模型，使用它
            if self.current_model and 'model' not in kwargs:
                kwargs['model'] = self.current_model
                logger.info(f"使用指定模型: {self.current_model}")
            
            response = self.config_manager.create_completion_with_monitoring(
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            raise
    
    def generate_plots(self, prompt: str) -> List[str]:
        """生成情节"""
        logger.info("生成小说情节...")
        
        # 获取系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是一个创意助手，专门生成引人入胜的奇幻小说情节。"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"基于这个提示生成10个奇幻小说情节：{prompt}"
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            user_content = current_provider.config.system_prompt + "\n\n" + user_content
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.create_completion_with_monitoring(messages)
        
        # 处理不同提供商的响应格式
        content = self.extract_content_from_response(response)
        return content.split('\n')
    
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
    
    def write_first_chapter(self, plot: str, first_chapter_title: str, writing_style: str) -> str:
        """写第一章"""
        logger.info("写作第一章...")
        
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
        initial_response = self.create_completion_with_monitoring(messages)
        initial_chapter = self.extract_content_from_response(initial_response)
        
        # 改进章节
        improvement_default_prompt = "你是一位世界级的奇幻小说作家。你的工作是拿你学生的第一章初稿，重写得更好，更详细。"
        improvement_user_content = f"这是你要求学生遵循的高级情节：{plot}\n\n这是他们写的第一章：{initial_chapter}\n\n现在，重写这部小说的第一章，要比你学生的章节好得多。它应该仍然遵循完全相同的情节，但应该更详细、更长、更引人入胜。以下是你应该使用的写作风格描述：`{writing_style}`。请用中文回答。"
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            improvement_user_content = current_provider.config.system_prompt + "\n\n" + improvement_user_content
            
        improvement_messages = [
            {"role": "system", "content": improvement_default_prompt},
            {"role": "user", "content": improvement_user_content}
        ]
        
        improved_response = self.create_completion_with_monitoring(improvement_messages)
        return self.extract_content_from_response(improved_response)
    
    def write_chapter(self, previous_chapters: str, plot: str, chapter_title: str) -> str:
        """写章节"""
        logger.info(f"写作章节：{chapter_title}")
        
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
            response = self.create_completion_with_monitoring(messages)
            return self.extract_content_from_response(response)
        except Exception as e:
            logger.warning(f"第一次尝试失败，重试：{e}")
            time.sleep(10)
            response = self.create_completion_with_monitoring(messages)
            return self.extract_content_from_response(response)
    
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
            
            novel = f"故事线:\n{storyline}\n\n"
            
            # 写第一章
            first_chapter = self.write_first_chapter(storyline, str(chapter_titles[0]), writing_style.strip())
            logger.info('第一章已完成')
            
            # 保存第一章
            save_novel_chapter(novel_id, 0, list(chapter_titles[0])[0], first_chapter)
            
            novel += f"第一章:\n{first_chapter}\n"
            chapters = [first_chapter]
            
            # 写其余章节
            for i in range(num_chapters - 1):
                logger.info(f"正在写第 {i + 2} 章...")
                time.sleep(10)  # 减少等待时间
                
                chapter = self.write_chapter(novel, storyline, str(chapter_titles[i + 1]))
                
                # 检查章节长度
                if len(str(chapter)) < 100:
                    logger.warning('章节长度不足，重新生成...')
                    time.sleep(10)
                    chapter = self.write_chapter(novel, storyline, str(chapter_titles[i + 1]))
                
                novel += f"第{i + 2}章:\n{chapter}\n"
                chapters.append(chapter)
                logger.info(f'第{i + 2}章已完成')
                
                # 保存章节
                save_novel_chapter(novel_id, (i+1), list(chapter_titles[i + 1])[0], chapter)
            
            # 获取监控摘要
            summary = self.config_manager.get_monitoring_summary(1)  # 最近1小时
            logger.info(f"创作完成，总成本：${summary['total_cost']:.4f}")
            
            return novel, title, chapters, chapter_titles
            
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
    
    return writer.write_fantasy_novel(prompt, num_chapters, writing_style, provider_name, model_name)