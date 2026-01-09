<div align="center">

# 🌐 web2json-agent

**Stop Coding Scrapers, Start Getting Data — from Hours to Seconds**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-00C851?style=for-the-badge&logo=chainlink&logoColor=white)](https://www.langchain.com/)
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

## 🎨 Web UI

### Installation and Launch

```bash
# Enter frontend directory
cd web2json_ui/

# Install dependencies
npm install

# Start development server
npm run dev

# Or build production version
npm run build
```

---

## 📄 License

Apache-2.0 License

---

<div align="center">

**Made with ❤️ by the web2json-agent team**

[⭐ Star us on GitHub](https://github.com/ccprocessor/web2json-agent) | [🐛 Report Issues](https://github.com/ccprocessor/web2json-agent/issues) | [📖 Documentation](https://github.com/ccprocessor/web2json-agent)

</div>
