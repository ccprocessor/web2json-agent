<div align="center">

# 🌐 web2json-agent

**Stop Coding Scrapers, Start Getting Data — from Hours to Seconds**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-00C851?style=for-the-badge&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Compatible-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![License](https://img.shields.io/badge/License-Apache--2.0-orange?style=for-the-badge)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-1.1.2-blue?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/web2json-agent/)

[English](README.md) | [中文](docs/README_zh.md)

</div>

---

## 📋 Demo


https://github.com/user-attachments/assets/6eec23d4-5bf1-4837-af70-6f0a984d5464


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

### Usage instructions

```bash
# Mode 1: Auto mode (Automatically select the fields to be extracted)
web2json -d html_samples/ -o output/result

# Mode 2: Predefined mode (Specify the fields to be extracted)
web2json -d html_samples/ -o output/result --interactive-schema
```

---

## 🐍 API Usage

### API 1: extract_data()

Complete workflow: Generate parser and parse all HTML files

```python
from web2json.simple import extract_data

html_path = "html_samples/"
iteration_rounds = 3  # default value

# Method 1: auto mode (agent automatically analyzes and selects fields)
result_dir = extract_data(html_path, iteration_rounds=iteration_rounds)

# Method 2: predefined mode (specify schema)
schema = {
    "title": "string",
    "author": "string",
    "publish_date": "string",
    "content": "string"
}
result_dir = extract_data(html_path, iteration_rounds=iteration_rounds, schema_template=schema)

# output
print(f"Result directory: {result_dir}")
```

### API 2: generate_parser()

Generate parser code only

```python
from web2json.simple import generate_parser

html_path = "html_samples/"
iteration_rounds = 3  # default value

# Method 1: auto mode
parser_path = generate_parser(html_path, iteration_rounds=iteration_rounds)

# Method 2: predefined mode
schema = {
    "title": "string",
    "author": "string",
    "publish_date": "string",
    "content": "string"
}
parser_path = generate_parser(html_path, iteration_rounds=iteration_rounds, schema_template=schema)

# output
print(f"Parser path: {parser_path}")
```

### API 3: generate_schema()

Generate data schema definition only

```python
from web2json.simple import generate_schema

html_path = "html_samples/"
iteration_rounds = 3  # default value

# Method 1: auto mode
schema_path = generate_schema(html_path, iteration_rounds=iteration_rounds)

# Method 2: predefined mode
schema = {
    "title": "string",
    "author": "string",
    "publish_date": "string",
    "content": "string"
}
schema_path = generate_schema(html_path, iteration_rounds=iteration_rounds, schema_template=schema)

# output
print(f"Schema path: {schema_path}")
```

### API 4: parse_with_parser()

Parse HTML using existing parser

```python
from web2json.simple import parse_with_parser

html_path = "html_samples/"
parser_path = "output/sample/parsers/final_parser.py"

# Call the API
result_dir = parse_with_parser(html_path, parser_path)
print(f"Result directory: {result_dir}")
```

### API 5: extract_all()

Complete workflow, return all paths

```python
from web2json.simple import extract_all

html_path = "html_samples/"
iteration_rounds = 3  # default value

# Method 1: auto mode
paths = extract_all(html_path, iteration_rounds=iteration_rounds)

# Method 2: predefined mode
schema = {
    "title": "string",
    "author": "string",
    "publish_date": "string",
    "content": "string"
}
paths = extract_all(html_path, iteration_rounds=iteration_rounds, schema_template=schema)

# output
print(f"Result directory: {paths['result_dir']}")
print(f"Parser path: {paths['parser_path']}")
print(f"Schema path: {paths['schema_path']}")
print(f"Output directory: {paths['output_dir']}")
```

---

## 📄 License

Apache-2.0 License

---

<div align="center">

**Made with ❤️ by the web2json-agent team**

[⭐ Star us on GitHub](https://github.com/ccprocessor/web2json-agent) | [🐛 Report Issues](https://github.com/ccprocessor/web2json-agent/issues) | [📖 Documentation](https://github.com/ccprocessor/web2json-agent)

</div>
