"""
Schema提取的Prompt模板
用于从HTML和视觉截图中提取Schema
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
    def get_visual_extraction_prompt() -> str:
        """
        获取从截图提取Schema的Prompt（包含视觉描述）

        Returns:
            Prompt字符串
        """
        return """你是一个专业的网页视觉分析专家，擅长从截图中识别页面结构。

## 任务目标

分析提供的网页截图，识别核心数据字段，并为每个字段提供视觉特征描述。

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
    "value_sample": "关于人工智能的未来",
    "visual_features": "位于页面上部中央区域，字体非常大且加粗，颜色为深色，是页面中最显眼的文本元素"
  },
  "author": {
    "type": "string",
    "description": "作者姓名",
    "value_sample": "张三",
    "visual_features": "位于标题正下方偏左的位置，字体较小，颜色为灰色，旁边可能有作者头像"
  },
  "comments": {
    "type": "array",
    "description": "评论列表",
    "value_sample": [{"user": "用户A", "text": "很好的文章"}],
    "visual_features": "位于正文下方，多个评论项垂直排列，每个评论包含用户名和评论内容"
  }
}
```

## 字段说明

- **type**: 数据类型（string, number, array, object等）
- **description**: 字段的语义描述
- **value_sample**: 从截图中看到的实际值示例（字符串字段截取前50字符）
- **visual_features**: 该元素的视觉特征描述，包括位置、字体、颜色、布局等

## 注意事项

- value_sample应该是从截图中实际看到的值
- visual_features应该足够详细，便于后续定位元素
- 对于列表字段（如评论），要识别出它是多个重复的结构
- 确保输出是有效的JSON格式
"""
