# Web2JsonAgent

Web2JSON-Agent 完整使用指南

## Web2JSON-Agent 是什么

**Web2JSON-Agent** 是一个 AI 驱动的 Web 数据提取工具，通过大模型自动分析 HTML 结构，迭代学习生成最优 Schema，并自动生成生产级 BeautifulSoup Parser 代码。

### 核心特性

- 🤖 **AI 自动分析**：无需手写 XPath/CSS Selector，AI 自动识别数据模式
- 🔄 **迭代学习**：从多个样本中学习，生成最优解析方案
- 🎯 **布局聚类**：自动识别混合布局（列表页/详情页），分别处理
- 🚀 **全自动工作流**：从 HTML 输入到结构化数据输出，一步到位

### 适用场景

- 电商数据采集（商品信息、价格、评论）
- 新闻内容聚合（标题、正文、作者、时间）
- 学术论文抓取（作者、摘要、关键词）
- 招聘信息提取（职位、薪资、要求）
- 任何需要批量提取 Web 结构化数据的场景

这份指南将带你从零开始，完成 Web2JSON-Agent 的安装、配置、使用全流程。

---

## 📦 第一阶段：环境安装

### 步骤 1：安装核心包

```bash
pip install web2json-agent
```

### 步骤 2：验证安装

```bash
python -c "from web2json import extract_data, Web2JsonConfig; print('✅ 安装成功')"
```

---

## ⚙️ 第二阶段：配置 API 密钥

Web2JSON-Agent 需要调用大模型 API（支持 OpenAI / Claude 等兼容接口）。你可以通过以下三种方式配置 API 密钥。

### 方式一：交互式配置向导（推荐）

最简单的方式，系统会自动引导你完成所有配置：

```bash
web2json setup
```

配置向导会完成：
- ✅ API 密钥设置
- ✅ 模型选择（Claude / GPT-4等）
- ✅ 迭代参数配置
- ✅ 自动生成 `.env` 配置文件

---

### 方式二：手动创建配置文件

```bash
# 生成 .env 配置文件模板
web2json init

# 编辑 .env 文件，填入以下必需配置
```

`.env` 文件示例（至少需要前两项）：

```bash
# 必需配置
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1

# 可选配置（推荐使用默认值）
DEFAULT_MODEL=claude-sonnet-4-5-20250929
DEFAULT_TEMPERATURE=0.3
DEFAULT_ITERATION_ROUNDS=3
```

---

### 方式三：环境变量设置

如果你不想使用配置文件，可以直接设置环境变量。

**Windows PowerShell：**

```powershell
$env:OPENAI_API_KEY="your-api-key"
$env:OPENAI_API_BASE="https://api.openai.com/v1"
```

**Windows CMD：**

```cmd
set OPENAI_API_KEY=your-api-key
set OPENAI_API_BASE=https://api.openai.com/v1
```

**Linux / Mac：**

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_BASE="https://api.openai.com/v1"
```

---

### 验证配置

```bash
# 检查配置是否正确
web2json check

# 检查配置并测试 API 连接
web2json check --test-api
```

---

## 🎯 第三阶段：布局识别（可选但推荐的前置步骤）

### 核心能力：智能处理混合布局

**Web2JSON-Agent 的一大亮点是能够处理混合布局的 HTML 输入。**

在实际的数据采集场景中，你可能会遇到：
- 批量下载的网页包含列表页和详情页
- 同一目录下混合了商品页、评论页、搜索结果页
- 爬虫抓取时未区分不同类型的页面

**如果直接对混合布局的 HTML 使用 `extract_data()`，会导致：**
- ❌ 生成的 Schema 混乱（混合了不同页面类型的字段）
- ❌ Parser 代码提取准确率低（无法适配所有页面类型）
- ❌ 解析结果字段缺失或数据错误

**解决方案：使用布局聚类功能**

Web2JSON-Agent 提供了 **`classify_html_dir()`** API，能够：
- ✅ 自动分析 HTML 结构相似度
- ✅ 将不同布局的页面自动分组
- ✅ 为每种布局生成专属的高质量 Parser

---

### 步骤 0：判断你的 HTML 是否需要聚类

**什么是"相同布局"？**

指页面的 HTML 结构、数据字段位置、DOM 层级关系基本一致。

**✅ 相同布局示例（可直接使用）：**
- 同一个网站的所有商品详情页
- 同一个新闻站的所有文章页面
- 同一个招聘网站的所有职位详情页
- 从同一 URL 模板爬取的页面（如 `/product/{id}`）

**⚠️ 混合布局示例（建议先聚类）：**
- 不同网站的相同类型页面（即使都是文章，HTML 结构也可能完全不同）
- 列表页 + 详情页混在一起
- 商品页 + 评论页 + 搜索结果页混在一起
- 爬虫未分类的批量下载页面

---

### 快速判断方法

1. **目测判断**：打开 2-3 个 HTML 文件，页面"长得很像"（标题、内容、布局位置相似）→ 相同布局
2. **文件名判断**：HTML 来自同一 URL 模板（如 `/product/123`, `/product/456`）→ 相同布局
3. **数据字段判断**：期望提取的字段在所有页面都存在（如"标题"、"价格"、"作者"）→ 相同布局

**如果不确定，建议使用以下代码快速分析：**

```python
from web2json import Web2JsonConfig, classify_html_dir

