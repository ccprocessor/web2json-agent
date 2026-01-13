<div align="center">

# 🌐 web2json-agent

**告别爬虫开发，秒级获取网页数据**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-00C851?style=for-the-badge&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Compatible-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![PyPI](https://img.shields.io/badge/PyPI-1.1.2-blue?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/web2json-agent/)

[English](../README.md) | [中文](README_zh.md)

</div>

---

## 📋 DEMO


https://github.com/user-attachments/assets/6eec23d4-5bf1-4837-af70-6f0a984d5464


---

## 📊 SWDE 基准测试结果

SWDE 数据集涵盖 8 个垂直领域，80 个网站，124,291 页面

<div align="center">

| |Precision|Recall|F1 Score|
|--------|-------|-------|------|
|COT| 87.75 | 79.90 |76.95 |
|Reflexion| **93.28** | 82.76 |82.40 |
|AUTOSCRAPER| 92.49 | 89.13 |88.69 |
| Web2JSON-Agent | 91.50 | **90.46** |**89.93** |

</div>

---

## 🚀 快速开始

### 通过 pip 安装

```bash
# 1. 安装包
pip install web2json-agent

# 2. 初始化配置
web2json setup
```

### 开发者安装

```bash
# 1. 克隆仓库
git clone https://github.com/ccprocessor/web2json-agent
cd web2json-agent

# 2. 以可编辑模式安装
pip install -e .

# 3. 初始化配置
web2json setup
```

---

## 🐍 API 使用

Web2JSON 提供四个简单的 API，适用于不同的使用场景。

### 示例 1：直接获取结构化数据

**自动模式** - 让 Agent 自动筛选字段并提取数据：

```python
from web2json import Web2JsonConfig, extract_html_to_json

config = Web2JsonConfig(
    name="my_project",
    html_path="html_samples/",
    output_path="output/"
)

result = extract_html_to_json(config)
# 输出：output/my_project/result/*.json
print(f"✓ 结果已保存至：{result}")
```

**预定义模式** - 仅提取指定字段：

```python
from web2json import Web2JsonConfig, extract_html_to_json

config = Web2JsonConfig(
    name="articles",
    html_path="html_samples/",
    output_path="output/",
    schema={
        "title": "string",
        "author": "string",
        "date": "string",
        "content": "string"
    }
)

result = extract_html_to_json(config)
# 输出：output/articles/result/*.json
print(f"✓ 结果已保存至：{result}")
```

---

### 示例 2：生成可重用解析器

生成一次解析器，多次使用：

```python
from web2json import Web2JsonConfig, generate_html_parser

config = Web2JsonConfig(
    name="product_parser",
    html_path="training_samples/",
    output_path="parsers/"
)

parser_path = generate_html_parser(config)
# 输出：parsers/product_parser/final_parser.py
print(f"✓ 解析器已保存：{parser_path}")
```

---

### 示例 3：使用现有解析器解析

在新的 HTML 文件上重用已训练的解析器：

```python
from web2json import Web2JsonConfig, parse_html_with_parser

config = Web2JsonConfig(
    name="batch_001",
    html_path="new_html_files/",
    output_path="results/",
    parser_path="parsers/product_parser/final_parser.py"
)

result = parse_html_with_parser(config)
# 输出：results/batch_001/result/*.json
print(f"✓ 解析数据已保存至：{result}")
```

---

### 示例 4：仅生成 Schema

生成包含字段描述和 XPath 的JSON Schema

```python
from web2json import Web2JsonConfig, infer_html_to_schema
import json

config = Web2JsonConfig(
    name="schema_exploration",
    html_path="html_samples/",
    output_path="schemas/"
)

schema_path = infer_html_to_schema(config)
# 输出：schemas/schema_exploration/final_schema.json

# 查看学习到的 schema
with open(schema_path) as f:
    schema = json.load(f)
    print(json.dumps(schema, indent=2))
```

---

### 配置参数参考

| 参数 | 类型 | 默认值 | 说明 |
|-----------|------|---------|-------------|
| `name` | `str` | 必需 | 项目名称（创建子目录） |
| `html_path` | `str` | 必需 | HTML 文件所在目录 |
| `output_path` | `str` | `"output"` | 输出目录 |
| `iteration_rounds` | `int` | `3` | 用于学习的样本数量 |
| `schema` | `Dict` | `None` | 预定义字段（None = 自动模式） |
| `parser_path` | `str` | `None` | 解析器文件（用于 `parse_html_with_parser`） |

---

### 应该使用哪个 API？

```python
# 需要立即获取 JSON 数据？ → extract_html_to_json
extract_html_to_json(config)

# 想先查看 schema？ → infer_html_to_schema
infer_html_to_schema(config)

# 需要可重用的解析器？ → generate_html_parser
generate_html_parser(config)

# 已有解析器，需要解析更多文件？ → parse_html_with_parser
parse_html_with_parser(config)
```

---

## 📄 许可证

Apache-2.0 License

---

<div align="center">

**用 ❤️ 打造 by web2json-agent 团队**

[⭐ 在 GitHub 上给我们点个 Star](https://github.com/ccprocessor/web2json-agent) | [🐛 报告问题](https://github.com/ccprocessor/web2json-agent/issues) | [📖 文档](https://github.com/ccprocessor/web2json-agent)

</div>
