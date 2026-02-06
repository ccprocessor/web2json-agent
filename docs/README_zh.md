<div align="center">

# 🌐 web2json-agent

**告别爬虫开发，秒级获取网页数据**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-00C851?style=for-the-badge&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Compatible-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![PyPI](https://img.shields.io/badge/PyPI-1.1.4-blue?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/web2json-agent/)

[English](../README.md) | [中文](README_zh.md)

</div>

---

## 📖 什么是 web2json-agent？

基于 AI 的智能网页解析代理，从 HTML 样本自动生成生产级解析器代码，无需手写 XPath/CSS 选择器。

---

## 📋 DEMO


https://github.com/user-attachments/assets/6eec23d4-5bf1-4837-af70-6f0a984d5464


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

### 通过 pip 安装

```bash
# 1. 安装包
pip install web2json-agent

# 2. 初始化配置
web2json setup
```

### 开发者安装

```bash
# 1. 克隆仓库
git clone https://github.com/ccprocessor/web2json-agent
cd web2json-agent

# 2. 以可编辑模式安装
pip install -e .

# 3. 初始化配置
web2json setup
```

---

## 🐍 API 使用

Web2JSON 提供五个简洁的 API，返回内存数据对象。适用于数据库、API 接口和实时处理场景。

### API 1: `extract_data` - 完整工作流

一步从 HTML 提取结构化数据（schema + parser + data）。

**自动模式** - 让 AI 自动发现并提取字段：

```python
from web2json import Web2JsonConfig, extract_data

config = Web2JsonConfig(
    name="my_project",
    html_path="html_samples/",
    # iteration_rounds=3
    # enable_schema_edit=True  # 取消注释以手动编辑 schema
)

result = extract_data(config)

# 打印查看结果
print(result.final_schema)        # Dict: 提取的 schema
print(result.parser_code)          # str: 生成的解析器代码
print(result.parsed_data[0])       # List[Dict]: 解析的 JSON 数据
```

**预定义模式** - 仅提取指定字段：

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
# 返回：ExtractDataResult，包含 schema、code 和 data
```

---

### API 2: `extract_schema` - 仅提取 Schema

生成描述 HTML 数据结构的 JSON schema。

```python
from web2json import Web2JsonConfig, extract_schema

config = Web2JsonConfig(
    name="schema_only",
    html_path="html_samples/",
    iteration_rounds=3
    # enable_schema_edit=True  # 取消注释以手动编辑 schema
)

result = extract_schema(config)

print(result.final_schema)         # Dict: 最终 schema
print(result.intermediate_schemas) # List[Dict]: 迭代历史
```

---

### API 3: `infer_code` - 生成解析器代码

从 schema（Dict 或上一步的结果）生成解析器代码。

```python
from web2json import Web2JsonConfig, infer_code

# 使用上一步的 schema 或手动定义
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

# print(result.parser_code)  # str: BeautifulSoup 解析器代码
# print(result.schema)       # Dict: 使用的 schema
#
# # 保存或立即使用
# with open("my_parser.py", "w") as f:
#     f.write(result.parser_code)
```

---

### API 4: `extract_data_with_code` - 使用代码解析

使用解析器代码从 HTML 文件提取数据。

```python
from web2json import Web2JsonConfig, extract_data_with_code

# 来自上一步的解析器代码或从文件加载
parser_code = """
def parse_html(html_content):
    # ... 解析器实现
"""

config = Web2JsonConfig(
    name="parse_demo",
    html_path="new_html_files/",
    parser_code=parser_code
)
result = extract_data_with_code(config)

print(f"成功: {result.success_count}, 失败: {result.failed_count}")
for item in result.parsed_data:
    print(f"文件: {item['filename']}")
    print(f"数据: {item['data']}")
```

---

### API 5: `classify_html_dir` - 按布局分类 HTML

按布局相似度对 HTML 文件分组（适用于混合布局数据集）。

```python
from web2json import Web2JsonConfig, classify_html_dir

config = Web2JsonConfig(
    name="classify_demo",
    html_path="mixed_html/"
)
result = classify_html_dir(config)

# 直接访问聚类结果
print(f"发现 {result.cluster_count} 种布局类型")
print(f"噪声文件: {len(result.noise_files)}")

# 遍历各个簇
for cluster_name, files in result.clusters.items():
    print(f"{cluster_name}: {len(files)} 个文件")
    for file in files[:3]:
        print(f"  - {file}")
```

---

### 配置参数参考

**Web2JsonConfig 参数：**

| 参数 | 类型 | 默认值 | 说明 |
|-----------|------|---------|-------------|
| `name` | `str` | 必需 | 项目名称（用于标识） |
| `html_path` | `str` | 必需 | HTML 目录或文件路径 |
| `iteration_rounds` | `int` | `3` | 用于学习的样本数量 |
| `schema` | `Dict` | `None` | 预定义 schema（None = 自动模式） |
| `enable_schema_edit` | `bool` | `False` | 启用手动编辑 schema |

**独立 API 参数：**

| API | 参数 | 返回值 |
|-----|------|--------|
| `extract_data` | `config: Web2JsonConfig` | `ExtractDataResult` |
| `extract_schema` | `config: Web2JsonConfig` | `ExtractSchemaResult` |
| `infer_code` | `config: Web2JsonConfig` | `InferCodeResult` |
| `extract_data_with_code` | `config: Web2JsonConfig` | `ParseResult` |
| `classify_html_dir` | `config: Web2JsonConfig` | `ClusterResult` |

**所有结果对象都提供：**
- 通过对象属性直接访问数据
- `.to_dict()` 方法用于序列化
- `.get_summary()` 方法用于快速统计

---

### 应该使用哪个 API？

```python
# 需要立即获取数据？ → extract_data
config = Web2JsonConfig(name="my_run", html_path="html_samples/")
result = extract_data(config)
print(result.parsed_data)

# 想先查看/编辑 schema？ → extract_schema + infer_code
config = Web2JsonConfig(name="schema_run", html_path="html_samples/")
schema_result = extract_schema(config)

# 根据需要编辑 schema，然后生成代码
config = Web2JsonConfig(
    name="code_run",
    html_path="html_samples/",
    schema=schema_result.final_schema
)
code_result = infer_code(config)

# 使用生成的代码进行解析
config = Web2JsonConfig(
    name="parse_run",
    html_path="new_html_files/",
    parser_code=code_result.parser_code
)
data_result = extract_data_with_code(config)

# 已有解析器代码，需要解析更多文件？ → extract_data_with_code
config = Web2JsonConfig(
    name="parse_more",
    html_path="more_files/",
    parser_code=my_parser_code
)
result = extract_data_with_code(config)

# 混合布局（列表页 + 详情页）？ → classify_html_dir
config = Web2JsonConfig(name="classify", html_path="mixed_html/")
result = classify_html_dir(config)
```

---

## 📄 许可证

Apache-2.0 License

---

<div align="center">

**用 ❤️ 打造 by web2json-agent 团队**

[⭐ 在 GitHub 上给我们点个 Star](https://github.com/ccprocessor/web2json-agent) | [🐛 报告问题](https://github.com/ccprocessor/web2json-agent/issues) | [📖 文档](https://github.com/ccprocessor/web2json-agent)

</div>
