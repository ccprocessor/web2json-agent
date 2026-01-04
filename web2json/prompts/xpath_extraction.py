"""
XPath提取器 Prompt 模板
用于从生成的parser代码中提取最优xpath表达式
"""
import json
from typing import Dict


class XPathExtractionPrompts:
    """XPath提取 Prompt 模板类"""

    @staticmethod
    def get_xpath_extraction_prompt(parser_code: str) -> str:
        """
        获取XPath提取 Prompt

        Args:
            parser_code: 生成的parser代码

        Returns:
            Prompt 字符串
        """
        return f"""
你是一个专业的代码分析专家。请分析以下Python解析器代码，提取出每个字段对应的最优XPath表达式。

## 解析器代码
```python
{parser_code}
```

## 任务要求

1. **分析代码结构**：识别WebPageParser类中的所有_extract_xxx方法
2. **提取XPath表达式**：
   - 找到每个方法中使用的 `tree.xpath()` 调用
   - 如果一个字段有多个xpath，选择最核心、最重要的一个（通常是第一个或提取主要内容的）
   - XPath表达式应该是完整的、可直接使用的字符串
3. **输出格式**：返回一个JSON对象，key是字段名，value是最优的xpath字符串

## 输出格式示例

```json
{{
  "title": "//h1[@class='product-title']/text()",
  "price": "//span[@class='price']/text()",
  "description": "//div[@class='description']//text()",
  "images": "//img[@class='product-img']/@src"
}}
```

## 注意事项

1. 字段名应该是_extract_xxx方法中的xxx部分
2. 只返回JSON格式，不要包含其他说明文字
3. 如果某个字段没有使用xpath（例如使用CSS选择器），则不要包含该字段
4. 如果某个字段有多个xpath，选择最能代表该字段主要提取逻辑的xpath
5. XPath表达式必须是字符串类型，不要包含变量或复杂表达式

请直接输出JSON格式的结果，不要包含任何其他内容。
"""
