# web2json-agent

智能网页解析代码生成器 - 基于 AI 自动生成网页解析代码

## 简介

**web2json-agent** 是一个基于 LangChain 的智能 Agent 系统，通过多模态 AI 自动分析网页结构并生成高质量的 Python 解析代码。

### 核心能力

提供几个示例 HTML，Agent 自动完成：

1. 📸 获取网页源码和截图（DrissionPage）
2. 🔍 视觉模型分析页面结构（Qwen VL Max）
3. 💻 生成 BeautifulSoup 解析代码（Claude Sonnet 4.5）
4. ✅ 自动验证并迭代优化代码
5. 🎯 Token 使用跟踪和成本控制

### 适用场景

- 批量爬取同类型网页（博客、产品页、新闻等）
- 快速生成解析代码原型
- 减少手动编写解析器的时间

## 工作流程

```
URL列表 → 任务规划 → Schema迭代阶段（对每个HTML）
                    ├─ 获取HTML源码 + 截图
                    ├─ HTML → Schema（含xpath路径）
                    ├─ 视觉 → Schema（含视觉描述）
                    └─ 合并两个Schema
         ↓
    多Schema合并（筛选+修正+去重）→ 最终Schema
         ↓
    代码迭代阶段 → 生成/优化解析代码 → 最终代码
```

### Schema迭代规则

**对于单个HTML（假设输入5个）：**
1. **HTML分析**：从HTML代码提取Schema（字段名、说明、值示例、**xpath路径**）
2. **视觉分析**：从网页截图提取Schema（字段名、说明、值示例、**视觉描述**）
3. **Schema合并**：判断相同字段，合并xpath和visual_features

**处理完所有HTML后：**
4. **多Schema整合**：
   - 去除无意义字段（广告、导航等）
   - 修正字段结构（元信息归属、列表字段识别）
   - 合并xpath路径（每个字段包含多个xpath，增强鲁棒性）
   - 生成最终Schema

### 核心技术

- **双重视角Schema提取**：同时从HTML代码和视觉布局提取Schema，互相补充
- **多路径鲁棒性**：每个字段保留多个xpath提取路径，适应不同页面结构
- **智能Schema合并**：自动识别相同字段、修正字段类型、优化数据结构
- **HTML精简**：使用html_alg_lib库精简HTML，减少token消耗，提升响应速度
- **Token 跟踪**：实时监控 API 调用成本

---

## 安装

```bash
# 克隆项目
git clone https://github.com/ccprocessor/web2json-agent.git
cd web2json-agent

# 安装依赖
pip install -r requirements.txt

# 或使用可编辑模式（开发）
pip install -e .
```

---

## ⚙️ 配置（重要！）

### 首次使用配置

**安装后必须先配置 API 密钥才能使用！**

#### 方法一：交互式配置（推荐新手）

```bash
# 运行配置向导
web2json setup

# 按照提示输入:
# 1. API 密钥（必需）
# 2. API 地址（必需）
# 3. 模型配置（可选）

# 验证配置
web2json check
```

#### 方法二：快速配置

```bash
# 1. 创建配置文件
web2json init

# 2. 编辑 .env 文件，填入你的 API 密钥
vim .env  # 或使用其他编辑器

# 3. 验证配置
web2json check
```

### 最小配置示例

在项目目录创建 `.env` 文件，填入以下内容：

```bash
# API 配置（必需）
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# 模型配置（可选，默认值如下）
AGENT_MODEL=claude-sonnet-4-5-20250929
CODE_GEN_MODEL=claude-sonnet-4-5-20250929
VISION_MODEL=qwen-vl-max
```

---

## 使用

### 命令行使用

```bash
# 查看帮助
web2json --help

# 从目录读取HTML文件（推荐）
web2json -d input_html/ -o output/blog

# 指定输出目录和页面类型
web2json -d input_html/ -o output/blog -t blog_article

# 跳过验证，快速生成
web2json -d input_html/ --no-validate
```

### Python 源码使用（开发模式）

如果从源码安装，也可以使用原始的 Python 方式：

```bash
# 从目录读取（推荐）
python main.py -d input_html/ -o output/blog

# 指定页面类型
python main.py -d input_html/ -o output/blog -t blog_article
```

### HTML 文件准备

在 `input_html/` 目录下放置多个同类型网页的 HTML 源码文件：

```
input_html/
  ├── page1.html
  ├── page2.html
  └── page3.html
```

### 使用生成的解析器

