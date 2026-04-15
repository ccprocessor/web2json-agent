# 马来西亚语 ms-web-jwn 全量清洗报告

## 1. 任务范围

本次处理对象是目录：

- [Prod/ms-web-jwn](/home/luqing/Downloads/web2json-agent/Prod/ms-web-jwn)

其中包含 **9** 份源 `jsonl`（按文件名排序）：

1. `20260310094905_352_d5c97d3855d7e8c777f63fd07dfce918.jsonl`
2. `20260311203119_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl`
3. `20260312001751_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl`
4. `20260312035605_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl`
5. `20260312073301_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl`
6. `20260312111019_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl`
7. `20260312150026_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl`
8. `20260312183025_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl`
9. `20260312220228_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl`

处理流程为：

```text
jsonl -> html + manifest -> classify_html_dir -> extract_schema -> infer_code -> extract_data_with_code
```

说明：

- 当前 repo 没有原生 URL 分桶能力；本次完全按 **HTML 结构聚类** 与 **cluster 内 parser 生成** 处理。
- Schema 采用 **Predefined** 模式，字段定义见项目根目录 [my_schema.json](/home/luqing/Downloads/web2json-agent/my_schema.json)：`title`、`content`、`author`、`date`（类型均为 `string`）。
- 调度命令形态：`scripts/run_jsonl_web2json_pipeline.py --source-jsonl <文件> --schema-json my_schema.json`（部分批次带 `--merge-summary` 等补跑参数）。

## 2. 产物目录

每份 `jsonl` 对应一个流水线根目录（`work_id` 与文件名主名一致）：

| 源 jsonl | 输出目录 |
|-----------|----------|
| `20260310094905_352_d5c97d3855d7e8c777f63fd07dfce918.jsonl` | [output/20260310094905_352_d5c97d3855d7e8c777f63fd07dfce918_pipeline](/home/luqing/Downloads/web2json-agent/output/20260310094905_352_d5c97d3855d7e8c777f63fd07dfce918_pipeline) |
| `20260311203119_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl` | [output/20260311203119_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline](/home/luqing/Downloads/web2json-agent/output/20260311203119_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline) |
| `20260312001751_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl` | [output/20260312001751_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline](/home/luqing/Downloads/web2json-agent/output/20260312001751_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline) |
| `20260312035605_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl` | [output/20260312035605_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline](/home/luqing/Downloads/web2json-agent/output/20260312035605_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline) |
| `20260312073301_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl` | [output/20260312073301_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline](/home/luqing/Downloads/web2json-agent/output/20260312073301_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline) |
| `20260312111019_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl` | [output/20260312111019_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline](/home/luqing/Downloads/web2json-agent/output/20260312111019_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline) |
| `20260312150026_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl` | [output/20260312150026_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline](/home/luqing/Downloads/web2json-agent/output/20260312150026_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline) |
| `20260312183025_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl` | [output/20260312183025_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline](/home/luqing/Downloads/web2json-agent/output/20260312183025_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline) |
| `20260312220228_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl` | [output/20260312220228_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline](/home/luqing/Downloads/web2json-agent/output/20260312220228_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee_pipeline) |

每份流水线下的核心汇总：

- `output/<work_id>_pipeline/pipeline_summary.json`：token、各簇耗时、`llm_retry_stats`（若脚本版本已写入）等。
- `input_html/<work_id>/manifest.jsonl`：与 `0001.html` 等 HTML 一一对应。

说明：本批 **未** 在流水线目录中生成 `qa_summary.json` / `qa_summary_schema_auto.json`（与 ms-web-kln 当时跑质检的路径不同）；若需字段回溯 QA，可复用 kln 报告中的 `verify_extract_alignment.py` 思路单独跑（见第 9 节）。

## 3. 规模与耗时

### 3.1 源数据规模（汇总）

- 源 `jsonl` 总大小：约 **11 GB**（`du -ch Prod/ms-web-jwn/*.jsonl`）
- `manifest.jsonl` 总行数（有效 HTML 行数口径）：**76,360** 行
- 各 `cluster_*_extract_data/result/*.json` 合计：**76,356** 个  
  - 与 manifest 差 **4**：集中在首份小批量 `20260310094905_...`（1210 行 manifest，1206 份结果），多为源行无有效 `html` 字段被流水线跳过，属预期范围。

