"""
代码修复工具
基于验证结果和错误信息，使用LLM修复生成的解析器代码
"""
from typing import Dict, List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from config.settings import settings
from loguru import logger
import json


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
    
    # 构建错误描述
    error_descriptions = []
    for i, error in enumerate(validation_errors, 1):
        error_descriptions.append(
            f"{i}. URL: {error.get('url', 'unknown')}\n"
            f"   错误: {error.get('error', 'unknown error')}\n"
            f"   详情: {error.get('details', 'no details')}"
        )
    
    errors_text = "\n".join(error_descriptions)
    
    # 构建修复提示词
    prompt = f"""你是一个专业的Python代码调试专家。请修复以下BeautifulSoup解析器代码。

## 原始代码
```python
{original_code[:5000]}  # 限制长度
```

## 目标JSON结构
```json
{json.dumps(target_json, ensure_ascii=False, indent=2)[:2000]}
```

## 验证错误
{errors_text}

## 修复要求
1. 分析错误原因（选择器失效、字段缺失、类型错误等）
2. 修复代码中的问题
3. 确保代码能够正确提取所有必需字段
4. 添加更健壮的错误处理
5. 使用更可靠的选择器策略（优先使用多个备选选择器）

## 输出格式 - 重要！
**严格要求：**
1. 直接输出修复后的完整Python代码，从 `import` 语句开始
2. **绝对不要**使用任何markdown标记，包括：
   - 不要使用 ```python
   - 不要使用 ```
   - 不要使用任何反引号
3. 不要包含任何说明文字、注释或解释（代码内注释除外）
4. 代码必须可以直接保存为.py文件并运行
5. 保持原有的类名 `WebPageParser` 和方法名 `parse`

请直接输出修复后的代码：
"""
    
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
            {"role": "system", "content": "你是一个专业的Python代码调试和修复专家，擅长BeautifulSoup和网页解析。"},
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

