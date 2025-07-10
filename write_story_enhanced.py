import ast
import time
import logging
from typing import Dict, List, Tuple
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
            
            # 尝试提取详细的错误信息
            error_code = 0
            error_details = ""
            detailed_error_msg = str(e)
            
            # 检查是否是HTTP错误，尝试提取状态码
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                error_code = e.response.status_code
                try:
                    error_details = e.response.text
                except:
                    pass
            elif "403" in str(e):
                error_code = 403
            elif "429" in str(e):
                error_code = 429
            elif "502" in str(e):
                error_code = 502
            elif "503" in str(e):
                error_code = 503
            
            # 增强的控制台错误显示
            logger.error("=" * 80)
            logger.error(f"❌ API调用失败")
            logger.error(f"📡 提供商: {provider_name}")
            logger.error(f"🤖 模型: {model_name}")
            logger.error(f"⏱️ 失败时间: {response_time:.2f}秒")
            if error_code > 0:
                logger.error(f"🔢 错误代码: {error_code}")
            logger.error(f"🚫 错误信息: {detailed_error_msg}")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            if error_details:
                logger.error(f"📋 详细信息: {error_details[:200]}...")
            
            # 根据错误类型提供解决建议
            if error_code == 403:
                logger.error(f"💡 解决建议: 检查内容是否违反审核规则，或切换其他模型")
            elif error_code == 429:
                logger.error(f"💡 解决建议: 请求频率过高，建议等待后重试")
            elif error_code == 502:
                logger.error(f"💡 解决建议: 模型可能暂时不可用，建议切换其他模型")
            elif error_code == 503:
                logger.error(f"💡 解决建议: 服务暂时不可用，建议稍后重试或调整模型选择")
            
            logger.error("=" * 80)
            
            # 在错误消息中包含更多信息，便于UI显示
            if error_code > 0:
                enhanced_error_msg = f"[{error_code}] {detailed_error_msg}"
                if "OpenRouter" in detailed_error_msg:
                    if error_code == 403:
                        enhanced_error_msg += " | 建议: 检查内容审核或切换模型"
                    elif error_code == 429:
                        enhanced_error_msg += " | 建议: 降低请求频率"
                    elif error_code == 502:
                        enhanced_error_msg += " | 建议: 切换其他可用模型"
                    elif error_code == 503:
                        enhanced_error_msg += " | 建议: 稍后重试或调整模型选择"
                
                # 创建一个包含详细信息的新异常
                enhanced_exception = type(e)(enhanced_error_msg)
                enhanced_exception.error_code = error_code
                enhanced_exception.error_details = error_details
                enhanced_exception.provider = provider_name
                enhanced_exception.model = model_name
                raise enhanced_exception
            
            raise
    
    def generate_plots(self, prompt: str) -> List[str]:
        """生成情节"""
        logger.info("🎭 开始生成小说情节")
        logger.info(f"📝 用户提示: {prompt}")
        
        # 获取系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是一个创意助手，专门生成引人入胜的网络小说作家小说情节。"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"基于这个提示生成10个网络小说情节：{prompt}"
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
        default_system_prompt = "你是写作网络小说情节的专家。"
        
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
    
    def generate_character_list(self, plot: str, num_chapters: int) -> str:
        """生成主要人物列表"""
        logger.info("📚 开始生成主要人物列表...")
        logger.info(f"📖 基于情节: {plot[:200]}...")
        logger.info(f"📊 章节数: {num_chapters}")
        
        # 获取系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是一位专业的小说角色设计师，专门为网络小说创建详细的角色档案。"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"""基于以下情节为{num_chapters}章的网络小说创建主要人物列表：

情节：{plot}

请创建一个详细的人物列表，包含：
1. 主角（1-2个）
2. 重要配角（3-5个）
3. 反派角色（1-2个）
4. 其他关键角色（根据需要）

每个角色需要包含：
- 姓名
- 年龄
- 性格特点
- 背景设定
- 在故事中的作用
- 能力或特长
- 外貌特征

请按照以下JSON格式返回：
{{
  "characters": [
    {{
      "name": "角色姓名",
      "age": "年龄",
      "personality": "性格特点",
      "background": "背景设定",
      "role": "在故事中的作用",
      "abilities": "能力或特长",
      "appearance": "外貌特征",
      "importance": "主角/配角/反派"
    }}
  ]
}}

请用中文回答，只返回JSON内容，不要添加任何前缀或后缀。"""
        
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            user_content = current_provider.config.system_prompt + "\n\n" + user_content
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        logger.info("📤 发送人物列表生成请求")
        response = self.create_completion_with_monitoring(messages)
        character_list = self.extract_content_from_response(response)
        
        logger.info("✅ 主要人物列表生成完成")
        logger.info(f"📊 人物列表长度: {len(character_list)}字符")
        
        return character_list
    
    def generate_story_outline(self, plot: str, character_list: str, num_chapters: int) -> str:
        """生成文章大纲"""
        logger.info("📋 开始生成文章大纲...")
        logger.info(f"📖 基于情节: {plot[:200]}...")
        logger.info(f"📊 章节数: {num_chapters}")
        
        # 获取系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = """# 角色定位：
