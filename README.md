# web2json-agent

智能网页解析代码生成器 - 通过AI自动生成网页解析代码

---

## 📖 目录

- [1. 简介](#1-简介)
- [2. 基本原理](#2-基本原理)
- [3. 安装](#3-安装)
- [4. 使用](#4-使用)
  - [4.1 命令行使用](#41-命令行使用)
  - [4.2 API使用](#42-api使用)
- [5. 核心特性](#5-核心特性)
- [6. 项目结构](#6-项目结构)
- [7. 配置说明](#7-配置说明)
- [8. 架构设计](#8-架构设计)
- [9. 许可证](#9-许可证)

---

## 1. 简介

### 1.1 项目概述

**web2json-agent** 是一个基于langchain1.0框架的智能Agent系统，能够自动分析网页结构并生成高质量的Python解析代码。

### 1.2 核心能力

只需提供几个示例URL，Agent就能自动完成：

1. 📸 **自动获取网页源码和截图** - 使用DrissionPage获取完整页面内容
2. 🔍 **使用视觉模型分析页面结构** - 通过VLLM理解页面布局和数据结构
3. 💻 **生成可直接使用的BeautifulSoup解析代码** - 使用Claude生成高质量、可维护的代码
4. ✅ **自动验证生成代码的正确性** - 在真实URL上测试生成的代码
5. 🔄 **迭代优化直到满足要求** - 自动修复错误，提升成功率

### 1.3 适用场景

- ✅ 批量爬取同类型网页（博客文章、产品页面、新闻列表等）
- ✅ 快速原型开发，自动生成解析代码框架
- ✅ 网页结构分析和数据提取
- ✅ 减少手动编写解析代码的时间
---

## 2. 基本原理

### 2.1 工作流程

web2json-agent 采用**多阶段Agent架构**，通过以下步骤自动生成解析代码：

```
┌─────────────────────────────────────────────────────────────┐
│  阶段1: 任务规划 (Planning)                                  │
│  ├─ 分析URL列表                                              │
│  ├─ 确定域名和布局类型                                        │
│  └─ 生成执行计划                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段2: 任务执行 (Execution)                                 │
│  ├─ 处理每个样本URL:                                         │
│  │   ├─ 获取HTML源码 (get_webpage_source)                   │
│  │   ├─ 捕获全页截图 (capture_webpage_screenshot)           │
│  │   └─ 提取JSON Schema (extract_json_from_image)           │
│  ├─ 合并多个样本的Schema (智能识别必需/可选字段)              │
│  └─ 生成解析代码 (generate_parser_code)                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段3: 代码验证 (Validation)                                │
│  ├─ 在所有URL上测试生成的代码                                │
│  ├─ 计算成功率                                               │
│  └─ 收集错误信息                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段4: 迭代优化 (Iteration) - 可选                          │
│  ├─ 如果成功率 < 阈值 (默认80%):                             │
│  │   ├─ 分析失败原因                                         │
│  │   ├─ 使用LLM修复代码 (fix_parser_code)                   │
│  │   ├─ 重新验证                                             │
│  │   └─ 比较成功率 (提升→继续，下降→回滚)                    │
│  └─ 重复直到达到阈值或最大迭代次数                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    生成的解析器代码
```

### 2.2 核心技术

#### 2.2.1 多URL样本处理

- 支持同时处理**任意数量**的URL样本
- 每个URL独立提取HTML、截图和Schema
- 容错设计：单个样本失败不影响整体流程

#### 2.2.2 智能Schema合并

当提供多个URL时，系统会：

1. 统计每个字段在所有样本中的出现频率
2. 出现频率 ≥ 50% → 标记为**必需字段**
3. 出现频率 < 50% → 标记为**可选字段**
4. 生成包含所有字段的通用解析器

**示例**：
```
样本1: 8个字段  (title, author, date, content, ...)
样本2: 6个字段  (title, author, content, ...)
样本3: 16个字段 (title, author, date, tags, comments, ...)

合并后: 25个字段
  - 必需字段: title, author (出现在所有样本)
  - 可选字段: tags (仅出现在样本3)
```

#### 2.2.3 视觉理解驱动

使用**多模态大模型**（如qwen-vl-max）分析页面截图：

- 识别页面布局和结构
- 提取数据字段和类型
- 理解字段之间的关系
- 生成结构化的JSON Schema

#### 2.2.4 自动迭代优化

当验证失败时，系统会：

1. 收集详细的错误信息（包括traceback）
2. 调用LLM分析错误原因
3. 生成修复后的代码
4. 重新验证并比较成功率
5. 如果成功率提升→接受修改，否则→回滚

### 2.3 关键优势

- ✅ **完全自动化** - 无需手动编写解析代码
- ✅ **智能化** - LLM驱动的规划、生成和修复
- ✅ **可扩展** - 支持任意数量的URL，易于扩展
- ✅ **健壮性** - 完善的错误处理和自动回滚机制

---

## 3. 安装

### 3.1 环境要求

- **Python**: 3.12 或更高版本
- **浏览器**: Chrome/Chromium（用于网页截图）
- **操作系统**: macOS, Linux, Windows

### 3.2 克隆项目

```bash
git clone https://github.com/ccprocessor/web2json-agent.git
cd web2json-agent
```

### 3.3 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt
```

**主要依赖**：
```
langchain==1.0.1
langchain-anthropic==1.1.0
langchain-core==1.0.5
langchain-openai==1.0.3
DrissionPage==4.1.1.2
loguru==0.7.3
lxml==5.3.0
openai==2.8.1
pydantic==2.10.3
pydantic_core==2.27.1
pydantic-settings==2.6.1
python-dotenv==1.1.0
requests==2.32.3
```

### 3.4 配置API密钥

复制 `.env.example` 为 `.env` 并配置API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# API配置
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=http://your_base_url/

# 模型配置
AGENT_MODEL=claude-sonnet-4-5-20250929      # Agent使用的模型
CODE_GEN_MODEL=claude-sonnet-4-5-20250929   # 代码生成模型
VISION_MODEL=qwen-vl-max                     # 视觉理解模型

# Agent配置
MAX_ITERATIONS=5          # 最大迭代次数
SUCCESS_THRESHOLD=0.8     # 验证成功阈值（80%）
MIN_SAMPLE_SIZE=2         # 最小样本数量
```

### 3.5 验证安装

```bash
# 运行测试脚本
python test_setup.py
```

如果看到以下输出，说明安装成功：

```
✓ 通过 - 模块导入
✓ 通过 - 配置检查
✓ 通过 - 目录结构
✓ 通过 - Agent创建

总计: 4/4 通过
```

---

## 4. 使用

### 4.1 命令行使用

#### 4.1.1 基本用法

```bash
# 查看帮助
python main.py -h

# 单个URL（测试用）
python main.py https://example.com/article

# 多个URL（直接指定）
python main.py https://example.com/article1 https://example.com/article2

# 从文件读取URL列表（推荐，适合多URL场景）
python main.py -f urls.txt

# 指定输出目录和页面类型
python main.py -f urls.txt -o output/blog -t blog_article

# 跳过验证，快速生成
python main.py -f urls.txt --no-validate
```

#### 4.1.2 URL文件格式

创建一个 `urls.txt` 文件，每行一个URL：

```text
# URL列表示例
# 每行一个URL，以 # 开头的行为注释

https://stackoverflow.blog/2025/10/15/secure-coding-in-javascript/
https://stackoverflow.blog/2024/12/18/you-should-keep-a-developer-changelog/
https://stackoverflow.blog/2024/11/13/your-docs-are-your-infrastructure/
```

#### 4.1.3 使用生成的解析器

```bash
# 解析新的URL
python output/blog/parsers/generated_parser.py https://example.com/new-article

# 解析本地HTML文件
python output/blog/parsers/generated_parser.py path/to/file.html
```

---

### 4.2 API使用

#### 4.2.1 基本用法

```python
from agent import ParserAgent

# 创建Agent实例
agent = ParserAgent(output_dir="output/blog")

# 准备URL列表（建议2个以上同类型URL）
urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3",
]

# 生成解析器
result = agent.generate_parser(
    urls=urls,
    domain="example.com",         # 可选，自动从URL提取
    layout_type="blog_article",   # 可选，页面类型描述
    validate=True                  # 是否验证生成的代码
)

# 检查结果
if result['success']:
    print(f"✓ 解析器: {result['parser_path']}")
    print(f"✓ 成功率: {result['validation_result']['success_rate']:.1%}")
else:
    print(f"✗ 失败: {result.get('error', 'Unknown error')}")
```

#### 4.2.2 从文件读取URL

```python
from agent import ParserAgent

# 读取URL文件
with open('urls.txt', 'r') as f:
    urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# 生成解析器
agent = ParserAgent(output_dir="output/blog")
result = agent.generate_parser(urls=urls, validate=True)
```

#### 4.2.3 使用生成的解析器

```python
import sys
sys.path.insert(0, 'output/blog/parsers')
from generated_parser import WebPageParser

# 创建解析器实例
parser = WebPageParser()

# 解析HTML
html = """<html>...</html>"""
data = parser.parse(html)
print(data)
```

#### 4.2.4 返回值说明

`generate_parser()` 返回一个字典：

```python
{
    'success': bool,              # 是否成功
    'parser_path': str,           # 生成的解析器路径
    'config_path': str,           # 配置文件路径
    'validation_result': {        # 验证结果（如果validate=True）
        'success': bool,
        'success_rate': float,    # 成功率 (0.0-1.0)
        'tests': [...]            # 测试结果列表
    },
    'error': str                  # 错误信息（如果失败）
}
```

---

## 5. 核心特性

### 5.1 多URL样本处理

- ✅ 支持同时处理**任意数量**的URL
- ✅ 每个URL独立提取HTML、截图和Schema
- ✅ 容错设计：单个样本失败不影响整体
- ✅ 完全可扩展的架构

### 5.2 智能Schema合并

- ✅ 自动统计字段出现频率
- ✅ 识别必需字段（出现≥50%样本）
- ✅ 识别可选字段（出现<50%样本）
- ✅ 生成包含所有字段的通用解析器

### 5.3 自动迭代优化

- ✅ 验证失败时自动触发
- ✅ LLM驱动的代码修复
- ✅ 智能判断修复效果
- ✅ 自动回滚机制
- ✅ 支持最多5轮迭代

### 5.4 视觉理解

- ✅ 使用多模态大模型分析页面
- ✅ 识别页面布局和结构
- ✅ 提取数据字段和类型
- ✅ 生成结构化JSON Schema

### 5.5 高质量代码生成

- ✅ 使用Claude生成代码
- ✅ 符合PEP 8规范
- ✅ 包含完整的错误处理
- ✅ 可直接使用的BeautifulSoup代码

---

## 6. 项目结构

```
web2json-agent/
├── agent/                          # Agent核心模块
│   ├── __init__.py
│   ├── planner.py                 # 任务规划器 (AgentPlanner)
│   ├── executor.py                # 任务执行器 (AgentExecutor)
│   ├── validator.py               # 代码验证器 (AgentValidator)
│   └── orchestrator.py            # Agent编排器 (ParserAgent)
│
├── tools/                          # 工具模块 (LangChain Tools)
│   ├── __init__.py
│   ├── webpage_source.py          # 网页源码获取工具
│   ├── webpage_screenshot.py      # 网页截图工具
│   ├── visual_understanding.py    # 视觉理解工具
│   ├── code_generator.py          # 代码生成工具
│   └── code_fixer.py              # 代码修复工具
│
├── utils/                          # 工具类
│   ├── __init__.py
│   └── llm_client.py              # LLM客户端封装
│
├── config/                         # 配置模块
│   ├── __init__.py
│   └── settings.py                # 配置管理 (Pydantic)
│
├── output/                         # 输出目录
│   └── [domain]/
│       ├── screenshots/           # 截图
│       ├── parsers/               # 生成的解析器
│       └── configs/               # 配置文件
│
├── logs/                           # 日志目录
│
├── main.py                        # 主程序入口
├── example.py                     # 使用示例
│
├── requirements.txt               # 依赖列表
├── .env.example                   # 环境配置示例
│
└── README.md                      # 本文档

```

---

## 7. 配置说明

### 7.1 环境变量配置

`.env` 文件中的主要配置项：

| 配置项 | 说明 | 默认值 | 推荐值 |
|--------|------|--------|--------|
| `OPENAI_API_KEY` | API密钥 | - | 必填 |
| `OPENAI_API_BASE` | API基础URL | - | 必填 |
| `AGENT_MODEL` | Agent模型 | claude-sonnet-4-5-20250929 | claude-sonnet-4-5-20250929 |
| `CODE_GEN_MODEL` | 代码生成模型 | claude-sonnet-4-5-20250929 | claude-sonnet-4-5-20250929 |
| `VISION_MODEL` | 视觉模型 | qwen-vl-max | qwen-vl-max |
| `MAX_ITERATIONS` | 最大迭代次数 | 5 | 3-5 |
| `SUCCESS_THRESHOLD` | 成功率阈值 | 0.8 | 0.7-0.9 |
| `MIN_SAMPLE_SIZE` | 最小样本数 | 2 | 2-3 |

### 7.3 模型选择建议

**代码生成模型**：
- ✅ **Claude Sonnet 4.5** - 推荐，代码质量高

**视觉理解模型**：
- ✅ **qwen-vl-max** - 推荐

---

## 8. 架构设计

### 8.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      ParserAgent                             │
│                    (Orchestrator)                            │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Planner   │→ │  Executor  │→ │ Validator  │            │
│  │  任务规划   │  │  任务执行   │  │  代码验证   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│                         ↓                ↓                   │
│                    ┌─────────────────────┐                  │
│                    │  Iteration Loop     │                  │
│                    │  迭代优化（可选）    │                  │
│                    └─────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │         LangChain Tools               │
        ├───────────────────────────────────────┤
        │  • get_webpage_source                 │
        │  • capture_webpage_screenshot         │
        │  • extract_json_from_image            │
        │  • generate_parser_code               │
        │  • fix_parser_code                    │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │         External Services             │
        ├───────────────────────────────────────┤
        │  • Claude Sonnet 4.5 (代码生成)       │
        │  • Qwen VL Max (视觉理解)             │
        │  • DrissionPage (网页抓取)            │
        └───────────────────────────────────────┘
```


### 8.3 数据流

```
URLs → Planner → Plan
                   ↓
Plan → Executor → Samples (HTML + Screenshot + Schema)
                   ↓
Samples → Schema Merger → Merged Schema
                            ↓
Merged Schema + HTML → Code Generator → Parser Code
                                          ↓
Parser Code → Validator → Validation Result
                            ↓
                    Success Rate < Threshold?
                            ↓
                    Yes → Code Fixer → Fixed Code → Validator
                            ↓
                    No → Final Parser
```

## 9. 许可证

MIT License

---

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - Agent框架
- [DrissionPage](https://github.com/g1879/DrissionPage) - 网页抓取工具

---

## 📞 联系方式

如有问题或建议，请：
- 提交 [Issue](https://github.com/ccprocessor/web2json-agent)
- 发送邮件至: 1041206149@qq.com

---

**最后更新**: 2025-11-20
**版本**: 1.0.0
**状态**: ✅ 生产就绪

