# SWDE 评测使用指南

## 快速开始

### 0. 一键运行（推荐）

**首次使用**：在 `.env` 文件中配置好 SWDE 评测相关参数，然后一键运行：

```bash
# 直接运行，使用 .env 中的所有配置
python3 evaluation/run_swde_evaluation.py
```

**.env 配置示例**：

```bash
# SWDE 评估配置
SWDE_DATASET_DIR=evaluationSet
SWDE_GROUNDTRUTH_DIR=evaluationSet/groundtruth
SWDE_OUTPUT_DIR=output/swde_results
SWDE_PYTHON_CMD=python3
SWDE_USE_PREDEFINED_SCHEMA=true  # 推荐开启
SWDE_RESUME=false
SWDE_SKIP_AGENT=false
SWDE_SKIP_EVALUATION=false
SWDE_FORCE=false
```

**优点**：
- ✅ 无需每次输入长命令
- ✅ 配置集中管理，易于修改
- ✅ 命令行参数可以覆盖 .env 配置

**命令行覆盖示例**：

```bash
# 使用 .env 配置，但只评测 book 垂直领域
python3 evaluation/run_swde_evaluation.py --vertical book

# 使用 .env 配置，但强制重新运行
python3 evaluation/run_swde_evaluation.py --force

# 查看当前配置（会显示 .env 中的默认值）
python3 evaluation/run_swde_evaluation.py --help
```

---

### 1. 基本评测（使用预定义Schema）

**不使用 .env 的传统方式**：

```bash
python3 evaluation/run_swde_evaluation.py \
  --dataset-dir /path/to/swde/dataset \
  --groundtruth-dir /path/to/swde/groundtruth \
  --output-dir output/swde_results \
  --use-predefined-schema
```

**说明**：
- `--use-predefined-schema`: 自动从 groundtruth 生成 schema 模板作为 agent 输入
- Schema 模板包含字段名、类型、描述（value_sample 和 xpath 为空）
- 评测使用 SWDE 标准（精确匹配、HTML实体解码、集合操作）

### 2. 评测单个垂直领域

```bash
python3 evaluation/run_swde_evaluation.py \
  --dataset-dir /path/to/swde/dataset \
  --groundtruth-dir /path/to/swde/groundtruth \
  --output-dir output/swde_results \
  --vertical book \
  --use-predefined-schema
```

可选垂直领域：`auto`, `book`, `camera`, `job`, `movie`, `nbaplayer`, `restaurant`, `university`

### 3. 评测单个网站

```bash
python3 evaluation/run_swde_evaluation.py \
  --dataset-dir /path/to/swde/dataset \
  --groundtruth-dir /path/to/swde/groundtruth \
  --output-dir output/swde_results \
  --vertical book \
  --website amazon \
  --use-predefined-schema
```

### 4. 断点续评（Resume模式）

```bash
python3 evaluation/run_swde_evaluation.py \
  --dataset-dir /path/to/swde/dataset \
  --groundtruth-dir /path/to/swde/groundtruth \
  --output-dir output/swde_results \
  --use-predefined-schema \
  --resume
```

**说明**：
- `--resume`: 跳过已完成的网站，从中断处继续
- 适用于大规模评测时的中断恢复

### 5. 跳过特定阶段

```bash
# 跳过 agent 执行（如果已有结果）
python3 evaluation/run_swde_evaluation.py \
  --dataset-dir /path/to/swde/dataset \
  --groundtruth-dir /path/to/swde/groundtruth \
  --output-dir output/swde_results \
  --use-predefined-schema \
  --skip-agent

# 跳过评测（如果已有报告）
python3 evaluation/run_swde_evaluation.py \
  --dataset-dir /path/to/swde/dataset \
  --groundtruth-dir /path/to/swde/groundtruth \
  --output-dir output/swde_results \
  --use-predefined-schema \
  --skip-evaluation

# 强制重新运行（覆盖所有结果）
python3 evaluation/run_swde_evaluation.py \
  --dataset-dir /path/to/swde/dataset \
  --groundtruth-dir /path/to/swde/groundtruth \
  --output-dir output/swde_results \
  --use-predefined-schema \
  --force
```

## 输出结果

### 目录结构

