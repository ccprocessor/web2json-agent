# web2json-agent Jupyter Guide

这个文档专门基于 [scripts/run_jsonl_web2json_pipeline.py](/Users/luqing/Downloads/multiModal/web2json-agent/scripts/run_jsonl_web2json_pipeline.py) 来写，目标是在 Jupyter 里直接跑完整 `jsonl -> html -> classify -> schema -> code -> data` 流水线。

它不覆盖项目原始 [README.md](/Users/luqing/Downloads/multiModal/web2json-agent/README.md)。

## 这份文档对应哪条执行链路

这里用的不是最简单的 `extract_data(...)` 单接口方案，而是项目里的完整脚本流水线:

- 入口脚本: [scripts/run_jsonl_web2json_pipeline.py](/Users/luqing/Downloads/multiModal/web2json-agent/scripts/run_jsonl_web2json_pipeline.py)
- Jupyter 包装: [jupyter_helper.py](/Users/luqing/Downloads/multiModal/web2json-agent/jupyter_helper.py)
- Notebook helper 实现: [notebooks/jupyter_helper.py](/Users/luqing/Downloads/multiModal/web2json-agent/notebooks/jupyter_helper.py)
- 示例 notebook: [notebooks/web2json_quickstart.ipynb](/Users/luqing/Downloads/multiModal/web2json-agent/notebooks/web2json_quickstart.ipynb)

## 流水线做了什么

脚本会按下面顺序执行:

1. 读取 `jsonl`
2. 从每条记录里取出 `html` 字段
3. 拆成一批 `.html` 文件，并生成 `manifest.jsonl`
4. 对 HTML 做 `classify_html_dir`
5. 对每个 cluster 执行 `extract_schema`
6. 执行 `infer_code`
7. 用生成的 parser 执行 `extract_data_with_code`
8. 输出 `pipeline_summary.json`

适合这种输入数据:

- 原始数据是 `jsonl`
- 每行是一条网页记录
- 每条记录里有 `html` 字段
- 可能还带 `url`、`track_id`、`status`

## Jupyter 最短路径

### 1. 进入项目目录

```bash
cd /Users/luqing/Downloads/multiModal/web2json-agent
```

### 2. 安装项目

请显式使用 `python3.11`，不要用系统默认的旧版 `python3`。

```bash
python3.11 -m pip install .
```

### 3. 启动 Jupyter

```bash
python3.11 -m notebook
```

或者:

```bash
python3.11 -m jupyter lab
```

### 4. 打开示例 notebook

打开:

`notebooks/web2json_quickstart.ipynb`

## Notebook 最小示例

### Cell 1: 初始化环境

```python
from jupyter_helper import prepare_notebook

prepare_notebook(
    api_key="YOUR_API_KEY",
    api_base="https://api.openai.com/v1",
)
```

### Cell 2: 运行完整 JSONL pipeline

```python
from jupyter_helper import run_jsonl_pipeline, summarize_pipeline_result

result = run_jsonl_pipeline(
    source_jsonl="ToClassify/sample.json",
    work_id="sample_run",
    input_root="input_html",
    output_root="output",
    html_key="html",
    iteration_rounds=3,
    cluster_limit=1,
)

summarize_pipeline_result(result)
```

### Cell 3: 查看完整结果

```python
result.to_dict()
```

## 也可以直接调用原脚本

如果你不想通过 helper，也可以在 notebook 里直接 import 原脚本里的函数:

```python
from scripts.run_jsonl_web2json_pipeline import run_jsonl_pipeline

result = run_jsonl_pipeline(
    source_jsonl="ToClassify/sample.json",
    work_id="sample_run",
)
```

这就是 [scripts/run_jsonl_web2json_pipeline.py](/Users/luqing/Downloads/multiModal/web2json-agent/scripts/run_jsonl_web2json_pipeline.py) 里新增的 notebook-friendly 入口。

## 参数说明

`run_jsonl_pipeline(...)` 主要参数:

- `source_jsonl`: 源 `jsonl` 路径
- `work_id`: 这次运行的标识；为空时按文件名自动生成
- `input_root`: 拆分后 HTML 的输出根目录，默认 `input_html`
- `output_root`: pipeline 输出根目录，默认 `output`
- `html_key`: `jsonl` 中 HTML 字段名，默认 `html`
- `iteration_rounds`: schema 学习轮数上限，默认 `3`
- `cluster_limit`: 最多处理多少个 cluster，默认 `0`，表示全部

## 结果会落到哪里

如果你设置:

```python
result = run_jsonl_pipeline(
    source_jsonl="ToClassify/sample.json",
    work_id="sample_run",
)
```

通常会生成:

- `input_html/sample_run/`
- `output/sample_run_pipeline/`
- `output/sample_run_pipeline/pipeline_summary.json`

每个 cluster 下面还会有:

- schema 输出目录
- code 输出目录
- data 输出目录
- 最终 parser 文件

## API Key 配置

你可以二选一:

### 方式 A: 在 notebook 里设置

```python
from jupyter_helper import prepare_notebook

prepare_notebook(
    api_key="YOUR_API_KEY",
    api_base="https://api.openai.com/v1",
)
```

### 方式 B: 在项目根目录放 `.env`

```env
OPENAI_API_KEY=YOUR_API_KEY
OPENAI_API_BASE=https://api.openai.com/v1
DEFAULT_MODEL=gpt-4.1
```

## 已知前提

- Python 要求 `>= 3.10`
- 当前这台机器上默认 `python3` 是旧的 `3.7.3`
- 建议始终显式使用 `python3.11`
- 这条流水线依赖模型 API，可用前需要配置好 key/base

## 相关文件

- [README.md](/Users/luqing/Downloads/multiModal/web2json-agent/README.md)
- [README_JUPYTER.md](/Users/luqing/Downloads/multiModal/web2json-agent/README_JUPYTER.md)
- [scripts/run_jsonl_web2json_pipeline.py](/Users/luqing/Downloads/multiModal/web2json-agent/scripts/run_jsonl_web2json_pipeline.py)
- [jupyter_helper.py](/Users/luqing/Downloads/multiModal/web2json-agent/jupyter_helper.py)
- [notebooks/jupyter_helper.py](/Users/luqing/Downloads/multiModal/web2json-agent/notebooks/jupyter_helper.py)
- [notebooks/web2json_quickstart.ipynb](/Users/luqing/Downloads/multiModal/web2json-agent/notebooks/web2json_quickstart.ipynb)
