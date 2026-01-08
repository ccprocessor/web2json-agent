# web2json-agent

**Let AI automatically generate web parsing code, say goodbye to manual XPath and CSS selectors, easily get structured data**

[English](README.md) | [中文](docs/README_zh.md)

## 📋 Demo


https://github.com/user-attachments/assets/6eec23d4-5bf1-4837-af70-6f0a984d5464


---

## 📊 SWDE Benchmark Results

Evaluated on the SWDE dataset (8 verticals, 80 websites, 124,291 pages):

<div align="center">
    
| Metric |Precision|Recall|F1 Score|
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

# Mode 1: Auto mode (auto) - Quick exploration, unsure which fields to extract
web2json -d html_samples/ -o output/result

# Mode 2: Predefined mode (predefined) - Know exactly which fields to extract, need precise output control
web2json -d html_samples/ -o output/result --interactive-schema
```

---
## 🎨 Web UI

The project provides a visual Web UI interface for convenient browser-based operations.

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

MIT License

---