# 分析HTML布局
config = Web2JsonConfig(
    name="layout_check",
    html_path="html_samples/"
)
result = classify_html_dir(config)

# 查看结果
print(f"✅ 识别出 {result.cluster_count} 种布局")

if result.cluster_count == 1:
    print("📌 所有页面属于相同布局，可直接使用 extract_data()")
else:
    print(f"📌 包含 {result.cluster_count} 种不同布局，建议分别处理")
    for cluster_name, files in result.clusters.items():
        print(f"   - {cluster_name}: {len(files)} 个文件")
```

---

### 使用决策流程

```
你的 HTML 文件
    │
    ├──→ 【不确定布局类型】
    │       │
    │       └──→ 运行 classify_html_dir() 分析
    │               │
    │               ├──→ cluster_count = 1  → 相同布局 → 跳到第四阶段
    │               └──→ cluster_count > 1  → 混合布局 → 继续下一步
    │
    ├──→ 【确定是相同布局】
    │       │
    │       └──→ 直接跳到第四阶段，使用 extract_data()
    │
    └──→ 【确定是混合布局】
            │
            └──→ 使用下方的"混合布局处理流程"
```

---

### 混合布局处理完整示例

当你的 HTML 包含多种页面布局时，使用以下流程（同demo.py）：

**方式一：Python API（推荐）**

```python
from web2json import Web2JsonConfig, classify_html_dir, extract_data
import os

# Step 1: Classify HTML files by layout
classify_config = Web2JsonConfig(
    name="classify_demo",
    html_path="input_html/mixed_input/",
    # save=['report', 'files'],  # Save cluster report and copy files to subdirectories
    # output_path="./cluster_analysis",  # Custom output directory
)

classify_result = classify_html_dir(classify_config)

print(f"\n{'='*60}")
print(f"布局分类完成")
print(f"{'='*60}")
print(f"识别出的布局类型: {classify_result.cluster_count}")
print(f"噪声文件: {len(classify_result.noise_files)}")

for cluster_name, files in classify_result.clusters.items():
    print(f"\n{cluster_name}: {len(files)} 个文件")
    for file in files[:3]:
        print(f"  - {os.path.basename(file)}")

# Step 2: Extract data for each cluster
print(f"\n{'='*60}")
print(f"开始对每个布局类型进行数据提取")
print(f"{'='*60}")

extraction_results = {}

for cluster_name, files in classify_result.clusters.items():
    print(f"\n处理 {cluster_name} ({len(files)} 个文件)...")

    # Get cluster directory path
    cluster_dir = os.path.join(
        classify_config.output_path or "output",
        classify_config.name,
        "clusters",
        cluster_name
    )

    # Create extraction config for this cluster
    extract_config = Web2JsonConfig(
        name=f"{classify_config.name}_{cluster_name}",
        html_path=cluster_dir,
        save=['schema', 'code', 'data'],  # Save schema, code, and extracted data
        iteration_rounds=min(3, len(files)),  # Use min(3, file_count) samples for learning
    )

    # Extract data
    try:
        result = extract_data(extract_config)
        extraction_results[cluster_name] = result
        print(f"✓ {cluster_name} 数据提取完成")
        print(f"  生成的 schema 字段数: {len(result.final_schema) if result.final_schema else 0}")
        print(f"  解析的文件数: {len(result.parsed_data)}")
    except Exception as e:
        print(f"✗ {cluster_name} 数据提取失败: {e}")
        extraction_results[cluster_name] = None

