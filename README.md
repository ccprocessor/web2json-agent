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

---

## 🐍 API Usage

Web2JSON provides four simple APIs for different use cases. All examples are ready to run!

### Example 1: Directly obtain structured data

**Auto Mode** - Let AI automatically filter fields and extract data:

```python
from web2json import Web2JsonConfig, extract_html_to_json

config = Web2JsonConfig(
    name="my_project",
    html_path="html_samples/",
    output_path="output/"
)

result = extract_html_to_json(config)
# Output: output/my_project/result/*.json
print(f"✓ Results saved to: {result}")
```

**Predefined Mode** - Extract only specific fields:

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
# Output: output/articles/result/*.json
print(f"✓ Results saved to: {result}")
```

---

### Example 2: Generate Reusable Parser

Generate a parser once, use it many times:

```python
from web2json import Web2JsonConfig, generate_html_parser

config = Web2JsonConfig(
    name="product_parser",
    html_path="training_samples/",
    output_path="parsers/"
)

parser_path = generate_html_parser(config)
# Output: parsers/product_parser/final_parser.py
print(f"✓ Parser saved: {parser_path}")
```

---

### Example 3: Parse with Existing Parser

Reuse a trained parser on new HTML files:

```python
from web2json import Web2JsonConfig, parse_html_with_parser

config = Web2JsonConfig(
    name="batch_001",
    html_path="new_html_files/",
    output_path="results/",
    parser_path="parsers/product_parser/final_parser.py"
)

result = parse_html_with_parser(config)
# Output: results/batch_001/result/*.json
print(f"✓ Parsed data saved to: {result}")
```

---

### Example 4: Generate Schema Only

Generate a JSON Schema containing field descriptions and XPath:

```python
from web2json import Web2JsonConfig, infer_html_to_schema
import json

config = Web2JsonConfig(
    name="schema_exploration",
    html_path="html_samples/",
    output_path="schemas/"
)

schema_path = infer_html_to_schema(config)
# Output: schemas/schema_exploration/final_schema.json

# View the learned schema
with open(schema_path) as f:
    schema = json.load(f)
    print(json.dumps(schema, indent=2))
```

---

### Configuration Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Project name (creates subdirectory) |
| `html_path` | `str` | Required | Directory with HTML files |
| `output_path` | `str` | `"output"` | Output directory |
| `iteration_rounds` | `int` | `3` | Number of samples for learning |
| `schema` | `Dict` | `None` | Predefined fields (None = auto mode) |
| `parser_path` | `str` | `None` | Parser file (for `parse_html_with_parser`) |

---

### Which API Should I Use?

```python
# Need JSON data immediately? → extract_html_to_json
extract_html_to_json(config)

# Want to inspect schema first? → infer_html_to_schema
infer_html_to_schema(config)

# Need reusable parser? → generate_html_parser
generate_html_parser(config)

# Have parser, need to parse more files? → parse_html_with_parser
parse_html_with_parser(config)
```

---

## 📄 License

Apache-2.0 License

---

<div align="center">

**Made with ❤️ by the web2json-agent team**

[⭐ Star us on GitHub](https://github.com/ccprocessor/web2json-agent) | [🐛 Report Issues](https://github.com/ccprocessor/web2json-agent/issues) | [📖 Documentation](https://github.com/ccprocessor/web2json-agent)

</div>
