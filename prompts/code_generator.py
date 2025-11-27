"""
代码生成器 Prompt 模板
用于生成和优化 BeautifulSoup 解析代码
"""
import json
from typing import Dict


class CodeGeneratorPrompts:
    """代码生成器 Prompt 模板类"""

    @staticmethod
    def get_initial_generation_prompt(html_content: str, target_json: Dict) -> str:
        """
        获取初始代码生成 Prompt（第一轮）

        Args:
            html_content: HTML 内容
            target_json: 目标 JSON 结构

        Returns:
            Prompt 字符串
        """
        # 截断过长的HTML
        if len(html_content) > 30000:
            html_content = html_content[:30000] + "\n... (截断)"

        return f"""
你是一个专业的HTML解析代码生成器。请根据以下信息生成一个Python类，用于解析同类网页。

## 目标结构
需要提取以下字段（JSON格式）：
```json
{json.dumps(target_json, ensure_ascii=False, indent=2)}
```

## HTML示例
```html
{html_content}
```

## 要求
1. 生成一个名为 `WebPageParser` 的Python类
2. 使用 BeautifulSoup 和 lxml 进行解析
3. 实现 `parse(html: str) -> dict` 方法
4. 为每个字段编写提取逻辑，使用CSS选择器或XPath
5. 尽量使用类名、ID等稳定属性，避免使用绝对索引
6. 代码尽量简洁，减少冗余
7. 添加适当的错误处理

## 输出格式 - 重要！
**严格要求：**
1. 直接输出纯Python代码，从 `import` 语句开始
2. **绝对不要**使用任何markdown标记，包括：
   - 不要使用 ```python
   - 不要使用 ```
   - 不要使用任何反引号
3. 不要包含任何说明文字、注释或解释
4. 代码必须可以直接保存为.py文件并运行
5. 确保代码完整，所有方法和函数都要有完整的实现

**正确示例（直接从import开始）：**
import sys
import json
from pathlib import Path
...

## 使用示例要求
在 `if __name__ == '__main__'` 部分，必须生成一个完整的 main 函数，支持两种输入方式：

**main 函数结构：**
```python
def main():
    # 获取命令行参数，默认为 'sample.html'
    input_source = sys.argv[1] if len(sys.argv) > 1 else 'sample.html'

    try:
        # 判断是 URL 还是文件
        if input_source.startswith('http://') or input_source.startswith('https://'):
            # URL 处理：使用 DrissionPage
            try:
                from DrissionPage import ChromiumPage
            except ImportError:
                print(json.dumps({{'error': 'DrissionPage not installed. Install it with: pip install DrissionPage'}}))
                sys.exit(1)

            page = ChromiumPage()
            page.get(input_source)
            html_content = page.html
            page.quit()
        else:
            # 文件处理：直接读取
            html_file = Path(input_source)
            if not html_file.exists():
                print(json.dumps({{'error': f'File not found: {{html_file}}'}}))
                sys.exit(1)
            html_content = html_file.read_text(encoding='utf-8')

        # 解析并输出结果
        parser = WebPageParser()
        result = parser.parse(html_content)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({{'error': str(e)}}))
        sys.exit(1)


if __name__ == '__main__':
    main()
```

**注意：必须完整实现上述结构，不要省略任何部分！**
"""

    @staticmethod
    def get_optimization_prompt(
        html_content: str,
        target_json: Dict,
        previous_parser_code: str,
        round_num: int
    ) -> str:
        """
        获取代码优化 Prompt（第二轮及以后）

        Args:
            html_content: HTML 内容
            target_json: 目标 JSON 结构
            previous_parser_code: 前一轮的解析代码
            round_num: 当前轮次号

        Returns:
            Prompt 字符串
        """
        # 截断过长的HTML
        if len(html_content) > 30000:
            html_content = html_content[:30000] + "\n... (截断)"

        return f"""
你是一个专业的HTML解析代码优化师。你需要根据新的HTML样本和更新的字段列表，优化和补充之前生成的解析代码。

## 当前轮次信息
轮次: {round_num}
任务: 补充和优化现有解析代码

## 前一轮生成的解析代码
```python
{previous_parser_code[:2000]}
...（部分代码）
```

## 新的HTML示例
```html
{html_content}
```

## 更新的目标结构
需要提取以下字段（JSON格式）：
```json
{json.dumps(target_json, ensure_ascii=False, indent=2)}
```

## 优化要求
1. 保留前一轮代码中已有的、正确的字段提取逻辑（函数形式）
2. 添加在前一轮中遗漏的新字段提取逻辑
3. 尽量使用类名、ID等稳定属性，避免使用绝对索引
4. 代码尽量简洁，减少冗余
5. 添加适当的错误处理
6. main函数是固定的，不要修改

## 输出格式 - 重要！
**严格要求：**
1. 直接输出纯Python代码，从 `import` 语句开始
2. **绝对不要**使用任何markdown标记，包括：
   - 不要使用 ```python
   - 不要使用 ```
   - 不要使用任何反引号
3. 不要包含任何说明文字、注释或解释
4. 代码必须可以直接保存为.py文件并运行
5. 确保代码完整，所有方法和函数都要有完整的实现
6. 输出整个完整的WebPageParser类和main部分

## 优化建议
- 检查前一轮代码对新HTML的适配情况
- 合并两个样本中的选择器策略
- 确保所有字段都有备选方案


## 使用示例要求
在 `if __name__ == '__main__'` 部分，有一个完整的 main 函数，支持两种输入方式，当前已经实现，请勿修改。

**main 函数结构：**
```python
def main():
    # 获取命令行参数，默认为 'sample.html'
    input_source = sys.argv[1] if len(sys.argv) > 1 else 'sample.html'

    try:
        # 判断是 URL 还是文件
        if input_source.startswith('http://') or input_source.startswith('https://'):
            # URL 处理：使用 DrissionPage
            try:
                from DrissionPage import ChromiumPage
            except ImportError:
                print(json.dumps({{'error': 'DrissionPage not installed. Install it with: pip install DrissionPage'}}))
                sys.exit(1)

            page = ChromiumPage()
            page.get(input_source)
            html_content = page.html
            page.quit()
        else:
            # 文件处理：直接读取
            html_file = Path(input_source)
            if not html_file.exists():
                print(json.dumps({{'error': f'File not found: {{html_file}}'}}))
                sys.exit(1)
            html_content = html_file.read_text(encoding='utf-8')

        # 解析并输出结果
        parser = WebPageParser()
        result = parser.parse(html_content)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({{'error': str(e)}}))
        sys.exit(1)


if __name__ == '__main__':
    main()
```

"""

    @staticmethod
    def get_system_message() -> str:
        """获取系统消息"""
        return "你是一个专业的Python代码生成助手。"