# Step 3: Summary
print(f"\n{'='*60}")
print(f"全部完成")
print(f"{'='*60}")
print(f"总布局类型: {classify_result.cluster_count}")
print(f"成功提取数据的类型: {sum(1 for r in extraction_results.values() if r is not None)}")

for cluster_name, result in extraction_results.items():
    if result:
        output_dir = os.path.join("output", f"{classify_config.name}_{cluster_name}")
        print(f"\n{cluster_name}:")
        print(f"  结果目录: {output_dir}")
        print(f"  解析文件数: {len(result.parsed_data)}")
        print(f"  Schema 字段: {list(result.final_schema.keys()) if result.final_schema else []}")
```

**方式二：命令行工具**

```bash
# 自动聚类并分别生成 Parser
web2json -d mixed_html/ -o output/site --cluster
```

**输出结构：**

```
output/site_cluster0/          # 布局类型0的Parser和数据
output/site_cluster1/          # 布局类型1的Parser和数据
output/site_noise/             # 无法归类的异常页面
output/site_cluster_info.txt   # 详细聚类报告
```

---

### 聚类参数调优（可选）

如果聚类结果不理想，可以在 `.env` 中调整参数：

```bash
# 距离阈值（1 - 相似度），越小要求相似度越高
# 推荐范围: 0.03-0.10，默认: 0.05
CLUSTER_EPS=0.05

# 形成簇的最小样本数
# 推荐: 2
CLUSTER_MIN_SAMPLES=2
```

---

## 🚀 第四阶段：数据提取核心使用场景

> **💡 提示**：如果你的 HTML 是混合布局，请先完成第三阶段的布局识别和分组，再使用以下场景中的 API。

### 场景一：快速提取数据（一键模式）

**最常用场景**：你有一批 HTML 文件，想直接获取结构化数据。

```python
from web2json import Web2JsonConfig, extract_data

# 配置项目
config = Web2JsonConfig(
    name="my_project",           # 项目名称
    html_path="html_samples/"    # HTML文件目录
)

# 一键提取：Schema + Parser + 数据
result = extract_data(config)

print("✅ 处理完成！")
print(f"📊 Schema字段数: {len(result.final_schema)}")
print(f"🔧 Parser代码: {len(result.parser_code)} 字符")
print(f"📦 数据条数: {len(result.parsed_data)}")

# 查看第一条数据
if result.parsed_data:
    print(f"\n示例数据:\n{result.parsed_data[0]}")
```

**执行流程：**

1. 从 `html_samples/` 选取前 3 个 HTML（默认）进行**迭代学习**
2. AI 分析 HTML 结构，提取 Schema（自动合并多个样本）
3. 基于 Schema 生成 BeautifulSoup Parser 代码
4. **自动解析目录中所有 HTML 文件**（不仅限于学习样本）
5. 返回结构化数据（JSON 格式）

---

### 场景二：指定字段提取（预定义 Schema 模式）

**适用场景**：你明确知道要提取哪些字段。

```python
from web2json import Web2JsonConfig, extract_data

# 预定义需要提取的字段
my_schema = {
    "title": "string",        # 文章标题
    "author": "string",       # 作者
    "publish_date": "string", # 发布日期
    "content": "string",      # 正文内容
    "tags": "list"           # 标签（数组）
}

config = Web2JsonConfig(
    name="articles",
    html_path="html_samples/",
    schema=my_schema  # 传入预定义 Schema
)

result = extract_data(config)

print(f"✅ 成功提取 {len(result.parsed_data)} 条数据")
for item in result.parsed_data[:3]:
    print(f"\n标题: {item['data'].get('title')}")
    print(f"作者: {item['data'].get('author')}")
```

**预定义模式的优势：**
- 只提取你关心的字段，避免冗余
- 可以指定字段名称（AI 会寻找对应内容）
- 适合需求明确的数据采集任务

---

### 场景三：分步执行（Schema 审查 + 代码生成）

**适用场景**：需要先审查 AI 提取的 Schema，确认无误后再生成代码。

```python
from web2json import Web2JsonConfig, extract_schema, infer_code, extract_data_with_code