您是一位才华横溢的网络小说作家，因打破常规，用不同寻常的剧情和创意著称。同时，您也是一位经验丰富的金牌编剧，擅长将零散的想法构筑成结构完整、情节丰富、引人入胜的精彩故事。您必须使用中文创作所有内容。

## 背景与目标：
您正站在创作一部小说的起点，面前是一片等待被填充的白纸。您的目标是创作一部不仅结构完整、剧情引人深思、设定独树一帜的作品，而且能够触动读者心弦，带给他们既刺激又满足的阅读体验。您需要基于提供的信息，细化并构思出一个能够实现这些目标的小说大纲。所有输出内容必须使用中文。

## 您具有以下专业能力：
- 深厚的故事结构理论知识和实践经验
- 丰富的人物塑造和角色发展经验
- 敏锐的情节安排和节奏控制能力
- 对读者心理和市场需求的深刻理解
- 创新思维和打破常规的创作能力
- 精通中文表达和叙事技巧

## 工作流程：
1. **深入挖掘创意火花**：认真理解并分析提供的创意，捕捉其中的亮点和独特之处，探索这些想法的潜力和可能的拓展方向。
2. **魅力四射的开场**：构思一个立即抓住读者眼球的开场，通过情感波动的场景、令人震撼的事件或极具特色的角色来吸引读者。
3. **精心设计的高潮环节**：巧妙布局一个或几个高潮点，构建紧张刺激的情节发展，这些高潮既是对主角的挑战，也是故事的关键转折点。
4. **反转与惊奇的艺术**：设计既出乎意料又情理之中的剧情反转，给读者带来惊喜，展现角色深藏的一面或揭露背后的秘密。
5. **富有深意的结局**：以一个既巧妙又令人满意的结局收尾，揭露故事所蕴含的深层次意义，激发读者对人性、社会或生活本质的思考。
6. **保持创意的新鲜感**：确保每个故事元素和情节发展都具有原创性和新鲜感，避免陈词滥调或高度可预测的叙事模式。
7. **输出精细化的小说大纲**：综合创意和创新思维，构建一份详细的小说大纲，明确故事的核心主题和深层寓意。所有内容必须用中文表达。"""
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"""## 输入信息：
您将基于以下信息为{num_chapters}章的小说创建详细的故事大纲：

**情节设定：**
{plot}

**人物列表：**
{character_list}

**章节数量：** {num_chapters}章

## 输出格式：
请按照以下固定格式输出：
```json
{{
  "outline": [
    {{
      "part": "部分名称",
      "chapters": "章节范围",
      "chapter_numbers": [章节数字数组],
      "summary": "详细剧情梗概（300-500字，包含具体场景、对话要点、行动细节、人物心理变化等）",
      "key_events": ["关键事件列表"],
      "character_development": "角色发展变化",
      "connection": "与前后部分的衔接关系",
      "conflict_type": "冲突类型",
      "story_function": "在整个故事中的功能作用"
    }}
  ]
}}
```

## 详细要求：
请严格按照以下结构和要求来生成小说大纲：

**故事完整性要求：**
- 大纲必须讲述一个从开端到结局的完整故事
- 清晰地呈现主角的成长弧光和变化历程
- 解决所有核心的矛盾与冲突
- 确保故事逻辑连贯，情节发展自然

**分段式结构要求：**
将整个故事划分为逻辑清晰的几个主要部分：
1. 开端（故事起始）
2. 发展（矛盾升级） - 可根据情节复杂性细分为多个阶段
3. 高潮（关键冲突）
4. 结局（问题解决）

**章节分配要求：**
- 为每个部分明确标注所占的章节范围
- 根据{num_chapters}章进行合理估算与分配
- 开端部分通常占总章节的15-25%
- 发展部分通常占总章节的50-65%
- 高潮部分通常占总章节的10-20%
- 结局部分通常占总章节的10-15%

**剧情梗概要求：**
每个部分的summary必须非常详细，至少包含300-500字的深度描述：
- **核心情节和主要事件**：详细叙述这一阶段发生的所有重要情节，包括具体的场景、对话要点、行动细节
- **重要转折点和关键冲突**：明确描述每个转折点的具体情况、冲突的性质、产生原因和影响后果
- **人物关系的变化和发展**：详细阐述主要角色之间关系的演变过程，包括情感变化、立场转换、联盟与对立
- **主角的成长轨迹和心理变化**：深入描述主角在这一阶段的内心世界、价值观变化、能力提升、性格发展
- **具体场景和环境描述**：说明主要事件发生的地点、时间、环境氛围
- **次要角色的作用**：描述配角在这一阶段的具体贡献和发展
- **伏笔和悬念设置**：说明为后续情节埋下的伏笔，以及制造的悬念点
- **与前后部分的逻辑衔接**：详细说明如何承接上一部分的结尾，以及如何为下一部分做铺垫

