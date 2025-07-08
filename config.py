from openai import OpenAI
import os
import uuid
from dotenv import load_dotenv

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff


# 加载.env文件中的环境变量
load_dotenv()

llm_model_name = "gpt-3.5-turbo-16k"


# OpenAI客户端将在需要时初始化
openai_client = None

stability_api_key = os.getenv("STABILITY_API_KEY")  # get it at https://beta.dreamstudio.ai/
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")  # optional, if you don't add it, keep it as "YOUR ANTHROPIC API KEY"


def get_openai_client():
    """获取OpenAI客户端，延迟初始化"""
    global openai_client
    if openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # 如果没有API密钥，使用占位符避免错误
            api_key = "placeholder-key"
        
        base_url = os.getenv("OPENAI_API_BASE")
        openai_client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    return openai_client


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion_with_backoff(**kwargs):
    # 检查是否有有效的API密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "placeholder-key":
        raise ValueError("OpenAI API密钥未设置。请在.env文件中设置OPENAI_API_KEY。")
    
    # 使用新版OpenAI API
    client = get_openai_client()
    response = client.chat.completions.create(**kwargs)
    # 转换为旧版格式以保持兼容性
    return {
        'choices': [
            {
                'message': {
                    'content': response.choices[0].message.content
                }
            }
        ]
    }


# 生成32位唯一的uuid
def generate_uuid():
    # 生成UUID
    id = uuid.uuid4().hex
    return id


# 保存小说每章节的内容
def save_novel_chapter(novel_id, chapter_index, file_name, file_content):
    # 创建章节文件目录
    chapter_folder = os.path.join(os.getcwd(), f"story/{novel_id}/chapter_{chapter_index + 1}")
    if not os.path.exists(chapter_folder):
        os.makedirs(chapter_folder)

    # 写入章节内容到文件
    file_path = os.path.join(chapter_folder, f"{file_name}.txt")
    with open(file_path, "w") as file:
        file.write(file_content)