# 步骤1: 提取 Schema
print("步骤1: 提取数据Schema...")
config = Web2JsonConfig(
    name="schema_review",
    html_path="html_samples/"
)
schema_result = extract_schema(config)

print(f"✅ Schema提取完成: {schema_result.final_schema}")

# 【可选】手动编辑 schema_result.final_schema
# 比如删除不需要的字段、重命名字段等

# 步骤2: 生成 Parser 代码
print("\n步骤2: 生成Parser代码...")
config = Web2JsonConfig(
    name="code_gen",
    html_path="html_samples/",
    schema=schema_result.final_schema  # 使用提取的Schema（可编辑）
)
code_result = infer_code(config)

print(f"✅ 代码生成完成: {len(code_result.parser_code)} 字符")

# 步骤3: 使用生成的代码批量解析
print("\n步骤3: 批量解析数据...")
config = Web2JsonConfig(
    name="parse_data",
    html_path="html_samples/",
    parser_code="output/code_gen/parsers/final_parser.py"  # 使用生成的 Parser 文件路径
)
data_result = extract_data_with_code(config)

print(f"✅ 成功解析 {data_result.success_count} 个文件")
print(f"❌ 失败 {data_result.failed_count} 个文件")
```

---

### 场景四：重用已生成的 Parser

**适用场景**：已经有生成好的 Parser 代码，需要解析新的 HTML 文件。

```python
from web2json import Web2JsonConfig, extract_data_with_code

# 使用已有的 Parser 文件
config = Web2JsonConfig(
    name="new_batch",
    html_path="new_html_files/",
    parser_code="output/blog/parsers/final_parser.py"  # 直接传入 .py 文件路径
)

result = extract_data_with_code(config)

print(f"✅ 成功: {result.success_count}, 失败: {result.failed_count}")

# 查看解析结果
for item in result.parsed_data:
    print(f"\n文件: {item['filename']}")
    print(f"数据: {item['data']}")
```

---

## 💻 命令行工具使用

Web2JSON-Agent 提供了完整的命令行工具，支持所有核心功能。

### 1. 配置管理

```bash
# 交互式配置向导（推荐）
web2json setup

# 生成配置文件模板
web2json init

# 检查配置
web2json check

# 检查配置并测试 API
web2json check --test-api
```

---

### 2. 一键生成 Parser

```bash
# 基础用法
web2json -d input_html/ -o output/blog

# 指定迭代轮数（学习样本数量）
web2json -d input_html/ -o output/blog --iteration-rounds 3

# 指定域名（用于输出目录命名）
web2json -d input_html/ -o output/blog --domain example.com
```

**命令执行流程：**

1. 从 `input_html/` 选取前 N 个 HTML（N = iteration_rounds）
2. 迭代学习生成最优 Schema
3. 生成 BeautifulSoup Parser 代码
4. **自动解析所有 HTML 文件**
5. 结果保存到 `output/blog/result/` 目录

---

### 3. 布局聚类模式（混合布局处理）

**说明**：详细的布局聚类说明和示例请参考**第三阶段：布局识别**。

```bash
# 命令行快捷方式：自动聚类并分别生成 Parser
web2json -d mixed_html/ -o output/site --cluster
```

**输出结构：**

```
output/site_cluster0/          # 布局类型0的Parser和数据
output/site_cluster1/          # 布局类型1的Parser和数据
output/site_noise/             # 无法归类的异常页面
output/site_cluster_info.txt   # 详细聚类报告
```

---

### 4. 直接运行生成的 Parser

生成的 Parser 是标准的 Python 文件，可以独立运行：

```bash
# 解析本地 HTML 文件
python output/blog/final_parser.py sample.html

# 解析 URL（需要网络请求）
python output/blog/final_parser.py https://example.com/article
```

---

## 📝 完整示例脚本

```python
#!/usr/bin/env python3
"""
Web2JSON-Agent 完整使用示例
演示从环境检查到数据提取的完整流程
"""
import os
from pathlib import Path
from web2json import Web2JsonConfig, extract_data

