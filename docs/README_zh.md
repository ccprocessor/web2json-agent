<div align="center">

# 🌐 web2json-agent

**告别爬虫开发，秒级获取网页数据**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-00C851?style=for-the-badge&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Compatible-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![License](https://img.shields.io/badge/License-Apache--2.0-orange?style=for-the-badge)](../LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-1.1.2-blue?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/web2json-agent/)

[English](../README.md) | [中文](README_zh.md)

</div>


## 📋 视频演示

https://github.com/user-attachments/assets/772fb610-808e-431d-93b3-d16ca0775b3f

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

### 通过 pip 安装（方式1）

```bash
# 1. 安装包
pip install web2json-agent

# 2. 初始化配置
web2json setup
```

### 开发者安装（方式2）

```bash
# 1. 克隆仓库
git clone https://github.com/ccprocessor/web2json-agent
cd web2json-agent

# 2. 以可编辑模式安装
pip install -e .

# 3. 初始化配置
web2json setup
```

### 使用方式

```bash
# 模式1：自动模式 (auto) - 自动选择要抽取的字段并抽取
web2json -d html_samples/ -o output/result

# 模式2：预定义模式 (predefined) - 指定要抽取的字段并抽取
web2json -d html_samples/ -o output/result --interactive-schema
```

---

## 🐍 API 使用

### API 1: extract_data()

完整流程：生成解析器并解析所有HTML

```python
from web2json.simple import extract_data

html_path = "html_samples/"
iteration_rounds = 3  # 默认值

# 方式1: auto模式（Agent 自动分析并选择字段）
result_dir = extract_data(html_path, iteration_rounds=iteration_rounds)
print(f"结果目录: {result_dir}")

# 方式2: predefined模式（指定要抽取的字段）
schema = {
    "title": "string",
    "author": "string",
    "publish_date": "string",
    "content": "string"
}
result_dir = extract_data(html_path, iteration_rounds=iteration_rounds, schema_template=schema)
print(f"结果目录: {result_dir}")
```

### API 2: generate_parser()

只生成解析器代码

```python
from web2json.simple import generate_parser

html_path = "html_samples/"
iteration_rounds = 3  # 默认值

# 方式1: auto模式
parser_path = generate_parser(html_path, iteration_rounds=iteration_rounds)
print(f"解析器路径: {parser_path}")

# 方式2: predefined模式
schema = {
    "title": "string",
    "author": "string",
    "publish_date": "string",
    "content": "string"
}
parser_path = generate_parser(html_path, iteration_rounds=iteration_rounds, schema_template=schema)
print(f"解析器路径: {parser_path}")
```

### API 3: generate_schema()

只生成数据结构定义

```python
from web2json.simple import generate_schema

html_path = "html_samples/"
iteration_rounds = 3  # 默认值

# 方式1: auto模式
schema_path = generate_schema(html_path, iteration_rounds=iteration_rounds)
print(f"Schema路径: {schema_path}")

# 方式2: predefined模式
schema = {
    "title": "string",
    "author": "string",
    "publish_date": "string",
    "content": "string"
}
schema_path = generate_schema(html_path, iteration_rounds=iteration_rounds, schema_template=schema)
print(f"Schema路径: {schema_path}")
```

### API 4: parse_with_parser()

使用已有解析器解析HTML

```python
from web2json.simple import parse_with_parser

html_path = "html_samples/"
parser_path = "output/sample/parsers/final_parser.py"

# 调用接口
result_dir = parse_with_parser(html_path, parser_path)
print(f"结果目录: {result_dir}")
```

### API 5: extract_all()

完整流程，返回所有内容

```python
from web2json.simple import extract_all

html_path = "html_samples/"
iteration_rounds = 3  # 默认值

# 方式1: auto模式
paths = extract_all(html_path, iteration_rounds=iteration_rounds)

# 方式2: predefined模式
schema = {
    "title": "string",
    "author": "string",
    "publish_date": "string",
    "content": "string"
}
paths = extract_all(html_path, iteration_rounds=iteration_rounds, schema_template=schema)

print(f"结果目录: {paths['result_dir']}")
print(f"解析器路径: {paths['parser_path']}")
print(f"Schema路径: {paths['schema_path']}")
print(f"输出目录: {paths['output_dir']}")
```

---

## 📄 许可证

Apache-2.0 License

---

<div align="center">

**用 ❤️ 打造 by web2json-agent 团队**

[⭐ GitHub 点个 Star](https://github.com/ccprocessor/web2json-agent) | [🐛 报告问题](https://github.com/ccprocessor/web2json-agent/issues) | [📖 文档](https://github.com/ccprocessor/web2json-agent)

</div>
