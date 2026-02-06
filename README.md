<div align="center">

# 🌐 web2json-agent

**Stop Coding Scrapers, Start Getting Data — from Hours to Seconds**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-00C851?style=for-the-badge&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Compatible-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![PyPI](https://img.shields.io/badge/PyPI-1.1.4-blue?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/web2json-agent/)

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

Web2JSON provides five simple APIs. Perfect for databases, APIs, and real-time processing!

### API 1: `extract_data` - Complete Workflow

Extract structured data from HTML in one step (schema + parser + data).

**Auto Mode** - Let AI automatically discover and extract fields:

```python
from web2json import Web2JsonConfig, extract_data

config = Web2JsonConfig(
    name="my_project",
    html_path="html_samples/",
    # iteration_rounds=3  # default 3
    # enable_schema_edit=True  # Uncomment to manually edit schema
)

result = extract_data(config)

# print(result.final_schema)        # Dict: extracted schema
# print(result.parser_code)          # str: generated parser code
# print(result.parsed_data[0])       # List[Dict]: parsed JSON data
```

**Predefined Mode** - Extract only specific fields:

```python
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

result = extract_data(config)
# Returns: ExtractDataResult with schema, code, and data
```

---

### API 2: `extract_schema` - Extract Schema Only

Generate a JSON schema describing the data structure in HTML.

```python
from web2json import Web2JsonConfig, extract_schema

config = Web2JsonConfig(
    name="schema_only",
    html_path="html_samples/",
    # iteration_rounds=3
    # enable_schema_edit=True  # Uncomment to manually edit schema
)

result = extract_schema(config)

# print(result.final_schema)         # Dict: final schema
# print(result.intermediate_schemas) # List[Dict]: iteration history
```

---

### API 3: `infer_code` - Generate Parser Code

Generate parser code from a schema (Dict or from previous step).

```python
from web2json import Web2JsonConfig, infer_code

# Use schema from previous step or define manually
my_schema = {
    "title": "string",
    "author": "string",
    "content": "string"
}

config = Web2JsonConfig(
    name="my_parser",
    html_path="html_samples/",
    schema=my_schema
)
result = infer_code(config)

# print(result.parser_code)  # str: BeautifulSoup parser code
# print(result.schema)       # Dict: schema used
```

---

### API 4: `extract_data_with_code` - Parse with Code

Use parser code to extract data from HTML files.

```python
from web2json import Web2JsonConfig, extract_data_with_code

# Parser code from previous step or loaded from file
parser_code = """
def parse_html(html_content):
    # ... parser implementation
"""

config = Web2JsonConfig(
    name="parse_demo",
    html_path="new_html_files/",
    parser_code=parser_code
)
result = extract_data_with_code(config)

# print(f"Success: {result.success_count}, Failed: {result.failed_count}")
# for item in result.parsed_data:
#     print(f"File: {item['filename']}")
#     print(f"Data: {item['data']}")
```

---

### API 5: `classify_html_dir` - Classify HTML by Layout

Group HTML files by layout similarity (for mixed-layout datasets).

```python
from web2json import Web2JsonConfig, classify_html_dir

config = Web2JsonConfig(
    name="classify_demo",
    html_path="mixed_html/"
)
result = classify_html_dir(config)

# print(f"Found {result.cluster_count} layout types")
# print(f"Noise files: {len(result.noise_files)}")

# for cluster_name, files in result.clusters.items():
#     print(f"{cluster_name}: {len(files)} files")
#     for file in files[:3]:
#         print(f"  - {file}")
```

---

### Configuration Reference

**Web2JsonConfig Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Project name (for identification) |
| `html_path` | `str` | Required | HTML directory or file path |
| `iteration_rounds` | `int` | `3` | Number of samples for learning |
| `schema` | `Dict` | `None` | Predefined schema (None = auto mode) |
| `enable_schema_edit` | `bool` | `False` | Enable manual schema editing |

**Standalone API Parameters:**

| API | Parameters | Returns |
|-----|------------|---------|
| `extract_data` | `config: Web2JsonConfig` | `ExtractDataResult` |
| `extract_schema` | `config: Web2JsonConfig` | `ExtractSchemaResult` |
| `infer_code` | `config: Web2JsonConfig` | `InferCodeResult` |
| `extract_data_with_code` | `config: Web2JsonConfig` | `ParseResult` |
| `classify_html_dir` | `config: Web2JsonConfig` | `ClusterResult` |

**All result objects provide:**
- Direct access to data via object attributes
- `.to_dict()` method for serialization
- `.get_summary()` method for quick stats

---

### Which API Should I Use?

```python
# Need data immediately? → extract_data
config = Web2JsonConfig(name="my_run", html_path="html_samples/")
result = extract_data(config)
print(result.parsed_data)

# Want to review/edit schema first? → extract_schema + infer_code
config = Web2JsonConfig(name="schema_run", html_path="html_samples/")
schema_result = extract_schema(config)

# Edit schema if needed, then generate code
config = Web2JsonConfig(
    name="code_run",
    html_path="html_samples/",
    schema=schema_result.final_schema
)
code_result = infer_code(config)

# Parse with the generated code
config = Web2JsonConfig(
    name="parse_run",
    html_path="new_html_files/",
    parser_code=code_result.parser_code
)
data_result = extract_data_with_code(config)

# Have parser code, need to parse more files? → extract_data_with_code
config = Web2JsonConfig(
    name="parse_more",
    html_path="more_files/",
    parser_code=my_parser_code
)
result = extract_data_with_code(config)

# Mixed layouts (list + detail pages)? → classify_html_dir
config = Web2JsonConfig(name="classify", html_path="mixed_html/")
result = classify_html_dir(config)
```

---

## 📄 License

Apache-2.0 License

---

<div align="center">

**Made with ❤️ by the web2json-agent team**

[⭐ Star us on GitHub](https://github.com/ccprocessor/web2json-agent) | [🐛 Report Issues](https://github.com/ccprocessor/web2json-agent/issues) | [📖 Documentation](https://github.com/ccprocessor/web2json-agent)

</div>
