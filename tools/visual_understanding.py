"""
图片 → JSON 结构化信息提取工具
从网页截图中提取结构化信息
"""
import json
import base64
import re
from typing import Dict
from loguru import logger
from langchain_core.tools import tool
from config.settings import settings
from prompts.visual_understanding import VisualUnderstandingPrompts


def _image_to_base64(image_path: str) -> str:
    """读取图片并转 Base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _parse_llm_response(response: str) -> Dict:
    """解析模型响应中的 JSON"""
    try:
        # 尝试提取JSON
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(response)
    except Exception as e:
        logger.error(f"解析模型响应失败: {str(e)}")
        raise Exception(f"解析模型响应失败: {str(e)}")


@tool
def extract_json_from_image(image_path: str) -> Dict:
    """
    从网页截图中提取结构化页面信息

    Args:
        image_path: 图片文件路径

    Returns:
        dict: 模型解析得到的结构化 JSON
    """
    try:
        logger.info(f"正在从图片提取结构化信息: {image_path}")

        # 1. 图片转 base64
        image_data = _image_to_base64(image_path)

        # 2. 使用 Prompt 模块构建提示词
        prompt = VisualUnderstandingPrompts.get_extraction_prompt()

        # 3. 使用 LangChain 1.0 的 ChatOpenAI
        from langchain_openai import ChatOpenAI
        import os

        model = ChatOpenAI(
            model=settings.vision_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            temperature=settings.vision_temperature
        )

        # 4. 调用视觉模型
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"}
                    }
                ]
            }
        ]

        response = model.invoke(messages)

        # 5. 提取 JSON
        # 处理不同类型的响应
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)

        result = _parse_llm_response(content)

        logger.success(f"成功提取 {len(result)} 个字段")
        return result

    except Exception as e:
        import traceback
        error_msg = f"图片处理失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise Exception(error_msg)


@tool
def refine_schema_from_image(image_path: str, previous_schema: Dict) -> Dict:
    """
    基于新的网页截图，迭代优化已有的JSON Schema

    Args:
        image_path: 图片文件路径
        previous_schema: 上一轮的Schema

    Returns:
        dict: 优化后的完整Schema
    """
    try:
        logger.info(f"正在基于新截图优化Schema: {image_path}")

        # 1. 图片转 base64
        image_data = _image_to_base64(image_path)

        # 2. 使用Schema迭代Prompt
        prompt = VisualUnderstandingPrompts.get_schema_refinement_prompt(previous_schema)

        # 3. 使用 LangChain 1.0 的 ChatOpenAI
        from langchain_openai import ChatOpenAI
        import os

        model = ChatOpenAI(
            model=settings.vision_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            temperature=settings.vision_temperature
        )

        # 4. 调用视觉模型
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"}
                    }
                ]
            }
        ]

        response = model.invoke(messages)

        # 5. 提取 JSON
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)

        result = _parse_llm_response(content)

        logger.success(f"Schema优化完成，当前包含 {len(result)} 个字段")
        return result

    except Exception as e:
        import traceback
        error_msg = f"Schema优化失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise Exception(error_msg)