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


def _image_to_base64(image_path: str) -> str:
    """读取图片并转 Base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _build_prompt() -> str:
    """构建视觉模型提示词"""
    return """
请仔细观察整张网页截图，识别并提取页面中的关键信息字段。

你需要：
1. 自主判断页面类型（如：文章页、列表页、商品页、表单页等）
2. 识别页面中存在的关键字段（例如标题、日期、正文等），非关键信息（例如导航栏、页脚、图片广告等）请忽略
3. value字段提取实际值，不要生成页面不存在的内容
4. 为每个识别到的字段提取内容，如果内容过长可以适当截断

返回 JSON 格式如下：

{
  "字段名1": {
    "type": "string|number|array|object",
    "description": "字段语义（中文）",
    "value": "实际提取值",
    "confidence": 0.95
  }
}

要求：
1. **只返回纯JSON，不要使用markdown代码块标记（不要用 ```json 或 ```）**
2. 无任何解释文本，直接从 { 开始
3. 字段名必须使用英文 snake_case
4. 每个字段必须有 type / description / value / confidence
"""


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

        # 2. 构建提示词
        prompt = _build_prompt()

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