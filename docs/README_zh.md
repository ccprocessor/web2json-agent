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

## 📖 什么是 web2json-agent？

基于 AI 的智能网页解析代理，从 HTML 样本自动生成生产级解析器代码，无需手写 XPath/CSS 选择器。

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

Web2JSON 提供五个简单的 API，适用于不同的使用场景。所有示例都可以直接运行！

### API 1: `extract_data` - 完整工作流

一步从 HTML 提取结构化数据（schema + parser + data）。

**自动模式** - 让 AI 自动发现并提取字段：

```python
from web2json import Web2JsonConfig, extract_data

config = Web2JsonConfig(
    name="my_project",
    html_path="html_samples/",
    output_path="output/"
    # enable_schema_edit=True  # 取消注释以手动编辑 schema
)

result_dir = extract_data(config)
# 输出：output/my_project/result/*.json
```

**预定义模式** - 仅提取指定字段：

```python
from web2json import Web2JsonConfig, extract_data

config = Web2JsonConfig(
    name="articles",
    html_path="html_samples/",
    schema={
        "title": "string",
        "author": "string",
        "date": "string",
        "content": "string"
    }
)

result_dir = extract_data(config)
# 输出：output/articles/result/*.json
```

---

### API 2: `extract_schema` - 仅提取 Schema

生成描述 HTML 数据结构的 JSON schema。

```python
from web2json import Web2JsonConfig, extract_schema

config = Web2JsonConfig(
    name="schema_only",
    html_path="html_samples/",
    iteration_rounds=3
    # enable_schema_edit=True  # 取消注释以手动编辑 schema
)

schema_path = extract_schema(config)
# 输出：output/schema_only/final_schema.json
```

---

### API 3: `infer_code` - 生成解析器代码

从现有 schema 生成解析器代码。

```python
from web2json import infer_code

parser_path = infer_code(
    schema_path="output/schema_only/final_schema.json",
    html_path="html_samples/",
    name="my_parser"
)
# 输出：output/my_parser/final_parser.py
```

---

### API 4: `extract_data_with_code` - 使用代码解析

使用解析器代码从 HTML 文件提取数据。

```python
from web2json import extract_data_with_code

# 读取解析器代码
with open("output/my_parser/final_parser.py") as f:
    parser_code = f.read()

result_dir = extract_data_with_code(
    parser_code=parser_code,
    html_path="new_html_files/",
    name="batch_001"
)
# 输出：output/batch_001/result/*.json
```

---

### API 5: `classify_html_dir` - 按布局分类 HTML

按布局相似度对 HTML 文件分组（适用于混合布局数据集）。

```python
from web2json import classify_html_dir

result = classify_html_dir(
    html_path="mixed_html/",
    name="classified"
)
# 输出：output/classified/cluster_0/, cluster_1/, cluster_info.txt
```

---

### 配置参数参考

**Web2JsonConfig 参数：**

| 参数 | 类型 | 默认值 | 说明 |
|-----------|------|---------|-------------|
| `name` | `str` | 必需 | 项目名称（创建子目录） |
| `html_path` | `str` | 必需 | HTML 目录路径 |
| `output_path` | `str` | `"output"` | 输出目录 |
| `iteration_rounds` | `int` | `3` | 用于学习的样本数量 |
| `schema` | `Dict` | `None` | 预定义 schema（None = 自动模式） |
| `enable_schema_edit` | `bool` | `False` | 启用手动编辑 schema |

**独立 API 参数：**

| API | 参数 | 说明 |
|-----|------|------|
| `infer_code` | `schema_path`, `html_path`, `name` | 从 schema 生成解析器 |
| `extract_data_with_code` | `parser_code`, `html_path`, `name` | 使用代码字符串解析 |
| `classify_html_dir` | `html_path`, `name` | 按布局分类 |

---

### 应该使用哪个 API？

```python
# 需要立即获取数据？ → extract_data
extract_data(config)

# 想先查看/编辑 schema？ → extract_schema + infer_code
schema = extract_schema(config)
parser = infer_code(schema_path=schema, html_path="...")

# 已有解析器代码，需要解析更多文件？ → extract_data_with_code
extract_data_with_code(parser_code=code, html_path="...")

# 混合布局（列表页 + 详情页）？ → classify_html_dir
classify_html_dir(html_path="...")
```

---

## 📄 许可证

Apache-2.0 License

---

<div align="center">

**用 ❤️ 打造 by web2json-agent 团队**

[⭐ 在 GitHub 上给我们点个 Star](https://github.com/ccprocessor/web2json-agent) | [🐛 报告问题](https://github.com/ccprocessor/web2json-agent/issues) | [📖 文档](https://github.com/ccprocessor/web2json-agent)

</div>