def main():
    # 环境检查
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️ 请先配置 OPENAI_API_KEY")
        print("运行: web2json setup")
        return

    if not os.environ.get("OPENAI_API_BASE"):
        print("⚠️ 请先配置 OPENAI_API_BASE")
        return

    print("=" * 60)
    print("Web2JSON-Agent 完整使用示例")
    print("=" * 60)

    # 检查 HTML 文件
    html_dir = Path("html_samples")
    if not html_dir.exists() or not list(html_dir.glob("*.html")):
        print(f"⚠️ 未找到 HTML 文件: {html_dir}/")
        print("请将 HTML 文件放在 html_samples/ 目录")
        return

    html_files = list(html_dir.glob("*.html"))
    print(f"\n[1/3] 发现 {len(html_files)} 个 HTML 文件")

    # 一键提取数据
    print("\n[2/3] 开始数据提取...")
    config = Web2JsonConfig(
        name="demo",
        html_path=str(html_dir)
    )

    try:
        result = extract_data(config)
        print(f"✅ 数据提取完成")
        print(f"  - Schema 字段数: {len(result.final_schema)}")
        print(f"  - Parser 代码: {len(result.parser_code)} 字符")
        print(f"  - 解析数据: {len(result.parsed_data)} 条")
    except Exception as e:
        print(f"❌ 提取失败: {str(e)}")
        return

    # 展示结果
    print("\n[3/3] 结果预览...")

    print("\n📊 提取的 Schema:")
    for field, field_type in list(result.final_schema.items())[:5]:
        print(f"  - {field}: {field_type}")
    if len(result.final_schema) > 5:
        print(f"  ... 还有 {len(result.final_schema) - 5} 个字段")

    print("\n📦 解析数据（前3条）:")
    for i, item in enumerate(result.parsed_data[:3], 1):
        print(f"\n  [{i}] 文件: {item['filename']}")
        data = item['data']
        for key, value in list(data.items())[:3]:
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"      {key}: {value}")

    print("\n" + "=" * 60)
    print("✅ 示例完成！")
    print(f"\n📁 输出目录: output/demo/")
    print(f"  - Schema: output/demo/schemas/final_schema.json")
    print(f"  - Parser: output/demo/final_parser.py")
    print(f"  - 数据: output/demo/result/*.json")

if __name__ == "__main__":
    main()
```

---

## 🔍 API 参考文档

本节提供 Web2JSON-Agent 五大核心 API 的详细参考文档。

### 1. `extract_data` - 完整工作流（推荐）

**功能**：一步到位，完成 Schema 提取、Parser 生成、数据解析全流程。

**使用场景**：最常用的 API，适合快速获取结构化数据。

```python
from web2json import Web2JsonConfig, extract_data

# 自动模式（AI 自动发现字段）
config = Web2JsonConfig(
    name="my_project",
    html_path="html_samples/",
    # iteration_rounds=3  # 可选，默认3
)

result = extract_data(config)

# 返回 ExtractDataResult 对象
print(result.final_schema)      # Dict: 提取的 Schema
print(result.parser_code)        # str: 生成的 Parser 代码
print(result.parsed_data)        # List[Dict]: 解析的数据
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | 必填 | 项目名称 |
| `html_path` | `str` | 必填 | HTML 目录或文件路径 |
| `iteration_rounds` | `int` | `3` | 迭代学习样本数量 |
| `schema` | `Dict` | `None` | 预定义 Schema（None = 自动模式） |
| `enable_schema_edit` | `bool` | `False` | 是否启用 Schema 手动编辑 |

**返回值：**

```python
class ExtractDataResult:
    final_schema: Dict[str, str]           # 最终 Schema
    parser_code: str                       # 生成的 Parser 代码
    parsed_data: List[Dict[str, Any]]      # 解析的数据
    success_count: int                     # 成功数量
    failed_count: int                      # 失败数量
```

---

### 2. `extract_schema` - Schema 提取

**功能**：仅提取 Schema，不生成代码，适合需要审查 Schema 的场景。

```python
from web2json import Web2JsonConfig, extract_schema

config = Web2JsonConfig(
    name="schema_only",
    html_path="html_samples/",
    # iteration_rounds=5  # 可增加样本数提高准确度
)

result = extract_schema(config)

print(result.final_schema)         # Dict: 最终 Schema
print(result.intermediate_schemas) # List[Dict]: 迭代过程
```

**返回值：**

