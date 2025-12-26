"""
Schema合并的Prompt模板
用于合并单个或多个HTML的Schema
"""
import json


class SchemaMergePrompts:
    """Schema合并Prompt模板类"""

    # HTML和视觉Schema合并Prompt已禁用，保留代码以备后用
    # @staticmethod
    # def get_merge_single_schema_prompt(html_schema: dict, visual_schema: dict) -> str:
    #     """
    #     获取合并单个HTML的两种Schema的Prompt
    #
    #     Args:
    #         html_schema: 从HTML提取的Schema
    #         visual_schema: 从视觉提取的Schema
    #
    #     Returns:
    #         Prompt字符串
    #     """
    #     html_str = json.dumps(html_schema, ensure_ascii=False, indent=2)
    #     visual_str = json.dumps(visual_schema, ensure_ascii=False, indent=2)
    #
    #     return f"""你是一个专业的数据Schema合并专家。
    #
    # ## 任务目标
    #
    # 现在有同一个网页的两种Schema：
    # 1. 从HTML代码提取的Schema（包含xpath路径）
    # 2. 从视觉截图提取的Schema（包含视觉描述）
    #
    # 请分析这两个Schema，判断哪些字段是相同的，并将它们合并为一个完整的Schema。
    #
    # ## HTML Schema（包含xpath）
    #
    # ```json
    # {html_str}
    # ```
    #
    # ## 视觉Schema（包含visual_features）
    #
    # ```json
    # {visual_str}
    # ```
    #
    # ## 合并规则
    #
    # 1. **字段匹配**：根据字段名和description判断两个Schema中的哪些字段是相同的
    # 2. **信息合并**：对于相同的字段，合并它们的信息
    #    - 保留type、description
    #    - 保留HTML Schema的xpath
    #    - 保留视觉Schema的visual_features
    #    - value_sample优先使用HTML Schema的（因为更准确）
    # 3. **保留独有字段**：如果某个字段只在一个Schema中出现，也要保留
    # 4. **列表字段识别**：如果视觉Schema识别出某字段是列表（如评论），而HTML Schema是单个，以视觉Schema为准
    #
    # ## 输出格式
    #
    # 请输出合并后的完整Schema：
    #
    # ```json
    # {{
    #   "title": {{
    #     "type": "string",
    #     "description": "文章标题",
    #     "value_sample": "关于人工智能的未来...",
    #     "xpath": "//h1[@class='article-title']/text()",
    #     "visual_features": "位于页面上部中央区域，字体非常大且加粗..."
    #   }},
    #   // 其他字段
    # }}
    # ```
    #
    # ## 注意事项
    #
    # - 输出必须是完整的、可用的JSON格式
    # - 每个字段应该包含type、description、value_sample、xpath、visual_features（如果有）
    # - 对于只在一个Schema中出现的字段，尽可能保留其信息
    # """

    @staticmethod
    def get_merge_multiple_schemas_prompt(schemas: list) -> str:
        """
        获取合并多个HTML的Schema的Prompt

        Args:
            schemas: 多个HTML的Schema列表

        Returns:
            Prompt字符串
        """
        schemas_str = ""
        for idx, schema in enumerate(schemas, 1):
            schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
            schemas_str += f"\n### HTML {idx} 的Schema\n\n```json\n{schema_json}\n```\n"

        return f"""你是一个专业的数据Schema整合专家。

## 任务目标

现在有{len(schemas)}个不同网页的Schema，它们来自同一类型的网页（例如都是博客文章页）。

请分析这些Schema，进行筛选、合并和修正，输出一个最终的、鲁棒的Schema。

## 输入的多个Schema

{schemas_str}

## 整合规则

1. **字段合并**：将多个Schema中的相同字段合并
   - 相同字段的判断依据：字段名相似 + description含义相同
   - 合并时保留所有有效的xpath路径（一个字段可能有多个xpath）

2. **去除无意义字段**：删除以下字段
   - 广告、推荐、导航等非核心字段
   - 在多个Schema中都不一致的字段（可能是噪音）

3. **修正字段结构**：
   - 将元信息归属到正确的位置（例如：主贴发布时间应该是主贴的属性）
   - 修正字段类型（例如：评论应该是array而不是单个object）
   - 对于列表字段，确保type为array

4. **增强鲁棒性**：
   - 每个字段保留所有可用的xpath路径（数组形式）
   - 确保xpath路径的通用性，适用于多个页面

## 输出格式

请输出最终的完整Schema：

```json
{{
  "title": {{
    "type": "string",
    "description": "文章标题",
    "value_sample": "示例标题",
    "xpaths": [
      "//h1[@class='article-title']/text()",
      "//div[@class='title']/text()"
    ]
  }},
  "comments": {{
    "type": "array",
    "description": "评论列表",
    "value_sample": [{{"user": "用户A", "text": "评论内容"}}],
    "xpaths": [
      "//div[@class='comment-list']//div[@class='comment']",
      "//ul[@class='comments']//li"
    ]
  }},
  // 其他字段
}}
```

## 注意事项

1. **xpaths字段**：改为数组形式，包含所有可用的xpath路径
2. **type修正**：确保列表字段（如评论、标签等）的type为array
3. **结构合理**：字段的层级关系要合理，元信息归属正确
4. **输出完整**：必须是完整的、可解析的JSON格式
5. **保持核心字段**：即使某个字段只在部分Schema中出现，如果它是核心字段（如标题、内容等），也要保留
"""