**具体内容要求：**
- **开端部分summary**：必须详细介绍主角的初始状态（身份、能力、处境、目标）、世界背景设定（时代、环境、规则、文化）、核心冲突的引入过程（如何发现问题、第一次遭遇、初始反应）、主要角色的登场方式、故事基调的确立
- **发展部分summary**：必须展现冲突的逐步升级过程、主角能力的提升轨迹、新角色的加入和作用、关键任务或挑战的具体描述、人物关系的复杂化、世界观的进一步展开、每个阶段的具体目标和障碍
- **高潮部分summary**：必须描述最激烈冲突的具体情况、关键转折的详细过程、主角面临的最大考验、所有前期铺垫的汇聚点、决定性战斗或对话的内容、角色的最终选择和代价
- **结局部分summary**：必须提供明确完整的结局描述、所有主要问题的解决方式、主角的最终状态和成就、次要角色的去向、世界的新秩序、留给读者的思考点或余韵

**质量保证要求：**
- 所有章节都被分配到某个部分，不能遗漏
- 各部分之间有良好的逻辑衔接和过渡
- 故事结构符合经典的起承转合模式
- **每个部分的summary必须详细且具体**，至少300-500字，避免空泛描述，要具体到场景、对话、行动
- **summary内容必须可操作**，为后续章节创作提供充分的细节指导
- 主角的成长弧光贯穿始终，在每个部分的summary中都要体现具体的变化
- 所有核心冲突都得到合理解决，在相应部分的summary中详细描述解决过程
- 确保创意的新鲜感，避免陈词滥调，在summary中体现独特的创意点
- 融入反转与惊奇的元素，在summary中明确指出反转的具体内容和时机
- **summary必须包含足够的情节细节**，能够直接指导章节内容的创作，不能只是概括性描述

## 开始创作：
现在，我已经为您详细阐述了小说大纲创作的完整要求和标准。请您基于上述的角色定位、背景与目标、以及详细的工作流程，运用您作为才华横溢的网络小说作家的专业能力，深入理解并消化所有信息。

**特别强调：每个部分的summary是整个大纲的核心**，必须写得非常详细（300-500字），包含具体的情节发展、场景描述、人物行动、对话要点、心理变化等。这些summary将直接用于后续的章节创作，因此必须提供足够的细节指导，不能只是概括性的描述。

**重要语言要求：**
- 必须使用中文输出所有内容
- JSON格式中的所有字段值都必须是中文
- 不得包含任何英文内容
- 确保符合中文表达习惯

当您完全理解并准备好按照这些要求创作出一份引人入胜、结构完整、富有创意的小说大纲时，请开始创作并直接返回JSON格式的大纲内容，不要添加任何前缀或后缀。请用中文回答。"""
        
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            user_content = current_provider.config.system_prompt + "\n\n" + user_content
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        logger.info("📤 发送故事大纲生成请求")
        response = self.create_completion_with_monitoring(messages)
        story_outline = self.extract_content_from_response(response)
        
        logger.info("✅ 故事大纲生成完成")
        logger.info(f"📊 故事大纲长度: {len(story_outline)}字符")
        
        return story_outline
    
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
    
    def write_first_chapter(self, plot: str, character_list: str, story_outline: str, 
                           first_chapter_title: str, writing_style: str) -> Tuple[str, Dict]:
        """写第一章，返回内容和Token统计"""
        logger.info("📝 开始写作第一章")
        logger.info(f"📖 章节标题: {first_chapter_title}")
        logger.info(f"✍️ 写作风格: {writing_style}")
        logger.info(f"📋 情节摘要: {plot[:200]}...")
        
        # 获取当前提供商的系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是一位世界级的网络小说作家。请严格按照提供的人物设定、故事大纲和情节发展来创作。"
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"""基于以下信息写这部小说的第一章：

情节：{plot}

人物列表：{character_list}

故事大纲：{story_outline}

本章标题：{first_chapter_title}

写作风格：{writing_style}

**第一章创作特殊要求：**
作为故事开篇，第一章需要：
1. 创造引人入胜的开头，瞬间抓住读者注意力
2. 巧妙介绍主要人物和背景设定，避免生硬的信息堆砌
3. 建立故事基调和氛围，让读者沉浸其中
4. 埋下伏笔和悬念，激发读者阅读兴趣
5. 展现主角的初始状态，为后续成长做铺垫
6. 通过生动的场景和对话推动情节发展
7. 确保开头具有冲击力，可以是动作场面、悬疑情节或引人深思的场景

请严格按照以下要求创作：
1. 严格按照故事大纲的开端部分发展
2. 确保人物行为符合角色设定
3. 体现指定的写作风格
4. 为后续章节做好铺垫
5. 只包含章节文本，无需重写章节名称
6. 请用中文回答

**重要格式要求：**
请将章节正文内容包装在以下标记中：
<CHAPTER_CONTENT>
这里是章节正文内容
</CHAPTER_CONTENT>

在标记外可以添加任何说明或分析，但正文内容必须在标记内。

创作第一章："""
        
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
        improvement_default_prompt = "你是一位世界级的网络小说作家。你的工作是拿你学生的第一章初稿，重写得更好，更详细。"
        improvement_user_content = f"""基于以下信息改进第一章：

情节：{plot}

人物列表：{character_list}

故事大纲：{story_outline}

学生的第一章初稿：{initial_chapter}

写作风格：{writing_style}

现在，重写这部小说的第一章，要比学生的版本好得多。请：
1. 严格按照故事大纲的开端部分发展
2. 确保人物行为符合角色设定
3. 应该更详细、更长、更引人入胜
4. 体现指定的写作风格
5. 保持与大纲的一致性
6. 强化开头的冲击力和吸引力
7. 增强场景描写和人物刻画的生动性
8. 请用中文回答

