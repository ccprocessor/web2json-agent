# ms-web-mma：Jupyter 实操版 Checklist（Spark 清洗作业）

本文把 [ms-web-mma_聚类与schema回填流程说明.md](/home/luqing/Downloads/v2/web2json-agent/ms-web-mma_聚类与schema回填流程说明.md) 中的目标流程，展开成一份可在 `http://jupyter.bigdata.shlab.tech/` 上执行的实操 checklist。

适用目标：

- 利用 **web2json** 对 `ms-web-mma` 做统一聚类
- 按簇抽取 schema / parser / data
- 再回填成发布向 JSONL

---

## 0. 执行原则

建议先跑 **主文件**：

- `20260310094859_353_79bda33fa180eedac40d37876224609d.jsonl`

跑通主文件后，再放大到整个目录。原因很简单：

- 主文件有 191 行，是主要数据量
- 其余 5 个文件都只有 1 行，容易因为聚类噪声而影响你对流程状态的判断

---

## 1. 准备环境

### 输入

- Jupyter 环境：`http://jupyter.bigdata.shlab.tech/`
- 本地代码目录：
  [web2json-agent](/home/luqing/Downloads/v2/web2json-agent)
- 流程说明：
  [ms-web-mma_聚类与schema回填流程说明.md](/home/luqing/Downloads/v2/web2json-agent/ms-web-mma_聚类与schema回填流程说明.md)
- 数据目录：
  [Prod/ms-web-mma](/home/luqing/Downloads/v2/web2json-agent/Prod/ms-web-mma)
- 路径约定：
  `Prod/ms-web-mma/s3Path.txt`

### 要做什么

1. 打开 notebook，确认 Python 环境可用。
2. 确认能访问 `web2json-agent` 项目目录。
3. 确认能读取 `Prod/ms-web-mma/*.jsonl`。
4. 读取 `s3Path.txt`，确认输入与输出前缀。
5. 明确本次跑的是：
   - 仅主文件
   - 还是整个目录

### 产出

- 一份确认过的任务参数清单，例如：

```text
project_root=/home/luqing/Downloads/v2/web2json-agent
source_dir=/home/luqing/Downloads/v2/web2json-agent/Prod/ms-web-mma
source_files=[20260310094859_353_79bda33fa180eedac40d37876224609d.jsonl]
output_root=s3://xyz2-process-hdd1/nlp/ms-web-mma/v0001
```

### 要验什么

- 代码目录能读
- 源文件能读
- S3 路径约定明确
- 本次范围已经锁定，不临时变化

---

## 2. 启动 Spark Session

### 输入

- notebook 环境
- 项目根目录
- 任务名，例如：
  `ms-web-mma-cluster-v0001`

### 要做什么

1. 在 notebook 中初始化 Spark Session。
2. 配置应用名、必要的 executor / memory / shuffle 参数。
3. 将 `web2json-agent` 项目目录加入 Python path。
4. 用一个极小样本做试读。

### 产出

- 一个可用的 SparkSession
- 一次试读结果，确认 JSON 行结构正常

### 要验什么

- Spark 能成功启动
- 能成功 `read jsonl`
- 抽样记录中至少存在：
  - `html`
  - `track_id` 或可替代唯一键
  - `url`

---

## 3. 生成全量索引表

### 输入

- 目标源文件列表
- SparkSession

### 要做什么

对所有目标 JSONL 行生成统一索引。建议每一行至少补齐这些字段：

| 字段 | 说明 |
|---|---|
| `global_index` | 全局唯一顺序号 |
| `source_jsonl` | 源文件路径 |
| `source_name` | 源文件名 |
| `line_no` | 文件内行号 |
| `record_id` | 优先用 `track_id`，缺失时兜底 |
| `html` | 原始 HTML |
| `url` | 原始 URL |

建议将这一步的结果单独落盘，作为后面所有 join 的主键底表。

### 产出

- 一份“全量索引表”
- 可选落盘：
  - `output/ms-web-mma/v001/index/all_rows_with_index.jsonl`

### 要验什么

- 行数是否等于输入总行数
- `global_index` 是否唯一
- `(source_jsonl, line_no)` 是否唯一
- 每行是否有可用 `record_id`

---

## 4. 跑统一布局聚类

### 输入

- 全量索引表
- 每行的 `html`

### 要做什么

1. 对每行 `html` 调 web2json 的布局特征逻辑。
2. 对全体样本只做一次全局布局聚类。
3. 为每条记录生成：
   - `layout_cluster_id`
4. 单独标出：
   - `noise` 或 `-1`

### 产出

- `cluster_list/cluster_list.jsonl`
- 可选：
  - `cluster_list/cluster_info.txt`

建议 `cluster_list.jsonl` 包含：

| 字段 | 说明 |
|---|---|
| `global_index` | 全局索引 |
| `layout_cluster_id` | 聚类标签 |
| `source_jsonl` | 源路径 |
| `source_name` | 源文件名 |
| `line_no` | 原始行号 |
| `record_id` | 唯一标识 |

### 要验什么

- `cluster_list` 总行数是否等于输入总行数
- 是否存在异常大量 `noise`
- `layout_cluster_id` 是否有稳定分布
- `cluster_info.txt` 能否帮助人工快速判断簇是否合理

---

