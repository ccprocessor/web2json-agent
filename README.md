# web2json-agent

智能网页解析代码生成器 - 基于 AI 自动生成网页解析代码

## 简介

**web2json-agent** 是一个基于 LangChain 1.0 的智能 Agent 系统，通过多模态 AI 自动分析网页结构并生成高质量的 Python 解析代码。

### 核心能力

提供几个示例 URL，Agent 自动完成：

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
URL列表 → 任务规划 → 样本处理（截图+源码+Schema提取）
         ↓
    Schema合并 → 代码生成 → 验证测试
         ↓
   成功率<80%? → 迭代修复 → 最终代码
```

### 核心技术

- **多样本处理**：支持多个 URL，自动识别必需/可选字段（出现率 ≥50% 为必需）
- **视觉理解**：多模态 AI 分析页面截图提取数据结构
- **智能修复**：验证失败时自动分析错误并修复代码，支持自动回滚
- **Token 跟踪**：实时监控 API 调用成本

---

## 安装

### 环境要求

- Python 3.12+
- Chrome/Chromium（用于网页截图）

### 快速开始

```bash
# 克隆项目
git clone https://github.com/ccprocessor/web2json-agent.git
cd web2json-agent

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API 密钥
```

### 配置说明

编辑 `.env` 文件：

```bash
# API 配置
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=your_base_url

# 模型配置
AGENT_MODEL=claude-sonnet-4-5-20250929
CODE_GEN_MODEL=claude-sonnet-4-5-20250929
VISION_MODEL=qwen-vl-max

# Agent 配置
MAX_ITERATIONS=5          # 最大迭代次数
SUCCESS_THRESHOLD=0.8     # 成功率阈值（80%）
MIN_SAMPLE_SIZE=2         # 最小样本数量
```

---

## 使用

### 命令行使用

```bash
# 单个 URL
python main.py https://example.com/article

# 多个 URL
python main.py https://example.com/article1 https://example.com/article2

# 从文件读取（推荐）
python main.py -f urls.txt -o output/blog

# 跳过验证
python main.py -f urls.txt --no-validate
```

**urls.txt 格式**：
```text
https://example.com/article1
https://example.com/article2
https://example.com/article3
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
│   ├── executor.py        # 任务执行
│   ├── validator.py       # 代码验证
│   └── orchestrator.py    # Agent 编排
│
├── tools/                  # LangChain Tools
│   ├── webpage_source.py          # 获取源码
│   ├── webpage_screenshot.py      # 截图
│   ├── visual_understanding.py    # 视觉理解
│   ├── code_generator.py          # 代码生成
│   └── code_fixer.py              # 代码修复
│
├── config/                 # 配置
│   └── settings.py
│
├── utils/                  # 工具类
│   └── llm_client.py      # LLM 客户端
│
├── output/                 # 输出目录
│   └── [domain]/
│       ├── screenshots/   # 截图
│       ├── parsers/       # 生成的解析器
│       └── configs/       # 配置文件
│
├── main.py                # 命令行入口
├── example.py             # 使用示例
└── requirements.txt       # 依赖列表
```

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

**最后更新**: 2025-11-26
**版本**: 1.0.0
