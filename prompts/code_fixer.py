"""
代码修复器 Prompt 模板
用于修复解析器代码中的错误
"""
import json
from typing import Dict, List


class CodeFixerPrompts:
    """代码修复器 Prompt 模板类"""

    @staticmethod
    def get_fix_prompt(
        original_code: str,
        validation_errors: List[Dict],
        target_json: Dict
    ) -> str:
        """
        获取代码修复 Prompt

        Args:
            original_code: 原始代码
            validation_errors: 验证错误列表
            target_json: 目标 JSON 结构

        Returns:
            Prompt 字符串
        """
        # 构建错误描述
        error_descriptions = []
        for i, error in enumerate(validation_errors, 1):
            error_descriptions.append(
                f"{i}. URL: {error.get('url', 'unknown')}\n"
                f"   错误: {error.get('error', 'unknown error')}\n"
                f"   详情: {error.get('details', 'no details')}"
            )

        errors_text = "\n".join(error_descriptions)

        return f"""你是一个专业的Python代码调试专家。请修复以下BeautifulSoup解析器代码。

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

    @staticmethod
    def get_system_message() -> str:
        """获取系统消息"""
        return "你是一个专业的Python代码调试和修复专家，擅长BeautifulSoup和网页解析。"
