# web2json-agent

**让 AI 自动生成网页解析代码，告别手写 XPath 和 CSS 选择器，轻松得到结构化数据**

[中文](docs/README_zh.md) | [English](../README.md)

## 💡 项目简介

**web2json-agent** 是一个智能数据结构化解析工具，能够**自动分析网页结构并生成高质量的 Python 解析代码，并自动进行数据解析，节省 90% 的开发时间，从几小时到几分钟！**

### 📋 视频演示

https://github.com/user-attachments/assets/772fb610-808e-431d-93b3-d16ca0775b3f

---

## 📊 SWDE 基准测试结果

在 SWDE 数据集上的测评结果（8 个垂直领域，80 个网站，124,291 页面）：

<div align="center">

| 指标 | 分数 |
|------|------|
| **平均精确率 (Precision)** | **91.50%** |
| **平均召回率 (Recall)** | **90.46%** |
| **平均 F1 分数** | **89.93%** |

</div>

---

## 🚀 快速开始

### 通过 pip 安装

```bash
# 1. 安装包
pip install web2json-agent

# 2. 初始化配置
web2json setup

# 模式1：自动模式 (auto) - 快速探索，不确定需要提取哪些字段
web2json -d html_samples/ -o output/result

# 模式2：预定义模式 (predefined) - 明确知道需要提取哪些字段，需要精确控制输出结构
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

MIT License

---
