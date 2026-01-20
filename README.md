<div align="center">

# 🌐 web2json-agent

**Stop Coding Scrapers, Start Getting Data — from Hours to Seconds**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-00C851?style=for-the-badge&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Compatible-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![PyPI](https://img.shields.io/badge/PyPI-1.1.2-blue?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/web2json-agent/)

[English](README.md) | [中文](docs/README_zh.md)

</div>

---

## 📖 What is web2json-agent?

An AI-powered web scraping agent that automatically generates production-ready parser code from HTML samples — no manual XPath/CSS selector writing required.

---

## 📋 Demo



https://github.com/user-attachments/assets/c82e8e13-fc42-4d1f-a81a-4cec6e3f434b

---

## 📊 SWDE Benchmark Results

The SWDE dataset covers 8 vertical fields, 80 websites, and 124,291 pages

<div align="center">

| |Precision|Recall|F1 Score|
|--------|-------|-------|------|
|COT| 87.75 | 79.90 |76.95 |
|Reflexion| **93.28** | 82.76 |82.40 |
|AUTOSCRAPER| 92.49 | 89.13 |88.69 |
| Web2JSON-Agent | 91.50 | **90.46** |**89.93** |

</div>

---

## 🚀 Quick Start

### Install via pip

```bash
# 1. Install package
pip install web2json-agent

# 2. Initialize configuration
web2json setup
```

### Install for Developers

```bash
# 1. Clone the repository
git clone https://github.com/ccprocessor/web2json-agent
cd web2json-agent

# 2. Install in editable mode
pip install -e .

# 3. Initialize configuration
web2json setup
```

---

## 🐍 API Usage

Web2JSON provides five simple APIs for different use cases. All examples are ready to run!

### API 1: `extract_data` - Complete Workflow

Extract structured data from HTML in one step (schema + parser + data).

**Auto Mode** - Let AI automatically discover and extract fields:

```python
from web2json import Web2JsonConfig, extract_data

config = Web2JsonConfig(
    name="my_project",
    html_path="html_samples/",
    output_path="output/"
    # enable_schema_edit=True  # Uncomment to manually edit schema
)

result_dir = extract_data(config)
# Output: output/my_project/result/*.json
```

**Predefined Mode** - Extract only specific fields:

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
# Output: output/articles/result/*.json
```

---

### API 2: `extract_schema` - Extract Schema Only

Generate a JSON schema describing the data structure in HTML.

```python
from web2json import Web2JsonConfig, extract_schema

config = Web2JsonConfig(
    name="schema_only",
    html_path="html_samples/",
    iteration_rounds=3
    # enable_schema_edit=True  # Uncomment to manually edit schema
)

schema_path = extract_schema(config)
# Output: output/schema_only/final_schema.json
```

---

### API 3: `infer_code` - Generate Parser Code

Generate parser code from an existing schema.

```python
from web2json import infer_code

parser_path = infer_code(
    schema_path="output/schema_only/final_schema.json",
    html_path="html_samples/",
    name="my_parser"
)
# Output: output/my_parser/final_parser.py
```

---

### API 4: `extract_data_with_code` - Parse with Code

Use parser code to extract data from HTML files.

```python
from web2json import extract_data_with_code

# Read parser code
with open("output/my_parser/final_parser.py") as f:
    parser_code = f.read()

result_dir = extract_data_with_code(
    parser_code=parser_code,
    html_path="new_html_files/",
    name="batch_001"
)
# Output: output/batch_001/result/*.json
```

---

### API 5: `classify_html_dir` - Classify HTML by Layout

Group HTML files by layout similarity (for mixed-layout datasets).

```python
from web2json import classify_html_dir

result = classify_html_dir(
    html_path="mixed_html/",
    name="classified"
)
# Output: output/classified/cluster_0/, cluster_1/, cluster_info.txt
```

---

### Configuration Reference

**Web2JsonConfig Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Project name (creates subdirectory) |
| `html_path` | `str` | Required | HTML directory path |
| `output_path` | `str` | `"output"` | Output directory |
| `iteration_rounds` | `int` | `3` | Number of samples for learning |
| `schema` | `Dict` | `None` | Predefined schema (None = auto mode) |
| `enable_schema_edit` | `bool` | `False` | Enable manual schema editing |

**Standalone API Parameters:**

| API | Parameters | Description |
|-----|------------|-------------|
| `infer_code` | `schema_path`, `html_path`, `name` | Generate parser from schema |
| `extract_data_with_code` | `parser_code`, `html_path`, `name` | Parse with code string |
| `classify_html_dir` | `html_path`, `name` | Classify by layout |

---

### Which API Should I Use?

```python
# Need data immediately? → extract_data
extract_data(config)

# Want to review/edit schema first? → extract_schema + infer_code
schema = extract_schema(config)
parser = infer_code(schema_path=schema, html_path="...")

# Have parser code, need to parse more files? → extract_data_with_code
extract_data_with_code(parser_code=code, html_path="...")

# Mixed layouts (list + detail pages)? → classify_html_dir
classify_html_dir(html_path="...")
```

---

## 📄 License

Apache-2.0 License

---

<div align="center">

**Made with ❤️ by the web2json-agent team**

[⭐ Star us on GitHub](https://github.com/ccprocessor/web2json-agent) | [🐛 Report Issues](https://github.com/ccprocessor/web2json-agent/issues) | [📖 Documentation](https://github.com/ccprocessor/web2json-agent)

</div>
