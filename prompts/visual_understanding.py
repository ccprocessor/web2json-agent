"""
视觉理解 Prompt 模板
用于从网页截图提取结构化信息
"""


class VisualUnderstandingPrompts:
    """视觉理解 Prompt 模板类"""

    @staticmethod
    def get_extraction_prompt() -> str:
        """
        获取结构化信息提取 Prompt

        Returns:
            Prompt 字符串
        """
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

    @staticmethod
    def get_system_message() -> str:
        """获取系统消息"""
        return "你是一个专业的网页截图分析助手，擅长识别网页中的结构化信息。"
