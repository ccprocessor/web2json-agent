# web2json-agent

**Let AI automatically generate web parsing code, say goodbye to manual XPath and CSS selectors, easily get structured data**

[English](README.md) | [中文文档](docs/README_zh.md)

## 💡 Project Introduction

**web2json-agent** is an intelligent data parsing tool that can **automatically analyze web page structure and generate high-quality Python parser code with automatic data parsing, saving 80% of development time, from hours to minutes!**

### 📋 Video Demo

https://github.com/user-attachments/assets/772fb610-808e-431d-93b3-d16ca0775b3f

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
## 🎨 Web UI Frontend Interface

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