**重要格式要求：**
请将章节正文内容包装在以下标记中：
<CHAPTER_CONTENT>
这里是改进后的章节正文内容
</CHAPTER_CONTENT>

在标记外可以添加任何说明或分析，但正文内容必须在标记内。

改进后的第一章："""
        
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
    
    def write_chapter(self, previous_chapters: str, plot: str, character_list: str, story_outline: str, 
                     chapter_title: str, current_chapter_storyline: str, writing_style: str = "", 
                     next_5_chapters: str = "", current_chapter_num: int = 1, total_chapters: int = 10) -> Tuple[str, Dict]:
        """写章节，返回内容和Token统计"""
        logger.info(f"📝 开始写作章节：{chapter_title} ({current_chapter_num}/{total_chapters})")
        logger.info(f"📊 上下文长度: {len(previous_chapters)}字符")
        logger.info(f"📋 情节长度: {len(plot)}字符")
        
        # 获取当前提供商的系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = "你是一位世界级的网络小说作家。请严格按照提供的人物设定、故事大纲和章节故事线来创作。"
        
        # 判断章节类型并添加特殊要求
        special_requirements = ""
        if current_chapter_num == total_chapters:
            # 最后一章
            special_requirements = """**最后一章特殊要求：**
这是故事的最后一章，需要：
1. 完美收尾所有主要情节线，解决所有核心冲突
2. 展现主角的最终成长和变化
3. 给出令人满意的结局，回应读者的期待
4. 体现故事的主题和深层意义
5. 营造恰当的结束感，让读者感到完整和满足
6. 可以留下适当的余韵，但不能有重大悬念未解决
7. 在章节结尾明确表示故事完结

"""
        elif current_chapter_num >= total_chapters - 1:
            # 倒数第二章
            special_requirements = """**倒数第二章特殊要求：**
这是故事即将结束的关键章节，需要：
1. 将主要冲突推向最终高潮
2. 为最后一章的大结局做充分铺垫
3. 开始收束次要情节线
4. 展现主角面对最终挑战的决心和能力
5. 营造紧张感，让读者急于看到结局
6. 避免引入新的重大冲突或角色

"""
        elif current_chapter_num <= 2:
            # 前两章
            special_requirements = """**开头章节特殊要求：**
这是故事的开始阶段，需要：
1. 继续深入建立世界观和角色关系
2. 推动主要冲突的发展
3. 保持读者的阅读兴趣
4. 为中期发展做好铺垫
5. 平衡世界观介绍和情节推进

"""
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"""基于以下信息写这部小说的下一章：

情节：{plot}

人物列表：{character_list}

故事大纲：{story_outline}

前面的章节：{previous_chapters}

本章标题：{chapter_title}

本章故事线：{current_chapter_storyline}

写作风格：{writing_style}

{next_5_chapters}

{special_requirements}

请严格按照以下要求创作：
1. 严格按照故事大纲的相应部分发展
2. 确保人物行为符合角色设定
3. 按照本章故事线的具体要求写作
4. 保持与前面章节的逻辑衔接
5. 为后续章节做好铺垫
6. 只包含章节文本，无需重写章节名称
7. 请用中文回答

**重要格式要求：**
请将章节正文内容包装在以下标记中：
<CHAPTER_CONTENT>
这里是章节正文内容
</CHAPTER_CONTENT>

在标记外可以添加任何说明或分析，但正文内容必须在标记内。

创作本章："""
        
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
    
    def clean_json_response(self, response: str) -> str:
        """清理AI响应，提取有效的JSON内容"""
        import re
        import json
        
        try:
            # 移除前后的空白字符
            response = response.strip()
            
            # 尝试提取JSON代码块
            json_pattern = r'```json\s*(.*?)\s*```'
            json_match = re.search(json_pattern, response, re.DOTALL)
            
            if json_match:
                response = json_match.group(1).strip()
                logger.info("✅ 从代码块中提取到JSON内容")
            
            # 移除可能的前缀文字
            lines = response.split('\n')
            json_start = -1
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('[') or line.startswith('{'):
                    json_start = i
                    break
            
            if json_start > 0:
                response = '\n'.join(lines[json_start:])
                logger.info(f"✅ 移除了{json_start}行前缀文字")
            
            # 找到JSON结束位置
            json_end = -1
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i].strip()
                if line.endswith(']') or line.endswith('}'):
                    json_end = i
                    break
            
            if json_end >= 0 and json_end < len(lines) - 1:
                response = '\n'.join(lines[:json_end + 1])
                logger.info(f"✅ 移除了{len(lines) - json_end - 1}行后缀文字")
            
            # 验证JSON格式
            parsed = json.loads(response)
            logger.info("✅ JSON格式验证成功")
            
            return response
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON解析失败: {e}")
            # 尝试修复常见的JSON错误
            try:
                # 移除可能的尾随逗号
                response = re.sub(r',\s*([}\]])', r'\1', response)
                # 确保键名用双引号
                response = re.sub(r'(\w+):', r'"\1":', response)
                
                # 再次验证
                parsed = json.loads(response)
                logger.info("✅ JSON修复成功")
                return response
            except:
                logger.error("❌ JSON修复失败，返回原始内容")
                return response
        except Exception as e:
            logger.error(f"❌ 清理JSON响应时发生错误: {e}")
            return response
    
    def generate_storyline_batch(self, plot: str, character_list: str, story_outline: str, 
                               start_chapter: int, end_chapter: int, previous_chapters: str = "") -> str:
        """生成指定章节范围的故事线"""
        logger.info(f"📝 生成第{start_chapter}-{end_chapter}章的详细故事线...")
        
        # 获取系统提示词
        current_provider = self.config_manager.provider_manager.get_provider()
        default_system_prompt = """你是一位世界级的网络小说作家，专门负责创建详细的章节故事线。