```python
class ExtractSchemaResult:
    final_schema: Dict[str, str]              # 最终 Schema
    intermediate_schemas: List[Dict[str, str]] # 每轮迭代的 Schema
```

---

### 3. `infer_code` - 生成 Parser 代码

**功能**：根据 Schema 生成 BeautifulSoup Parser 代码。

```python
from web2json import Web2JsonConfig, infer_code

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

print(result.parser_code)  # str: BeautifulSoup 代码
print(result.schema)       # Dict: 使用的 Schema
```

**返回值：**

```python
class InferCodeResult:
    parser_code: str              # 生成的 Parser 代码
    schema: Dict[str, str]        # 使用的 Schema
```

---

### 4. `extract_data_with_code` - 使用代码解析

**功能**：使用已有的 Parser 代码批量解析 HTML 文件。

**参数说明**：
- `parser_code`：支持两种输入方式
  - **推荐方式**：直接传入 `.py` 文件路径（如 `"output/blog/parsers/final_parser.py"`）
    - 系统会自动检测是否为文件路径（包含 `.py` 或路径分隔符）
    - 如果文件不存在，会给出明确的错误提示
  - 向后兼容：传入 Python 代码字符串
    - 适用于从数据库或其他来源动态加载的代码

**使用场景**：
- 已有生成好的 Parser，需要解析新的相同结构的 HTML 文件
- 批量处理大量 HTML 文件
- 在生产环境中重用经过验证的 Parser

```python
from web2json import Web2JsonConfig, extract_data_with_code

# 方式1：使用文件路径（推荐）
config = Web2JsonConfig(
    name="parse_new",
    html_path="new_html_files/",
    parser_code="output/blog/parsers/final_parser.py"  # 直接传入 .py 文件路径
)

result = extract_data_with_code(config)

print(f"成功: {result.success_count}, 失败: {result.failed_count}")

for item in result.parsed_data:
    print(f"文件: {item['filename']}")
    print(f"数据: {item['data']}")
```

**返回值：**

```python
class ParseResult:
    parsed_data: List[Dict[str, Any]]  # 解析的数据
    success_count: int                 # 成功数量
    failed_count: int                  # 失败数量
```

**注意事项**：
- 文件路径支持相对路径和绝对路径
- HTML 文件可以是单个文件或目录（目录会自动处理所有 .html 文件）
- 解析失败的文件不会中断整个流程，会在 `failed_count` 中统计

---

### 5. `classify_html_dir` - 布局聚类（前置步骤）

**功能**：根据 HTML 结构相似度自动分组，**建议在第三阶段作为前置步骤使用**。

**使用场景**：
- 不确定 HTML 是否为混合布局时，先用此 API 快速分析
- 确定为混合布局时，用此 API 进行自动分组

**详细使用方法请参考：第三阶段 - 布局识别**

```python
from web2json import Web2JsonConfig, classify_html_dir

config = Web2JsonConfig(
    name="classify_demo",
    html_path="mixed_html/"
)

result = classify_html_dir(config)

print(f"识别出 {result.cluster_count} 种布局")
print(f"噪音文件: {len(result.noise_files)}")

for cluster_name, files in result.clusters.items():
    print(f"{cluster_name}: {len(files)} 个文件")
```

**返回值：**

```python
class ClusterResult:
    clusters: Dict[str, List[str]]  # 簇名称 -> 文件列表
    noise_files: List[str]          # 无法归类的文件
    cluster_count: int              # 簇数量
```

---

## 🔍 常见问题解答（FAQ）

### Q1: 如何确认环境配置是否正确？

**方法1：使用内置检查命令**

```bash
# 检查配置
web2json check

# 检查配置并测试 API 连接
web2json check --test-api
```

**方法2：Python 代码检查**

```python
import os

print("OPENAI_API_KEY:", "✅ 已设置" if os.environ.get("OPENAI_API_KEY") else "❌ 未设置")
print("OPENAI_API_BASE:", "✅ 已设置" if os.environ.get("OPENAI_API_BASE") else "❌ 未设置")
```

**方法3：命令行检查**

```bash
# Windows PowerShell
echo $env:OPENAI_API_KEY

# Linux/Mac
echo $OPENAI_API_KEY
```

---

### Q2: 如何选择配置方式（环境变量 vs 配置文件）？

**推荐使用配置文件（`.env`）：**

