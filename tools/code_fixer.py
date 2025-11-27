"""
代码修复工具
基于验证结果和错误信息，使用LLM修复生成的解析器代码
"""
from typing import Dict, List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from config.settings import settings
from loguru import logger
from prompts.code_fixer import CodeFixerPrompts


@tool
def fix_parser_code(
    original_code: str,
    validation_errors: List[Dict],
    target_json: Dict,
    html_sample: str = None
) -> Dict:
    """
    修复解析器代码

    Args:
        original_code: 原始代码
        validation_errors: 验证错误列表
        target_json: 目标JSON结构
        html_sample: HTML样本（可选，用于参考）

    Returns:
        修复后的代码和相关信息
    """
    logger.info("开始修复解析器代码...")

    # 使用 Prompt 模块构建修复提示词
    prompt = CodeFixerPrompts.get_fix_prompt(
        original_code,
        validation_errors,
        target_json
    )

    try:
        # 创建LLM实例
        llm = ChatOpenAI(
            model=settings.code_gen_model,
            temperature=settings.code_gen_temperature,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
            max_tokens=settings.code_gen_max_tokens
        )

        # 调用LLM
        messages = [
            {"role": "system", "content": CodeFixerPrompts.get_system_message()},
            {"role": "user", "content": prompt}
        ]

        response = llm.invoke(messages)
        fixed_code = response.content
        
        # 清理可能的markdown标记（备用安全措施）
        if "```python" in fixed_code:
            fixed_code = fixed_code.split("```python")[1].split("```")[0].strip()
        elif "```" in fixed_code:
            fixed_code = fixed_code.split("```")[1].split("```")[0].strip()
        
        logger.success("代码修复完成")
        
        return {
            'success': True,
            'fixed_code': fixed_code,
            'original_code': original_code,
            'changes_made': '基于验证错误进行了修复'
        }
        
    except Exception as e:
        logger.error(f"代码修复失败: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'fixed_code': original_code  # 返回原始代码
        }