你的任务是根据提供的信息，生成结构化的章节故事线，必须严格按照JSON格式输出。

要求：
1. 输出必须是有效的JSON数组格式
2. 每个章节使用字典结构，包含章节标题和详细内容
3. 不要添加任何前缀、后缀或解释文字
4. 专注于故事情节的逻辑发展和人物塑造"""
        
        # 构建 user 提示词：用户系统提示词 + 原始提示词
        user_content = f"""基于以下信息为第{start_chapter}-{end_chapter}章创建详细的故事线：

**情节设定：**
{plot}

**人物列表：**
{character_list}

**故事大纲：**
{story_outline}

**前面章节信息：**
{previous_chapters}

请为第{start_chapter}-{end_chapter}章创建详细的故事线，确保：
1. 严格按照故事大纲的结构发展
2. 人物行为符合角色设定
3. 与前面章节保持逻辑衔接
4. 每章包含具体的情节发展、人物互动和关键事件
5. 注意章节间的过渡和连贯性

**输出格式要求：**
必须返回有效的JSON数组，格式如下：
```json
[
  {{
    "第{start_chapter}章 - 章节标题": "详细的章节故事线内容，包括主要情节发展、人物互动、关键事件和场景描述"
  }},
  {{
    "第{start_chapter+1}章 - 章节标题": "详细的章节故事线内容..."
  }}
]
```