```bash
# 运行配置向导（最简单）
web2json setup

# 或手动创建配置文件
web2json init
# 然后编辑 .env 文件
```

**优势：**
- 配置持久化，无需每次设置
- 支持更多高级参数（模型、温度、迭代轮数等）
- 便于版本控制和团队协作

---

### Q3: Web2JSON-Agent 默认就是批量处理吗？

是的！只需指定 HTML 目录，系统会自动处理所有文件。

```python
from web2json import Web2JsonConfig, extract_data

config = Web2JsonConfig(
    name="batch_demo",
    html_path="html_samples/"  # 目录路径
)

result = extract_data(config)

print(f"✅ 成功解析 {result.success_count} 个文件")
```

**执行流程：**

1. 选取前 N 个文件（N = iteration_rounds）进行迭代学习
2. 生成 Parser 代码
3. **自动解析目录中所有 HTML 文件**（不仅限于学习样本）

---

### Q4: HTML 文件包含多种页面布局怎么办？

**答案**：Web2JSON-Agent 提供了强大的混合布局处理能力！

如果你的 HTML 是混合布局（如列表页+详情页），请使用**第三阶段：布局识别**中介绍的布局聚类功能。

**快速使用：**

**命令行：**

```bash
web2json -d mixed_html/ -o output/site --cluster
```

**Python API：**

```python
from web2json import Web2JsonConfig, classify_html_dir

# 快速分析布局
config = Web2JsonConfig(name="check", html_path="mixed_html/")
result = classify_html_dir(config)

if result.cluster_count == 1:
    print("相同布局，直接使用 extract_data()")
else:
    print(f"包含 {result.cluster_count} 种布局，建议分别处理")
    # 详细处理流程见第三阶段文档
```

**详细说明和完整示例请参考：第三阶段 - 布局识别**

---

### Q5: 生成的文件保存在哪里？

所有输出都在 `output/<项目名称>/` 目录下：

```
output/my_project/
├── schemas/              # Schema 迭代过程
│   ├── final_schema.json
│   └── ...
├── parsers/              # 每轮迭代的 Parser
│   ├── parser_round_1.py
│   └── ...
├── final_parser.py       # 最终 Parser（可直接使用）
├── result/               # 解析结果（JSON 文件）
│   ├── sample1.json
│   └── ...
└── html_original/        # 原始 HTML 备份
```

---

### Q6: 如何手动编辑 Schema？

启用 Schema 编辑模式，系统会在生成 Schema 后暂停，允许你手动编辑。

**配置文件（.env）：**

```bash
ENABLE_SCHEMA_EDIT=true
```

**代码中设置：**

```python
config = Web2JsonConfig(
    name="my_project",
    html_path="html_samples/",
    enable_schema_edit=True  # 启用手动编辑
)

result = extract_data(config)
```

**工作流程：**

1. AI 提取 Schema 后暂停
2. Schema 保存到 `output/my_project/schemas/final_schema.json`
3. 手动编辑该文件（删除不需要的字段、重命名等）
4. 按任意键继续，系统使用编辑后的 Schema

---

### Q7: 如何控制提取的字段数量？

**方法1：使用预定义 Schema**

```python
# 只提取你关心的字段
my_schema = {
    "title": "string",
    "author": "string",
    "content": "string"
}

config = Web2JsonConfig(
    name="custom_fields",
    html_path="html_samples/",
    schema=my_schema  # 指定字段
)

result = extract_data(config)
```

**方法2：启用 Schema 编辑模式**

让 AI 先提取，然后手动删除不需要的字段。

---

### Q8: 为什么字段提取不准确？

**可能原因1：样本数量不足**

```python
# 增加迭代轮数（学习更多样本）
config = Web2JsonConfig(
    name="more_samples",
    html_path="html_samples/",
    iteration_rounds=5  # 默认3，可增加到5-10
)
```

**可能原因2：字段命名不清晰**

使用预定义 Schema 明确字段语义：

```python
my_schema = {
    "product_title": "string",  # 明确指定为商品标题
    "product_price": "string",  # 明确指定为价格
}
```

**可能原因3：HTML 结构差异大**

先使用布局聚类模式分组：

```bash
web2json -d html_samples/ -o output/demo --cluster
```

---

