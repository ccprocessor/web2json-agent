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

## 🐍 API 使用

### API 1: extract_data()

从HTML文件生成 解析代码/Schema/抽取数据

**Auto模式** - 让AI自动检测并提取所有字段：

```python
from web2json import Web2JsonConfig, extract_data

config = Web2JsonConfig(
    name="news_auto",            # 运行名称（会创建 output/news_auto/）
    html_path="html_samples/",   # 包含HTML文件的目录
    iteration_rounds=3,          # AI使用多少个样本来学习结构
    output_dir="output/",        # 结果保存位置
    outputs=["data", "code", "schema"]     # 保留什么：解析后的数据 + 生成的解析器 + schema(含Xpath)
)

result_dir = extract_data(config)
print("保存到:", result_dir)
```

**Predefined模式** - 只提取指定的字段：

```python
from web2json import Web2JsonConfig, extract_data

config = Web2JsonConfig(
    name="news_schema",
    html_path="html_samples/",
    output_dir="output/",

    # 指定要提取的字段
    schema={
        "title": "string",
        "author": "string",
        "publish_date": "string",
        "content": "string"
    },

    outputs=["data", "code", "schema"]  # 保留数据 + 解析器 + schema
)

result_dir = extract_data(config)
print("保存到:", result_dir)
```

**配置参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | str | 必需 | 运行名称（在output_dir下创建子目录） |
| `html_path` | str | 必需 | 包含HTML文件的目录 |
| `iteration_rounds` | int | 3 | 用于学习的HTML样本数量 |
| `output_dir` | str | "output" | 主输出目录 |
| `schema` | Dict | None | 字段定义（None=Auto模式，Dict=Predefined模式） |
| `outputs` | List[str] | ["data", "code", "schema"] | 要保留的输出类型 |

**输出类型说明：**

- `"data"` - 解析后的JSON数据文件（保存在 `result/` 目录）
- `"code"` - 生成的解析器代码（保存在 `parsers/` 目录）
- `"schema"` - 学习到的schema定义（保存在 `schemas/` 目录）

---

### API 2: parse_data()

使用已有的训练好的解析器解析新的HTML文件。

```python
from web2json import Web2JsonConfig, parse_data

config = Web2JsonConfig(
    name="new_batch",
    html_path="new_html_samples/",                            # 要解析的新HTML文件
    parser_path="output/news_schema/parsers/final_parser.py", # 之前训练好的解析器
    output_dir="output/",
    outputs=["data"]                                          # 只保留解析后的JSON数据
)

result_dir = parse_data(config)
print("保存到:", result_dir)
```

**适用场景：**
- 已经有之前运行生成的训练好的解析器
- 需要解析结构相同的新HTML批次
- 生产环境中的增量数据处理

---

## 📄 许可证

Apache-2.0 License

---

<div align="center">

**用 ❤️ 打造 by web2json-agent 团队**

[⭐ GitHub 点个 Star](https://github.com/ccprocessor/web2json-agent) | [🐛 报告问题](https://github.com/ccprocessor/web2json-agent/issues) | [📖 文档](https://github.com/ccprocessor/web2json-agent)

</div>