### 3.2 各份 jsonl 行数与磁盘占用（约）

| 源 jsonl | 行数（wc -l） | 单文件约 |
|----------|---------------|----------|
| `20260310094905_352_d5c97d3855d7e8c777f63fd07dfce918.jsonl` | 1,210 | 169 MB |
| 其余 7 份（各 10k 行） | 10,000 × 7 | 约 1.3–1.4 GB/份 |
| `20260312220228_352_f4b4afed7fe66b4dd5bd1356f9d0e9ee.jsonl` | 5,150 | 686 MB |

### 3.3 聚类簇数（来自各 `pipeline_summary.json` 的 `cluster_count`）

| 源 jsonl | cluster_count |
|----------|-----------------|
| `20260310094905_...` | 7 |
| `20260311203119_...` | 7 |
| `20260312001751_...` | 5 |
| `20260312035605_...` | 6 |
| `20260312073301_...` | 6 |
| `20260312111019_...` | 6 |
| `20260312150026_...` | 6 |
| `20260312183025_...` | 5 |
| `20260312220228_...` | 5 |
| **合计** | **53**（九次流水线各自聚类簇数之和，非全局去重簇名） |

### 3.4 流水线脚本侧耗时（`pipeline_elapsed_seconds`）

九份 `pipeline_summary.json` 中，**前四份**较早跑次未写入 `pipeline_elapsed_seconds`（记为 `null`，汇总时按 **0**）；**后五份**有记录，其和为：

- `379.412 + 1050.147 + 1009.324 + 833.803 + 1615.611` = **4,888.297 s**（约 **1 h 21 min**）

与脚本 [aggregate_site_pipeline_stats.py](/home/luqing/Downloads/web2json-agent/scripts/aggregate_site_pipeline_stats.py) 字段 **`pipeline_elapsed_seconds_sum`** 一致。

说明：九份任务多为 **顺序或错峰执行**，墙钟总时间以实际排期为准；上值为 **各次 pipeline 内已记录簇耗时之和**，用于与 token 同口径对比成本；未写字段的跑次不代表实际墙钟为 0。

## 4. Token 消耗

以下为九份 `pipeline_summary.json` 中 `total_token_usage` **相加**（与脚本 `aggregate_site_pipeline_stats.py` 一致）：

| 指标 | 数值 |
|------|------|
| 请求次数 `request_count` | 146 |
| 输入 tokens | 1,816,722 |
| 输出 tokens | 481,691 |
| 合计 tokens | 2,298,413 |

各份明细（摘自各 `pipeline_summary.json`）：

| 源 jsonl | input | output | total |
|----------|-------|--------|-------|
| `20260310094905_...` | 290,156 | 60,120 | 350,276 |
| `20260311203119_...` | 329,881 | 67,892 | 397,773 |
| `20260312001751_...` | 176,182 | 44,655 | 220,837 |
| `20260312035605_...` | 208,499 | 65,357 | 273,856 |
| `20260312073301_...` | 70,853 | 21,271 | 92,124 |
| `20260312111019_...` | 208,477 | 63,485 | 271,962 |
| `20260312150026_...` | 206,996 | 59,579 | 266,575 |
| `20260312183025_...` | 160,467 | 47,037 | 207,504 |
| `20260312220228_...` | 165,211 | 52,295 | 217,506 |

LLM 可重试失败次数（`llm_retry_stats.llm_retry_events` 之和）：**0**（本批汇总为 0）。

## 5. 钱的换算（粗估）

按 **Claude Sonnet 4.5** 公开价粗估（与 ms-web-kln 报告口径一致，仅作量级参考）：

- 输入：`$3 / 1M tokens`
- 输出：`$15 / 1M tokens`

则：

- 输入成本：`1.816722 × 3 ≈ USD 5.45`
- 输出成本：`0.481691 × 15 ≈ USD 7.23`
- **合计：约 USD 12.68**

说明：实际计费若走内部兼容网关，可能与公开价不一致；此处仅供成本量级对比。

## 6. 解析结果

### 6.1 磁盘口径（推荐）

- `manifest` 总行数：**76,360**
- `cluster_*_extract_data/result/*.json` 总数：**76,356**
- 差 **4**：见 **§3.1**，视为无有效 HTML 的跳过行。