## 5. 按簇切片写 JSONL

### 输入

- 全量索引表
- `cluster_list.jsonl`

### 要做什么

1. 根据 `layout_cluster_id` 把原始行切到不同簇目录。
2. 每个簇形成一个或多个切片 JSONL。
3. `noise` 单独处理。

建议目录：

```text
output/ms-web-mma/v001/cluster_list/format_clusters/
  cluster_0/
  cluster_1/
  ...
  noise/
```

切片行里建议保留：

- 原始 crawl 字段
- `global_index`
- `layout_cluster_id`
- `source_name`
- `line_no`
- `record_id`

### 产出

- `cluster_k/*.jsonl.gz`
- `noise/*.jsonl.gz`

### 要验什么

- 所有簇切片行数总和是否等于输入总行数
- 同一 `global_index` 是否只出现在一个簇里
- `noise` 是否单独隔离成功

---

## 6. 对每个簇独立跑抽取

### 输入

- `cluster_k/*.jsonl.gz`

### 要做什么

对每个有效簇依次执行：

1. `extract_schema`
2. `infer_code`
3. `extract_data_with_code`

每个簇都要形成独立产物目录。

建议每簇至少保留：

| 文件 | 作用 |
|---|---|
| `schema.json` | 最终 schema |
| `final_parser.py` | 最终 parser |
| `result/*.json` | 每页抽取结果 |
| `cluster_k_extract_manifest.jsonl` | 回填主索引 |

### 产出

- 每个簇的抽取产物目录
- `cluster_k_extract_manifest.jsonl`

### 要验什么

- 每个簇都至少有 schema 和 parser
- `result/*.json` 数量和 manifest 对齐
- manifest 中能唯一回指 `global_index` 或 `(source_name, line_no)`
- 对于失败页，是否有 `parse_ok=false` 或等价状态

---

## 7. 回填原始 JSONL

### 输入

- 原始索引表
- `cluster_list.jsonl`
- 每簇 manifest
- 每簇 `result/*.json`

### 要做什么

基于 join 逻辑把抽取结果写回原始行：

1. 以 `global_index` 或 `(source_jsonl, line_no)` 做主键对齐。
2. 在原始对象基础上增量合并抽取字段：
   - `content`
   - `title`
   - `author`
   - `publish_time`
   - 其他 schema 定义字段
3. 把 schema / xpath 元信息写到：
   - `remark.extract_schema`
4. 生成：
   - `track_loc`
   - `doc_loc`

注意：

- 不要新增 `_w2j` 顶层字段
- 原始 crawl 字段尽量保留

### 产出

- 回填后的“发布向 JSONL”

### 要验什么

- 回填后总行数是否与输入一致
- 未抽取成功的行是否仍然可追踪
- `remark.extract_schema` 是否落对
- `track_loc` / `doc_loc` 是否符合文档约定

---

## 8. 写发布结果

### 输入

- 回填后的结果 DataFrame / JSONL
- 输出前缀：`xyz2-process-hdd1/.../nlp/ms-web-mma/v0001`

### 要做什么

1. 按最终发布规范写出 `.jsonl.gz`
2. 目录中保留：
   - 发布文件
   - pipeline 产物
   - 可追溯索引

### 产出

- 发布路径下的最终 `.jsonl.gz`

### 要验什么

- 能按 `doc_loc` 找到对应发布文件
- gzip 可解压
- 单行 JSON 格式合法
- 样本抽查字段完整

---

## 9. 最小验收清单

在整个 notebook 流程结束后，至少要核对下面这些：

| 项 | 验收问题 |
|---|---|
| 输入行数 | 是否与原始输入一致 |
| `cluster_list` 行数 | 是否与输入一致 |
| 切片总行数 | 是否与输入一致 |
| manifest 对齐 | 是否能唯一回填到原始行 |
| 回填后行数 | 是否与输入一致 |
| `remark.extract_schema` | 是否存在且结构合理 |
| `track_loc` | 是否能回指原始 source |
| `doc_loc` | 是否能回指发布文件 |
| `noise` | 是否单独标记处理 |

---

## 10. 推荐 notebook 拆分

建议不要把所有逻辑塞进一个 notebook，最好拆成 4 本：

### 10.1 `01_build_index_and_classify.ipynb`

负责：

- 读源数据
- 建立索引
- 跑统一聚类
- 写 `cluster_list.jsonl`

### 10.2 `02_split_by_cluster.ipynb`

负责：

- 按簇切片
- 写 `cluster_k/*.jsonl.gz`

### 10.3 `03_extract_per_cluster.ipynb`

负责：

- 对每个 `cluster_k` 跑
  - `extract_schema`
  - `infer_code`
  - `extract_data_with_code`
- 写 manifest

### 10.4 `04_merge_backfill_and_publish.ipynb`

负责：

- join 回填
- 写最终发布 JSONL
- 做最终验收

---

## 11. 建议执行顺序

最稳妥的顺序是：

1. 先只跑主文件 `20260310094859_...jsonl`
2. 跑通 `索引 -> 聚类 -> 切片 -> 单簇抽取 -> 回填`
3. 固化产物格式
4. 再扩大到整目录

---

## 12. 一句话版本

```text
先统一聚类，再按簇抽取，最后按索引回填原始行并发布。
```
