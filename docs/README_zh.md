<div align="center">

# 🌐 web2json-agent

**告别爬虫开发，秒级获取网页数据**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3b82f6?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.0%2B-22c55e?style=for-the-badge&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Compatible-ef4444?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![PyPI](https://img.shields.io/badge/PyPI-1.1.2-f97316?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/web2json-agent/)

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

## 🎨 Web UI 界面

项目提供了一个可视化的 Web UI 界面，方便在浏览器中操作。

### 安装和启动

```bash
# 进入前端目录
cd web2json_ui/

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 或构建生产版本
npm run build
```

---

## 📄 许可证

Apache-2.0 License

---

<div align="center">

**用 ❤️ 打造 by web2json-agent 团队**

[⭐ GitHub 点个 Star](https://github.com/ccprocessor/web2json-agent) | [🐛 报告问题](https://github.com/ccprocessor/web2json-agent/issues) | [📖 文档](https://github.com/ccprocessor/web2json-agent)

</div>