**重要说明：**
- 只返回JSON数组，不要任何前缀或后缀
- 章节标题要有意义，体现该章节的核心内容
- 每章内容要详细，包含情节发展和人物动向
- 确保JSON格式正确，可以被解析"""
        
        # 对于故事线生成，需要特别处理系统提示词以避免冲突
        if current_provider.config.system_prompt and current_provider.config.system_prompt.strip():
            provider_prompt = current_provider.config.system_prompt
            # 如果系统提示词包含字数要求，需要在故事线生成时忽略
            if "MINIMUM_WORD_COUNT" in provider_prompt or "minimum word" in provider_prompt.lower():
                logger.warning("⚠️ 检测到系统提示词包含字数要求，在故事线生成时将忽略以确保JSON格式正确")
                # 保留创意相关的部分，但移除字数限制
                modified_prompt = provider_prompt.split("MINIMUM_WORD_COUNT")[0].strip()
                if modified_prompt:
                    # 只在没有冲突的情况下添加用户系统提示词
                    if not any(keyword in modified_prompt.lower() for keyword in ["json", "格式", "format"]):
                        user_content = modified_prompt + "\n\n" + user_content
            else:
                # 检查系统提示词是否与JSON格式要求冲突
                if not any(keyword in provider_prompt.lower() for keyword in ["json", "格式", "format"]):
                    user_content = provider_prompt + "\n\n" + user_content
        
        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = self.create_completion_with_monitoring(messages)
        raw_content = self.extract_content_from_response(response)
        
        # 尝试清理和提取JSON内容
        cleaned_content = self.clean_json_response(raw_content)
        return cleaned_content
    
    def generate_storyline(self, plot: str, character_list: str, story_outline: str, num_chapters: int) -> str:
        """生成完整故事线 - 支持多API调用"""
        logger.info(f"📚 开始生成{num_chapters}章的完整故事线...")
        logger.info(f"📊 超过10章，将使用分批生成模式" if num_chapters > 10 else "📊 10章以内，使用单次生成模式")
        
        if num_chapters <= 10:
            # 10章以内，使用单次生成
            return self.generate_storyline_batch(plot, character_list, story_outline, 1, num_chapters)
        
        # 超过10章，使用分批生成
        all_chapters = []
        batch_size = 10
        previous_chapters_summary = ""
        
        for start_chapter in range(1, num_chapters + 1, batch_size):
            end_chapter = min(start_chapter + batch_size - 1, num_chapters)
            
            logger.info(f"📝 正在生成第{start_chapter}-{end_chapter}章...")
            
            # 为当前批次生成故事线
            current_batch = self.generate_storyline_batch(
                plot, character_list, story_outline, 
                start_chapter, end_chapter, previous_chapters_summary
            )
            
            # 解析当前批次的章节
            try:
                import json
                current_chapters = json.loads(current_batch)
                all_chapters.extend(current_chapters)
                
                # 更新前面章节的摘要，为下一批次提供上下文
                if end_chapter < num_chapters:
                    # 创建前面章节的摘要
                    chapter_summaries = []
                    for chapter_data in current_chapters:
                        for title, content in chapter_data.items():
                            chapter_summaries.append(f"{title}: {content[:200]}...")
                    
                    previous_chapters_summary = f"前面章节概述：\n" + "\n".join(chapter_summaries)
                    
                    # 限制摘要长度避免token过多
                    if len(previous_chapters_summary) > 3000:
                        previous_chapters_summary = previous_chapters_summary[:3000] + "..."
                
                logger.info(f"✅ 第{start_chapter}-{end_chapter}章故事线生成完成")
                
            except Exception as e:
                logger.error(f"❌ 解析第{start_chapter}-{end_chapter}章故事线失败: {e}")
                logger.info(f"📝 重试生成第{start_chapter}-{end_chapter}章...")
                
                # 重试一次
                try:
                    time.sleep(2)
                    retry_batch = self.generate_storyline_batch(
                        plot, character_list, story_outline, 
                        start_chapter, end_chapter, previous_chapters_summary
                    )
                    current_chapters = json.loads(retry_batch)
                    all_chapters.extend(current_chapters)
                    logger.info(f"✅ 重试成功：第{start_chapter}-{end_chapter}章故事线生成完成")
                    
                    # 更新前面章节的摘要
                    if end_chapter < num_chapters:
                        chapter_summaries = []
                        for chapter_data in current_chapters:
                            for title, content in chapter_data.items():
                                chapter_summaries.append(f"{title}: {content[:200]}...")
                        
                        previous_chapters_summary = f"前面章节概述：\n" + "\n".join(chapter_summaries)
                        
                        if len(previous_chapters_summary) > 3000:
                            previous_chapters_summary = previous_chapters_summary[:3000] + "..."
                    
                except Exception as retry_e:
                    logger.error(f"❌ 重试仍失败: {retry_e}")
                    # 使用增强的备用格式，包含基本的章节结构
                    fallback_chapters = []
                    
                    # 定义章节发展阶段模板
                    chapter_templates = {
                        1: "开篇引入，介绍主要背景和核心人物",
                        2: "深入展开设定，建立人物关系",
                        3: "初步冲突出现，推动情节发展",
                        4: "人物成长，背景扩展",
                        5: "矛盾加剧，情节复杂化",
                        6: "转折点出现，改变故事走向",
                        7: "高潮准备，积累张力",
                        8: "关键冲突，重要选择",
                        9: "情节高潮，决定性时刻",
                        10: "结局收尾，解决冲突"
                    }
                    
                    for i in range(start_chapter, end_chapter + 1):
                        chapter_title = f"第{i}章 - 待完善"
                        
                        # 基于章节位置生成不同的内容模板
                        if i <= 2:
                            phase = "开篇阶段"
                            content_hint = "重点介绍主要人物和世界设定，为后续发展做铺垫"
                        elif i <= 4:
                            phase = "发展阶段"
                            content_hint = "深入展开人物关系和背景设定，初步引入冲突"
                        elif i <= 6:
                            phase = "推进阶段"
                            content_hint = "矛盾和冲突逐渐显现，情节开始复杂化"
                        elif i <= 8:
                            phase = "高潮准备"
                            content_hint = "积累张力，为即将到来的高潮做准备"
                        else:
                            phase = "高潮收尾"
                            content_hint = "解决主要冲突，推向故事结局"
                        
                        # 获取章节特定模板
                        template_hint = chapter_templates.get(i % 10 + 1, "继续推进主要情节")
                        
                        chapter_content = f"第{i}章处于{phase}，{content_hint}。\n\n本章发展方向：{template_hint}。"
                        
                        if plot:
                            chapter_content += f"\n\n结合主要剧情背景：{plot[:150]}..."
                        
                        if i == start_chapter and previous_chapters_summary:
                            chapter_content += f"\n\n承接前文发展：{previous_chapters_summary[:200]}..."
                        
                        # 添加章节特有的发展提示
                        if i % 5 == 1:
                            chapter_content += "\n\n💡 建议：本章可以引入新的人物或场景。"
                        elif i % 5 == 3:
                            chapter_content += "\n\n💡 建议：本章可以深化主要冲突或揭示关键信息。"
                        elif i % 5 == 0:
                            chapter_content += "\n\n💡 建议：本章可以作为阶段性高潮或转折点。"
                        
                        fallback_chapters.append({chapter_title: chapter_content})
                    
                    all_chapters.extend(fallback_chapters)
                    logger.info(f"⚠️ 已为第{start_chapter}-{end_chapter}章生成差异化备用内容结构")
            
            # 添加延迟避免API限制
            if end_chapter < num_chapters:
                logger.info("⏳ 等待5秒后继续下一批次...")
                time.sleep(5)
        
        # 合并所有章节
        final_storyline = json.dumps(all_chapters, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 完整故事线生成完成")
        logger.info(f"📊 总章节数: {len(all_chapters)}")
        logger.info(f"📊 故事线长度: {len(final_storyline)}字符")
        
        return final_storyline
    
    def generate_complete_outline(self, prompt: str, num_chapters: int, writing_style: str = "") -> Dict[str, str]:
        """生成完整的创作大纲，包括剧情、人物列表、故事大纲和故事线"""
        logger.info(f"🎯 开始生成完整创作大纲 - {num_chapters}章")
        
        # 生成情节
        logger.info("📖 第1步：生成情节...")
        plots = self.generate_plots(prompt)
        best_plot = self.select_most_engaging(plots)
        improved_plot = self.improve_plot(best_plot)
        
        # 生成人物列表
        logger.info("👥 第2步：生成人物列表...")
        character_list = self.generate_character_list(improved_plot, num_chapters)
        
        # 生成故事大纲
        logger.info("📋 第3步：生成故事大纲...")
        story_outline = self.generate_story_outline(improved_plot, character_list, num_chapters)
        
        # 生成故事线
        logger.info("📝 第4步：生成详细故事线...")
        storyline = self.generate_storyline(improved_plot, character_list, story_outline, num_chapters)
        
        # 生成标题
        logger.info("📚 第5步：生成小说标题...")
        title = self.get_title(improved_plot)
        
        logger.info("✅ 完整创作大纲生成完成！")
        
        return {
            "title": title,
            "plot": improved_plot,
            "character_list": character_list,
            "story_outline": story_outline,
            "storyline": storyline
        }
    
    def write_novel_from_outline(self, outline_data: Dict[str, str], num_chapters: int, writing_style: str,
                               provider_name: str = None, model_name: str = None) -> Tuple[str, str, List[str], List[Dict]]:
        """基于已生成的大纲创作小说"""
        logger.info(f"📝 开始基于大纲创作{num_chapters}章小说")
        
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
            # 从大纲数据中提取信息
            title = outline_data["title"]
            improved_plot = outline_data["plot"]
            character_list = outline_data["character_list"]
            story_outline = outline_data["story_outline"]
            storyline = outline_data["storyline"]
            
            logger.info(f"📚 使用标题: {title}")
            logger.info(f"📝 使用已生成的大纲数据创作小说")
            
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
            
            logger.info(f'章节标题: {len(chapter_titles)}个')
            
            # 写第一章
            first_chapter, first_chapter_tokens = self.write_first_chapter(
                improved_plot, character_list, story_outline, 
                str(chapter_titles[0]), writing_style.strip()
            )
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
            
            # 写其余章节 - 使用增强的上下文构建
            for i in range(num_chapters - 1):
                current_chapter_index = i + 1  # 当前要写的章节索引（0-based）
                logger.info(f"正在写第 {current_chapter_index + 1} 章...")
                time.sleep(10)  # 减少等待时间
                
                # 构建优化的上下文（使用过去5章摘要 + 过去1章全文）
                optimized_context = self.build_optimized_context(novel_id, current_chapter_index, recent_chapters_count=1, summary_chapters_count=5)
                
                # 从故事线中提取当前章节和后续章节的信息
                current_storyline, next_chapters_context = self.extract_chapter_context(storyline, current_chapter_index + 1)
                
                # 写章节时使用增强的上下文
                chapter, chapter_tokens = self.write_chapter(
                    optimized_context, improved_plot, character_list, story_outline,
                    str(chapter_titles[i + 1]), current_storyline, writing_style.strip(),
                    next_chapters_context, current_chapter_index + 1, num_chapters  # 传递章节位置信息
                )
                
                # 检查章节长度
                if len(str(chapter)) < 100:
                    logger.warning('章节长度不足，重新生成...')
                    time.sleep(10)
                    chapter, chapter_tokens = self.write_chapter(
                        optimized_context, improved_plot, character_list, story_outline,
                        str(chapter_titles[i + 1]), current_storyline, next_chapters_context,
                        current_chapter_index + 1, num_chapters  # 传递章节位置信息
                    )
                
                # 如果是最后一章，添加"全文完"
                if current_chapter_index == num_chapters - 1:
                    chapter = chapter.rstrip() + "\n\n（全文完）"
                    logger.info("✅ 已在最后一章添加'全文完'标记")
                
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
            logger.error(f"基于大纲创作小说时发生错误: {e}")
            raise
    
    def extract_chapter_context(self, storyline: str, current_chapter: int) -> Tuple[str, str]:
        """从故事线中提取当前章节和后续章节的信息"""
        try:
            import json
            chapters = json.loads(storyline)
            
            # 获取当前章节故事线
            current_storyline = ""
            if current_chapter <= len(chapters):
                chapter_data = chapters[current_chapter - 1]
                for title, content in chapter_data.items():
                    current_storyline = f"{title}：{content}"
                    break
            
            # 获取后续5章的故事线
            next_chapters = []
            for i in range(current_chapter, min(current_chapter + 5, len(chapters))):
                chapter_data = chapters[i]
                for title, content in chapter_data.items():
                    next_chapters.append(f"{title}：{content}")
                    break
            
            next_chapters_text = ""
            if next_chapters:
                next_chapters_text = f"后续章节概况：\n" + "\n".join(next_chapters)
            
            return current_storyline, next_chapters_text
            
        except Exception as e:
            logger.warning(f"提取章节上下文失败: {e}")
            return f"第{current_chapter}章", ""
    
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
            cleaned_content = self.clean_response_content(content)
            
            # 提取结构化的章节内容
            structured_content = self.extract_structured_chapter_content(cleaned_content)
            
            return structured_content
            
        except Exception as e:
            logger.error(f"提取响应内容失败: {e}")
            return str(response)
    
    def extract_structured_chapter_content(self, content: str) -> str:
        """从响应中提取结构化的章节内容"""
        if not isinstance(content, str):
            content = str(content)
        
        import re
        
        # 尝试提取<CHAPTER_CONTENT>标签内的内容
        chapter_pattern = r'<CHAPTER_CONTENT>(.*?)</CHAPTER_CONTENT>'
        match = re.search(chapter_pattern, content, re.DOTALL)
        
        if match:
            extracted_content = match.group(1).strip()
            logger.info("✅ 成功提取结构化章节内容")
            logger.info(f"📊 结构化内容长度: {len(extracted_content)}字符")
            return extracted_content
        else:
            logger.warning("⚠️ 未找到结构化章节标记，使用原始内容")
            logger.info("💡 尝试智能提取章节内容...")
            
            # 备用方案：尝试智能提取章节内容
            return self.smart_extract_chapter_content(content)
    
    def smart_extract_chapter_content(self, content: str) -> str:
        """智能提取章节内容的备用方案"""
        import re
        
        # 移除常见的非正文内容
        # 1. 移除"分析"、"总结"等分析性内容
        analysis_patterns = [
            r'分析[:：].*?(?=\n\n|\n[^分析总结说明]|\Z)',
            r'总结[:：].*?(?=\n\n|\n[^分析总结说明]|\Z)',
            r'说明[:：].*?(?=\n\n|\n[^分析总结说明]|\Z)',
            r'本章要点[:：].*?(?=\n\n|\n[^本章要点]|\Z)',
            r'写作思路[:：].*?(?=\n\n|\n[^写作思路]|\Z)',
            r'这是.*?的章节内容[:：]?\s*',
            r'根据.*?要求创作.*?[:：]?\s*',
            r'这个章节.*?(?=\n\n|\Z)',
            r'以上.*?内容.*?(?=\n\n|\Z)',
        ]
        
        for pattern in analysis_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # 2. 移除明显的元数据行和段落
        metadata_patterns = [
            r'^(字数[:：]|Word count:).*$',
            r'^(创作时间[:：]|Created:).*$',
            r'^(作者[:：]|Author:).*$',
            r'^(版权[:：]|Copyright:).*$',
            r'^(备注[:：]|Note:).*$',
            r'\n(字数[:：]|Word count:).*?(?=\n|$)',
            r'\n(创作时间[:：]|Created:).*?(?=\n|$)',
            r'字数[:：].*?(?=\n|$)',
            r'创作时间[:：].*?(?=\n|$)',
        ]
        
        for pattern in metadata_patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
        
        # 3. 移除多余的空行
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = content.strip()
        
        # 4. 如果内容以明显的正文开头，保留它
        story_start_chars = '"\'\'"《「'
        if content and (content[0].isalnum() or content[0] in story_start_chars):
            logger.info("✅ 智能提取章节内容成功")
            logger.info(f"📊 智能提取内容长度: {len(content)}字符")
            return content
        
        # 5. 如果以上都不行，返回原始内容但记录警告
        logger.warning("⚠️ 智能提取也未能完美识别章节内容，返回清理后的原始内容")
        return content
    
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
        """写网络小说"""
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
            
            # 生成人物列表
            character_list = self.generate_character_list(improved_plot, num_chapters)
            logger.info(f'生成的人物列表: {character_list[:300]}...')
            
            # 生成故事大纲
            story_outline = self.generate_story_outline(improved_plot, character_list, num_chapters)
            logger.info(f'生成的故事大纲: {story_outline[:300]}...')
            
            # 生成故事线
            storyline = self.generate_storyline(improved_plot, character_list, story_outline, num_chapters)
            logger.info(f'生成的故事线: {storyline[:300]}...')
            
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
            first_chapter, first_chapter_tokens = self.write_first_chapter(
                improved_plot, character_list, story_outline, 
                str(chapter_titles[0]), writing_style.strip()
            )
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
            
            # 写其余章节 - 使用增强的上下文构建
            for i in range(num_chapters - 1):
                current_chapter_index = i + 1  # 当前要写的章节索引（0-based）
                logger.info(f"正在写第 {current_chapter_index + 1} 章...")
                time.sleep(10)  # 减少等待时间
                
                # 构建优化的上下文（使用过去5章摘要 + 过去1章全文）
                optimized_context = self.build_optimized_context(novel_id, current_chapter_index, recent_chapters_count=1, summary_chapters_count=5)
                
                # 从故事线中提取当前章节和后续章节的信息
                current_storyline, next_chapters_context = self.extract_chapter_context(storyline, current_chapter_index + 1)
                
                # 写章节时使用增强的上下文
                chapter, chapter_tokens = self.write_chapter(
                    optimized_context, improved_plot, character_list, story_outline,
                    str(chapter_titles[i + 1]), current_storyline, writing_style.strip(),
                    next_chapters_context, current_chapter_index + 1, num_chapters  # 传递章节位置信息
                )
                
                # 检查章节长度
                if len(str(chapter)) < 100:
                    logger.warning('章节长度不足，重新生成...')
                    time.sleep(10)
                    chapter, chapter_tokens = self.write_chapter(
                        optimized_context, improved_plot, character_list, story_outline,
                        str(chapter_titles[i + 1]), current_storyline, next_chapters_context,
                        current_chapter_index + 1, num_chapters  # 传递章节位置信息
                    )
                
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