按「是否产出结果 JSON 文件」：

- 成功率：**76,356 / 76,360 ≈ 99.995%**

### 6.2 `pipeline_summary.json` 中的 `parse_success_count` 之和

部分 summary 在 **补跑合并** 场景下只包含部分簇条目，**`parse_success_count` 加总可能小于磁盘真实结果数**（例如 `20260312073301_...` 的 summary 曾仅合并部分 cluster）。**验收与对账请以 §6.1 磁盘计数为准**。

### 6.3 与 ms-web-kln 的差异

- kln 报告含 **QA 双口径**（宽松 / 严格字段回溯）；本批 **ms-web-jwn 未跑同套 qa_summary**，若要对齐 kln 的可信度分析，需另行执行字段对齐脚本并落盘报告。

## 7. 结论与后续建议

**结论（流程是否跑通）：**

- 9 份 `jsonl` 均在 `output/<work_id>_pipeline/` 下具备完整目录结构及 `pipeline_summary.json`。
- 磁盘结果 JSON 与 manifest 对齐情况见 **§6.1**，整体可视为 **全量清洗流程已跑通**。

**建议（可选）：**

1. **质检**：参考 [马来西亚语ms-web-kln全量清洗报告.md](/home/luqing/Downloads/web2json-agent/马来西亚语ms-web-kln全量清洗报告.md) 第 7–8 节，对抽样或全量跑 `verify_extract_alignment.py`，区分宽松 / 严格回溯口径。
2. **summary 合并**：若需单份 `pipeline_summary.json` 完整列出全部簇统计，可在代码已支持 `--merge-summary` 的前提下补跑一次仅写 summary 的流程，或手工合并 JSON。
3. **Schema**：若某簇 `content` 过长导致 QA 假阴性居多，可考虑拆字段或收紧 predefined schema（与 kln 报告 §10 思路一致）。

## 8. 可复用脚本

### 8.1 总调度脚本

- [run_jsonl_web2json_pipeline.py](/home/luqing/Downloads/web2json-agent/scripts/run_jsonl_web2json_pipeline.py)

作用简述：拆 `jsonl` → `manifest` → 聚类 → `extract_schema` → `infer_code` → `extract_data_with_code`，并写 `pipeline_summary.json`（含 token、耗时、`llm_retry_stats` 等，视脚本版本）。

单文件示例：

```bash
cd /home/luqing/Downloads/web2json-agent
.venv/bin/python scripts/run_jsonl_web2json_pipeline.py \
  --source-jsonl Prod/ms-web-jwn/你的文件.jsonl \
  --schema-json my_schema.json
```

目录批量（按文件名排序依次处理目录下所有 `*.jsonl`）：

```bash
.venv/bin/python scripts/run_jsonl_web2json_pipeline.py --source-dir Prod/ms-web-jwn \
  --schema-json my_schema.json
```

补跑未跑满簇、合并 summary 等参数见脚本 `--help`。

### 8.2 站点级 token / 耗时汇总

- [aggregate_site_pipeline_stats.py](/home/luqing/Downloads/web2json-agent/scripts/aggregate_site_pipeline_stats.py)

用法示例：

```bash
cd /home/luqing/Downloads/web2json-agent
.venv/bin/python scripts/aggregate_site_pipeline_stats.py Prod/ms-web-jwn
```

全部 jsonl 均有 summary 且无缺失时退出码为 **0**；需同时校验「每簇 HTML 数 = result JSON 数」时加 **`--strict`**。

### 8.3 其它

- **LLM 重试**：`web2json/utils/llm_retry.py` + 环境变量 `LLM_API_RETRY_*` / `LLM_REQUEST_TIMEOUT`（见 `web2json/config/settings.py`）。
- **字段回溯 QA**：仍可采用 kln 报告 **§11.3** 中的 `verify_extract_alignment.py` 工作流（若仓库中已存在该脚本）。

---

*文档生成说明：规模、token、耗时、簇数等来自当前工作区 `Prod/ms-web-jwn` 与 `output/*_pipeline/pipeline_summary.json` 及磁盘计数；若你迁移目录或重跑流水线，请重新执行 `aggregate_site_pipeline_stats.py` 更新数字。*