### Q9: 生成的 Parser 可以用于生产环境吗？

可以！生成的代码是标准的 Python + BeautifulSoup，可直接集成到项目中。

**使用方式1：作为模块导入**

```python
import sys
sys.path.append("output/blog/")
from final_parser import parse_html

with open("new_file.html", "r") as f:
    html_content = f.read()

data = parse_html(html_content)
print(data)
```

**使用方式2：命令行调用**

```bash
python output/blog/final_parser.py sample.html
```

**使用方式3：通过 API 调用**

```python
from web2json import Web2JsonConfig, extract_data_with_code

config = Web2JsonConfig(
    name="prod_parse",
    html_path="production_html/",
    parser_code="output/blog/parsers/final_parser.py"  # 直接传入文件路径
)

result = extract_data_with_code(config)
```

---

### Q10: 支持哪些 AI 模型？

Web2JSON-Agent 支持所有 **OpenAI API 兼容**的模型。

**推荐模型：**

- ✅ **Claude Sonnet 4.5**（默认，推荐）
- ✅ Claude Opus
- ✅ GPT-4 / GPT-4 Turbo
- ✅ GPT-3.5 Turbo

**配置方式（.env 文件）：**

```bash
# 推荐配置（Claude Sonnet 4.5）
DEFAULT_MODEL=claude-sonnet-4-5-20250929
CODE_GEN_MODEL=claude-sonnet-4-5-20250929

# 或使用 GPT-4
DEFAULT_MODEL=gpt-4-turbo
CODE_GEN_MODEL=gpt-4-turbo

# 或使用 GPT-3.5（成本更低）
DEFAULT_MODEL=gpt-3.5-turbo
CODE_GEN_MODEL=gpt-3.5-turbo
```

**注意**：需要使用支持 OpenAI API 格式的中转服务或原生 API。

---

## 📚 更多资源

- **GitHub 仓库**: [https://github.com/ccprocessor/web2json-agent](https://github.com/ccprocessor/web2json-agent)
- **PyPI 页面**: [https://pypi.org/project/web2json-agent/](https://pypi.org/project/web2json-agent/)
- **问题反馈**: [GitHub Issues](https://github.com/ccprocessor/web2json-agent/issues)
- **SWDE 测评**: 在 SWDE 数据集（124,291 个页面）上 F1 Score 达到 **89.93%**

---

## 💡 最佳实践

1. **首次使用前：布局识别**（推荐的第一步）
   - 💡 建议先使用 `classify_html_dir()` 快速分析页面布局
   - 系统会自动判断是相同布局还是混合布局
   - 相同布局 → 直接跳到第四阶段使用 `extract_data()`
   - 混合布局 → 按第三阶段的流程分别处理（充分发挥系统能力）
2. **首次使用**：建议先用简单的 HTML 文件测试（2-3 个样本）
3. **配置管理**：推荐使用 `web2json setup` 配置向导，避免手动配置错误
4. **迭代轮数**：
   - 默认 3 轮通常足够
   - 更多样本 = 更准确的 Schema，但会增加 API 调用成本
5. **混合布局处理**：充分利用系统的布局聚类能力，自动处理多种页面类型
6. **Schema 审查**：重要项目建议启用 `enable_schema_edit`，手动审查 Schema
7. **输出管理**：每次运行会在 `output/` 下创建独立目录，便于版本管理
8. **批量处理**：Web2JSON-Agent 自动处理目录中所有 HTML，无需手动循环

---

## 🆘 获取帮助

如果遇到问题：

1. ✅ 运行 `web2json check --test-api` 检查配置
2. ✅ 查看 `logs/` 目录下的详细日志
3. ✅ 阅读本文档的 FAQ 章节
4. ✅ 在 [GitHub Issues](https://github.com/ccprocessor/web2json-agent/issues) 中搜索类似问题
5. ✅ 提交新的 Issue，并附上：
   - 错误信息（完整日志）
   - 配置信息（隐藏敏感信息）
   - HTML 样本（如果可以分享）
   - 运行环境（Python 版本、操作系统）

---

<div align="center">

**Made with ❤️ by the Web2JSON-Agent team**

[⭐ Star us on GitHub](https://github.com/ccprocessor/web2json-agent) | [🐛 Report Issues](https://github.com/ccprocessor/web2json-agent/issues)

</div>
