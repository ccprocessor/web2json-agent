"""
代码生成工具
从HTML和JSON Schema生成解析代码
"""
import json
import os
from pathlib import Path
from typing import Dict
from loguru import logger
from config.settings import settings
from langchain_core.tools import tool


def _build_code_generation_prompt(html_content: str, target_json: Dict) -> str:
    """构建代码生成提示词"""
    # 截断过长的HTML
    if len(html_content) > 30000:
        html_content = html_content[:30000] + "\n... (截断)"

    prompt = f"""
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
在 `if __name__ == '__main__'` 部分，生成一个灵活的使用示例：
1. 支持从命令行参数接收 HTML 文件路径或 URL
2. 如果是 URL，使用 DrissionPage 的 ChromiumPage 获取 HTML 内容
3. 如果是文件路径，直接读取文件
4. 默认参数示例：使用命令行参数 sys.argv[1]，默认为当前目录的 'sample.html'
"""
    return prompt


@tool
def generate_parser_code(html_content: str, target_json: Dict, output_dir: str = "generated_parsers") -> Dict:
    """
    从HTML和目标JSON生成BeautifulSoup解析代码

    Args:
        html_content: HTML内容
        target_json: 目标JSON结构
        output_dir: 输出目录

    Returns:
        生成结果，包括代码路径和配置路径
    """
    try:
        logger.info("正在生成解析代码...")

        # 使用 LangChain 1.0 的 ChatOpenAI
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(
            model=settings.code_gen_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            temperature=settings.code_gen_temperature
        )

        # 构建提示词
        prompt = _build_code_generation_prompt(html_content, target_json)

        # 调用 LLM 生成代码
        messages = [
            {"role": "system", "content": "你是一个专业的Python代码生成助手。"},
            {"role": "user", "content": prompt}
        ]

        response = model.invoke(messages)

        # 提取生成的代码并清理 markdown 标记
        generated_code = response.content.strip()

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
        config = {
            'version': '1.0',
            'fields': {
                key: {
                    'type': value.get('type', 'string'),
                    'description': value.get('description', ''),
                    'required': True
                }
                for key, value in target_json.items()
            },
            'options': {
                'encoding': 'utf-8',
                'timeout': 30,
                'retry': 3
            }
        }
        config_path = output_path / "schema.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.success(f"代码生成完成: {parser_path}")

        return {
            'parser_path': str(parser_path),
            'config_path': str(config_path),
            'code': generated_code,
            'config': config
        }

    except Exception as e:
        error_msg = f"代码生成失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
