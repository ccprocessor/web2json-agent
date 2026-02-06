"""
Schema提取和合并工具
从HTML和视觉两个维度提取Schema，并进行合并
"""
import json
import re
from typing import Dict, List
from loguru import logger
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

        return result

    except Exception as e:
        import traceback
        error_msg = f"HTML Schema提取失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise Exception(error_msg)


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

        return result

    except Exception as e:
        import traceback
        error_msg = f"多Schema合并失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise Exception(error_msg)


def enrich_schema_with_xpath(schema_template: Dict, html_content: str) -> Dict:
    """
    为预定义的Schema模板补充xpath和value_sample信息

    用于预定义模式，保持用户定义的字段key不变，只补充技术细节

    Args:
        schema_template: 预定义的Schema模板（包含字段key、type、description）
        html_content: HTML内容

    Returns:
        dict: 补充了xpath和value_sample的完整Schema
    """
    try:
        logger.info(f"正在为预定义Schema补充xpath信息（{len(schema_template)} 个字段）...")

        # 1. 获取Prompt
        prompt = SchemaExtractionPrompts.get_schema_enrichment_prompt()

        # 2. 构建消息
        # 确保中文字段名正确序列化
        try:
            schema_str = json.dumps(schema_template, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"JSON序列化失败，尝试使用ASCII模式: {e}")
            schema_str = json.dumps(schema_template, ensure_ascii=True, indent=2)

        user_message = f"{prompt}\n\n## Schema模板\n\n```json\n{schema_str}\n```\n\n## HTML内容\n\n```html\n{html_content[:50000]}\n```"

        # 确保消息内容是有效的UTF-8字符串
        try:
            # 清理可能存在的替代字符（surrogate characters）
            user_message = user_message.encode('utf-8', errors='replace').decode('utf-8')
        except Exception as e:
            logger.warning(f"消息编码处理失败: {e}")

        # 3. 调用LLM
        model = ChatOpenAI(
            model=settings.default_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            temperature=0.1
        )

        messages = [
            {"role": "system", "content": "你是一个专业的HTML分析和XPath专家。"},
            {"role": "user", "content": user_message}
        ]

        response = model.invoke(messages)

        # 4. 解析响应
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)

        result = _parse_llm_response(content)

        # 5. 验证返回的字段是否与模板一致
        template_keys = set(schema_template.keys())
        result_keys = set(result.keys())
        if template_keys != result_keys:
            logger.warning(f"返回的Schema字段与模板不一致")
            logger.warning(f"  模板字段: {template_keys}")
            logger.warning(f"  返回字段: {result_keys}")
            logger.warning(f"  缺失字段: {template_keys - result_keys}")
            logger.warning(f"  多余字段: {result_keys - template_keys}")

        logger.success(f"成功为预定义Schema补充xpath信息")
        return result

    except Exception as e:
        import traceback
        error_msg = f"Schema补充失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise Exception(error_msg)
