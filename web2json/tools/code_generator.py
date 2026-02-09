"""
代码生成工具
从HTML和JSON Schema生成解析代码
"""
import json
import os
from pathlib import Path
from typing import Dict
from loguru import logger
from web2json.config.settings import settings
from web2json.prompts.code_generator import CodeGeneratorPrompts


def generate_parser_code(
    html_content: str,
    target_json: Dict,
    output_dir: str = "generated_parsers",
    previous_parser_code: str = None,
    previous_parser_path: str = None,
    round_num: int = 1
) -> Dict:
    """
    从HTML和目标JSON生成或优化BeautifulSoup解析代码

    Args:
        html_content: HTML内容
        target_json: 目标JSON结构
        output_dir: 输出目录
        previous_parser_code: 前一轮的解析代码（用于优化）
        previous_parser_path: 前一轮的解析器路径（用于更新）
        round_num: 当前轮次号

    Returns:
        生成/优化结果，包括代码路径和配置路径
    """
    try:
        if round_num == 1:
            logger.info("正在从0生成解析代码...")
        else:
            logger.info(f"正在基于前一轮代码优化（第 {round_num} 轮）...")

        # 使用封装的 LLMClient 以支持 token 追踪
        from web2json.utils.llm_client import LLMClient

        llm_client = LLMClient(
            model=settings.code_gen_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            api_base=os.getenv("OPENAI_API_BASE"),
            temperature=settings.code_gen_temperature
        )

        # 使用 Prompt 模块构建提示词
        if round_num == 1:
            prompt = CodeGeneratorPrompts.get_initial_generation_prompt(
                html_content,
                target_json
            )
        else:
            prompt = CodeGeneratorPrompts.get_optimization_prompt(
                html_content,
                target_json,
                previous_parser_code,
                round_num
            )

        # 调用 LLM 生成代码
        messages = [
            {"role": "system", "content": CodeGeneratorPrompts.get_system_message()},
            {"role": "user", "content": prompt}
        ]

        # 使用 LLMClient 的 chat_completion 方法（自动记录 token）
        generated_code = llm_client.chat_completion(messages)

        # 清理 markdown 标记
        generated_code = generated_code.strip()

        # 移除 markdown 代码块标记
        if generated_code.startswith("```python"):
            generated_code = generated_code[len("```python"):].strip()
        elif generated_code.startswith("```"):
            generated_code = generated_code[3:].strip()

        if generated_code.endswith("```"):
            generated_code = generated_code[:-3].strip()

        # 保存生成的代码
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        parser_path = output_path / "generated_parser.py"
        parser_path.write_text(generated_code, encoding='utf-8')

        # 生成配置文件
        # 支持两种schema格式：
        # 1. 简单格式: {"field": "string"}
        # 2. 详细格式: {"field": {"type": "string", "description": "..."}}
        fields = {}
        for key, value in target_json.items():
            if isinstance(value, dict):
                # 详细格式
                fields[key] = {
                    'type': value.get('type', 'string'),
                    'description': value.get('description', ''),
                    'required': True
                }
            elif isinstance(value, str):
                # 简单格式
                fields[key] = {
                    'type': value,
                    'description': '',
                    'required': True
                }
            else:
                # 其他类型，默认处理
                fields[key] = {
                    'type': str(value),
                    'description': '',
                    'required': True
                }

        config = {
            'version': '1.0',
            'round': round_num,
            'fields': fields,
            'options': {
                'encoding': 'utf-8',
                'timeout': 30,
                'retry': 3
            }
        }
        config_path = output_path / "schema.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        if round_num == 1:
            logger.success(f"代码生成完成")
        else:
            logger.success(f"代码优化完成（第 {round_num} 轮）")

        return {
            'parser_path': str(parser_path),
            'config_path': str(config_path),
            'code': generated_code,
            'config': config,
            'round': round_num
        }

    except Exception as e:
        error_msg = f"代码生成失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