```
output/swde_results/
├── _schemas/                           # 生成的schema模板
│   ├── book/
│   │   ├── amazon_schema.json
│   │   └── ...
│   └── ...
├── book/
│   ├── amazon/
│   │   ├── html_original/              # 原始HTML
│   │   ├── html_simplified/            # 简化后HTML
│   │   ├── schemas/                    # Schema迭代过程
│   │   ├── parsers/                    # 生成的解析器
│   │   │   └── final_parser.py
│   │   ├── result/                     # 解析结果
│   │   │   ├── 0000.json
│   │   │   ├── 0001.json
│   │   │   └── ...
│   │   └── evaluation/                 # 评测报告
│   │       ├── evaluation_report.json
│   │       └── evaluation_report.txt
│   └── _summary/
│       └── summary.json                # 垂直领域汇总
└── summary.json                        # 全局汇总
```

### 评测报告

**evaluation_report.json** 包含：

```json
{
  "vertical": "book",
  "website": "amazon",
  "overall_metrics": {
    "precision": 0.85,
    "recall": 0.80,
    "f1": 0.82
  },
  "attribute_metrics": {
    "title": {
      "precision": 0.90,
      "recall": 0.88,
      "f1": 0.89,
      "total_true_positives": 45,
      "total_false_positives": 5,
      "total_false_negatives": 6
    },
    ...
  },
  "statistics": {
    "total_pages": 50,
    "evaluated_pages": 48,
    "errors": 2
  }
}
```

**summary.json** 包含全局进度和指标：

```json
{
  "timestamp": "2025-12-25T...",
  "overall": {
    "total_websites": 80,
    "completed_websites": 25,
    "precision": 0.82,
    "recall": 0.78,
    "f1": 0.80
  },
  "verticals": {
    "book": {
      "completed_websites": 10,
      "total_websites": 10,
      "metrics": {
        "precision": 0.85,
        "recall": 0.80,
        "f1": 0.82
      }
    }
  }
}
```

## SWDE 标准说明

### 归一化方式

1. HTML 实体解码（25+ 种）：`&lt;` → `<`, `&amp;` → `&`, `&nbsp;` → ` `, ...
2. 移除所有空白字符：`\s+` → ``
3. 转换为小写

### 匹配策略

- **精确匹配**：归一化后字符串完全相等
- 不使用子串匹配

### 指标计算

使用集合操作：

```
pred_set = {归一化后的预测值}
gt_set = {归一化后的真值}

TP = |pred_set ∩ gt_set|    # 交集
FP = |pred_set - gt_set|    # 预测但不在真值
FN = |gt_set - pred_set|    # 真值但未预测

Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
F1 = 2 × P × R / (P + R)
```

## 常见问题

### Q1: 为什么 precision/recall 比之前低？

A: 新版本使用 SWDE 标准的精确匹配，比之前的子串匹配更严格。这是正常现象，更符合学术评测标准。

### Q2: Schema 的 value_sample 和 xpath 为空是否正常？

A: 是的，这是简化后的设计。Agent 会自动从 HTML 中提取信息，不需要预先提供样本值和 XPath。

### Q3: 如何查看详细的错误信息？

A: 查看 `output/swde_results/{vertical}/{website}/evaluation/evaluation_report.json`，其中包含每个页面的详细评测结果和错误信息。

### Q4: 评测很慢怎么办？

A: 可以先评测单个网站测试，确认无误后再运行完整评测。使用 `--resume` 和 `--skip-agent` 参数可以加速重复运行。

## 进阶用法

### 只生成 Schema 模板

```python
from evaluation.schema_generator import SchemaGenerator
from pathlib import Path

generator = SchemaGenerator('/path/to/groundtruth')

# 生成单个网站的schema
schema = generator.generate_schema_for_website('book', 'amazon')

# 保存
output_path = Path('output/schemas/book_amazon_schema.json')
generator.save_schema_template(schema, output_path)
```

### 只运行评测（不运行Agent）

```python
from evaluation.evaluator import SWDEEvaluator
from pathlib import Path

evaluator = SWDEEvaluator('/path/to/groundtruth')

# 评测已有的agent输出
results = evaluator.evaluate_website(
    vertical='book',
    website='amazon',
    output_dir=Path('output/book/amazon/result')
)

print(f"Precision: {results['overall_metrics']['precision']:.2%}")
print(f"Recall: {results['overall_metrics']['recall']:.2%}")
print(f"F1: {results['overall_metrics']['f1']:.2%}")
```

## 参考资料

- **SWDE 数据集**: 官方网站 https://github.com/SWDE-2010
- **主项目文档**: 项目根目录的 `README.md`
