"""
Schema提取的Prompt模板
用于从HTML中提取Schema
"""


class SchemaExtractionPrompts:
    """Schema提取Prompt模板类"""

    @staticmethod
    def get_html_extraction_prompt() -> str:
        """
        获取从HTML提取Schema的Prompt

        Returns:
            Prompt字符串
        """
        return """你是一个专业的HTML分析专家，擅长从HTML中提取结构化数据Schema。

## 任务目标

分析提供的HTML内容，识别核心数据字段，并为每个字段生成XPath提取路径。

## 核心原则

**仅对网页中的有价值正文信息进行Schema建模**，包括但不限于：
- 文章标题、文章作者、作者信息、发布时间
- 文章摘要、完整的正文内容
- 评论区（如果有多个评论，这是一个列表字段）
- 其他核心内容元素

## 明确排除

请忽略以下非核心元素：
- 广告、侧边栏、推荐位、导航栏
- 页眉、页脚、相关推荐
- 任何网站通用组件

## 输出格式

请严格按照以下JSON格式输出：

```json
{
  "title": {
    "type": "string",
    "description": "文章标题",
    "value_sample": "关于人工智能的未来...",
    "xpath": "//h1[@class='article-title']/text()"
  },
  "author": {
    "type": "string",
    "description": "作者姓名",
    "value_sample": "张三",
    "xpath": "//div[@class='author-info']//span[@class='name']/text()"
  },
  "publish_time": {
    "type": "string",
    "description": "发布时间",
    "value_sample": "2024-01-15 10:30",
    "xpath": "//time[@class='publish-date']/@datetime"
  },
  "content": {
    "type": "string",
    "description": "文章正文内容",
    "value_sample": "人工智能技术正在...",
    "xpath": "//div[@class='article-content']//text()"
  },
  "comments": {
    "type": "array",
    "description": "评论列表",
    "value_sample": [{"user": "用户A", "text": "很好的文章"}],
    "xpath": "//div[@class='comment-list']//div[@class='comment-item']"
  }
}
```

## 字段说明

- **type**: 数据类型（string, number, array, object等）
- **description**: 字段的语义描述
- **value_sample**: 从HTML中提取的实际值示例（字符串字段截取前50字符，避免过长）
- **xpath**: 用于提取该字段的XPath表达式，确保路径准确可用

## XPath编写要求

1. 优先使用class、id等属性定位元素
2. 对于文本内容使用/text()，对于属性使用/@属性名
3. 对于列表字段，xpath应该定位到列表项的容器
4. 确保xpath尽可能健壮，适用于同类型的多个页面

## 注意事项

- value_sample应该是从HTML中实际提取的值，而不是编造的
- 对于过长的文本，只截取前50个字符作为示例
- 如果某个常见字段在HTML中不存在，可以不包含在输出中
- 确保输出是有效的JSON格式
"""

    @staticmethod
    def get_schema_enrichment_prompt() -> str:
        """
        获取Schema补充XPath的Prompt（预定义模式）

        Returns:
            Prompt字符串
        """
        return """你是一个专业的HTML分析和XPath专家，擅长为预定义的Schema字段补充技术细节。

## 任务目标

根据用户提供的Schema模板（只包含字段key和基本信息）和HTML内容，为每个字段补充以下信息：
- **xpath**: 准确的XPath提取路径
- **value_sample**: 从HTML中提取的实际值示例

## 输入说明

你将收到：
1. **Schema模板**: 包含字段key、type、description（用户预定义）
2. **HTML内容**: 需要分析的网页HTML

## 输出要求

请保持用户定义的所有字段key不变，只补充xpath和value_sample，严格按照以下JSON格式输出：

```json
{
  "title": {
    "type": "string",
    "description": "文章标题",
    "value_sample": "关于人工智能的未来...",
    "xpath": "//h1[@class='article-title']/text()"
  },
  "author": {
    "type": "string",
    "description": "作者姓名",
    "value_sample": "张三",
    "xpath": "//div[@class='author-info']//span[@class='name']/text()"
  },
  "publish_time": {
    "type": "string",
    "description": "发布时间",
    "value_sample": "2024-01-15 10:30",
    "xpath": "//time[@class='publish-date']/@datetime"
  },
  "content": {
    "type": "string",
    "description": "文章正文内容",
    "value_sample": "人工智能技术正在...",
    "xpath": "//div[@class='article-content']//text()"
  },
  "comments": {
    "type": "array",
    "description": "评论列表",
    "value_sample": [{"user": "用户A", "text": "很好的文章"}],
    "xpath": "//div[@class='comment-list']//div[@class='comment-item']"
  }
}
```

## XPath编写要求

1. 优先使用class、id等属性定位元素
2. 对于文本内容使用/text()，对于属性使用/@属性名
3. 对于列表字段，xpath应该定位到列表项的容器
4. 确保xpath尽可能健壮，适用于同类型的多个页面
5. 如果某个字段在HTML中找不到对应内容，xpath设为空字符串""，value_sample设为null

## 注意事项

- **必须保持用户定义的所有字段key、type、description不变**
- **一个字段可能对应多个xpath，务必选择有实际值的xpath**
- value_sample应该是从HTML中实际提取的值，而不是编造的
- 对于过长的文本，只截取前50个字符作为示例
- 如果某个字段在HTML中不存在，保留该字段但xpath为空
- 确保输出是有效的JSON格式
- 不要添加或删除任何用户预定义的字段
"""

