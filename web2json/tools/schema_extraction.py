"""
Schema提取和合并工具
从HTML和视觉两个维度提取Schema，并进行合并
"""
import json
import re
from typing import Dict, List
from loguru import logger
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import os

from web2json.config.settings import settings
from web2json.prompts.schema_extraction import SchemaExtractionPrompts
from web2json.prompts.schema_merge import SchemaMergePrompts


def _parse_llm_response(response: str) -> Dict:
    """解析模型响应中的JSON"""
    import tempfile
    from pathlib import Path

    def try_fix_json(json_str: str) -> str:
        """尝试修复常见的JSON格式问题"""
        # 修复：缺少逗号（对象内）
        json_str = re.sub(r'"\s*\n\s*"', '",\n  "', json_str)

        # 修复：对象后缺少逗号
        json_str = re.sub(r'}\s*\n\s*"', '},\n  "', json_str)

        # 修复：尾随逗号
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        return json_str

    try:
        # 尝试提取JSON代码块
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败，尝试修复: {str(e)}")
                # 尝试修复JSON
                fixed_json = try_fix_json(json_str)
                try:
                    return json.loads(fixed_json)
                except:
                    logger.debug(f"修复后的JSON: {fixed_json[:1000]}")
                    raise

        # 尝试提取普通JSON
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            json_str = match.group()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                fixed_json = try_fix_json(json_str)
                return json.loads(fixed_json)

        # 直接解析
        return json.loads(response)
    except Exception as e:
        logger.error(f"解析模型响应失败: {str(e)}")

        # 保存完整响应到临时文件，便于调试
        try:
            temp_dir = Path("logs/llm_responses")
            temp_dir.mkdir(parents=True, exist_ok=True)
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = temp_dir / f"error_response_{timestamp}.txt"
            error_file.write_text(response, encoding='utf-8')
            logger.error(f"完整响应已保存到: {error_file}")
        except:
            pass

        logger.debug(f"原始响应（前1000字符）: {response[:1000]}")
        raise Exception(f"解析模型响应失败: {str(e)}")


@tool
def extract_schema_from_html(html_content: str) -> Dict:
    """
    从HTML内容中提取Schema

    包含字段名、字段说明、字段值示例、xpath路径

    Args:
        html_content: HTML内容

    Returns:
        dict: 包含xpath的Schema
    """
    try:
        logger.info("正在从HTML提取Schema...")

        # 1. 获取Prompt
        prompt = SchemaExtractionPrompts.get_html_extraction_prompt()

        # 2. 调用LLM
        model = ChatOpenAI(
            model=settings.default_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            temperature=0.1
        )

        messages = [
            {"role": "system", "content": "你是一个专业的HTML分析专家。"},
            {"role": "user", "content": f"{prompt}\n\n## HTML内容\n\n```html\n{html_content[:50000]}\n```"}
        ]

        response = model.invoke(messages)

        # 3. 解析响应
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)

        result = _parse_llm_response(content)

        logger.success(f"成功从HTML提取 {len(result)} 个字段")
        return result

    except Exception as e:
        import traceback
        error_msg = f"HTML Schema提取失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise Exception(error_msg)


@tool
def extract_schema_from_image(image_path: str) -> Dict:
    """
    从网页截图中提取Schema

    包含字段名、字段说明、字段值示例、视觉描述

    Args:
        image_path: 截图文件路径

    Returns:
        dict: 包含视觉描述的Schema
    """
    try:
        logger.info(f"正在从截图提取Schema: {image_path}")

        # 1. 图片转base64
        import base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # 2. 获取Prompt
        prompt = SchemaExtractionPrompts.get_visual_extraction_prompt()

        # 3. 调用视觉模型
        model = ChatOpenAI(
            model=settings.vision_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            temperature=0.1
        )

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

        # 4. 解析响应
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)

        result = _parse_llm_response(content)

        logger.success(f"成功从截图提取 {len(result)} 个字段")
        return result

    except Exception as e:
        import traceback
        error_msg = f"视觉Schema提取失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise Exception(error_msg)


@tool
def merge_html_and_visual_schema(html_schema: Dict, visual_schema: Dict) -> Dict:
    """
    合并单个HTML的两种Schema

    判断相同字段并合并xpath和visual_features

    Args:
        html_schema: 从HTML提取的Schema（包含xpath）
        visual_schema: 从视觉提取的Schema（包含visual_features）

    Returns:
        dict: 合并后的Schema
    """
    try:
        logger.info("正在合并HTML和视觉Schema...")

        # 1. 获取Prompt
        prompt = SchemaMergePrompts.get_merge_single_schema_prompt(
            html_schema, visual_schema
        )

        # 2. 调用LLM
        model = ChatOpenAI(
            model=settings.default_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            temperature=0.1
        )

        messages = [
            {"role": "system", "content": "你是一个专业的Schema合并专家。"},
            {"role": "user", "content": prompt}
        ]

        response = model.invoke(messages)

        # 3. 解析响应
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)

        result = _parse_llm_response(content)

        logger.success(f"成功合并Schema，包含 {len(result)} 个字段")
        return result

    except Exception as e:
        import traceback
        error_msg = f"Schema合并失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise Exception(error_msg)


@tool
def merge_multiple_schemas(schemas: List[Dict]) -> Dict:
    """
    合并多个HTML的Schema

    进行筛选、合并、修正，输出最终Schema

    Args:
        schemas: 多个HTML的Schema列表

    Returns:
        dict: 最终合并后的Schema
    """
    try:
        logger.info(f"正在合并 {len(schemas)} 个Schema...")

        # 1. 获取Prompt
        prompt = SchemaMergePrompts.get_merge_multiple_schemas_prompt(schemas)

        # 2. 调用LLM
        model = ChatOpenAI(
            model=settings.default_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            temperature=0.1
        )

        messages = [
            {"role": "system", "content": "你是一个专业的Schema整合专家。"},
            {"role": "user", "content": prompt}
        ]

        response = model.invoke(messages)

        # 3. 解析响应
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)

        result = _parse_llm_response(content)

        logger.success(f"成功合并多个Schema，最终包含 {len(result)} 个字段")
        return result

    except Exception as e:
        import traceback
        error_msg = f"多Schema合并失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise Exception(error_msg)