```python
import sys
sys.path.insert(0, 'output/blog/parsers')
from generated_parser import WebPageParser

parser = WebPageParser()
data = parser.parse(html_content)
print(data)
```

---

## 项目结构

```
web2json-agent/
├── agent/                  # Agent 核心模块
│   ├── planner.py         # 任务规划
│   ├── executor.py        # 任务执行（含Schema迭代逻辑）
│   └── orchestrator.py    # Agent 编排
│
├── tools/                  # LangChain Tools
│   ├── webpage_source.py          # 获取源码
│   ├── webpage_screenshot.py      # 截图（Playwright）
│   ├── visual_understanding.py    # 视觉理解（旧版）
│   ├── schema_extraction.py       # Schema提取和合并（新版）
│   ├── html_simplifier.py         # HTML精简工具
│   ├── code_generator.py          # 代码生成
│   └── code_fixer.py              # 代码修复
│
├── prompts/                # Prompt 模板
│   ├── visual_understanding.py    # 视觉理解Prompt（旧版）
│   ├── schema_extraction.py       # Schema提取Prompt（新版）
│   ├── code_generator.py          # 代码生成Prompt
│   └── code_fixer.py              # 代码修复Prompt
│
├── html_alg_lib/           # HTML精简算法库
│   ├── simplify.py        # HTML精简入口
│   └── html_simplify/     # 精简算法实现
│
├── config/                 # 配置
│   └── settings.py
│
├── utils/                  # 工具类
│   └── llm_client.py      # LLM 客户端
│
├── output/                 # 输出目录
│   └── [domain]/
│       ├── screenshots/       # 网页截图
│       ├── html_original/     # 原始HTML
│       ├── html_simplified/   # 精简HTML
│       ├── schemas/           # Schema文件
│       │   ├── html_schema_round_{N}.json     # HTML提取的Schema
│       │   ├── visual_schema_round_{N}.json   # 视觉提取的Schema
│       │   ├── merged_schema_round_{N}.json   # 合并后的Schema
│       │   └── final_schema.json              # 最终Schema
│       ├── parsers/           # 生成的解析器
│       │   ├── parser_round_{N}.py            # 每轮生成的解析器
│       │   └── final_parser.py                # 最终解析器
│       └── result/            # 解析结果JSON
│
├── main.py                # 命令行入口
└── requirements.txt       # 依赖列表
```

---

## Schema格式说明

### 最终Schema结构

生成的`final_schema.json`包含每个字段的完整信息：

```json
{
  "title": {
    "type": "string",
    "description": "文章标题",
    "value_sample": "关于人工智能的未来",
    "xpaths": [
      "//h1[@class='article-title']/text()",
      "//div[@class='title']/text()"
    ],
    "visual_features": "位于页面上部中央区域，字体非常大且加粗，颜色为深色..."
  },
  "comments": {
    "type": "array",
    "description": "评论列表",
    "value_sample": [{"user": "用户A", "text": "评论内容"}],
    "xpaths": [
      "//div[@class='comment-list']//div[@class='comment']",
      "//ul[@class='comments']//li"
    ],
    "visual_features": "位于正文下方，多个评论项垂直排列..."
  }
}
```

### 字段说明

- **type**: 数据类型（string, number, array, object等）
- **description**: 字段的语义描述
- **value_sample**: 实际值示例（字符串截取前50字符）
- **xpaths**: 数组形式，包含多个可用的xpath提取路径（增强鲁棒性）
- **visual_features**: 视觉特征描述，包括位置、字体、颜色、布局等

---

## 返回值说明

`generate_parser()` 返回：

```python
{
    'success': bool,              # 是否成功
    'parser_path': str,           # 解析器路径
    'config_path': str,           # 配置文件路径
    'validation_result': {        # 验证结果
        'success': bool,
        'success_rate': float,    # 成功率 (0.0-1.0)
        'tests': [...]            # 测试详情
    },
    'error': str                  # 错误信息（如果失败）
}
```

---

## 许可证

MIT License

---

**最后更新**: 2025-12-16
**版本**: 2.1.0

## 更新日志

### v2.0.0 (2025-12-12)
- ✨ 新增双重视角Schema提取（HTML + 视觉）
- ✨ 支持多xpath路径，增强解析鲁棒性
- ✨ 智能Schema合并和结构优化
- ✨ 集成HTML精简工具，减少token消耗
- 🔧 使用Playwright替代DrissionPage进行截图
- 📝 完善文档和使用说明

### v1.0.0 (2025-11-26)
- 🎉 首次发布
- 基于视觉理解的Schema提取
- 自动代码生成和迭代优化

