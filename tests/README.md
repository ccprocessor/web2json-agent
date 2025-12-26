# 聚类功能测试文档

本目录包含 web2json-agent 的聚类功能测试套件。

## 评测集准备

测试需要使用SWDE（Structured Web Data Extraction）评测集。请按以下步骤准备：

1. **下载SWDE评测集** - 从 [SWDE数据集](https://github.com/SWDE-Dataset/SWDE) 下载完整评测集
2. **重命名目录** - 将下载的评测集目录重命名为 `evaluationSet`
3. **放置位置** - 将 `evaluationSet` 目录放在项目根目录下

```bash
# 目录结构示例
web2json-agent/
├── evaluationSet/          # SWDE评测集（需自行下载）
│   └── book/
│       ├── book-abebooks(2000)/
│       ├── book-amazon(2000)/
│       └── ...
├── tests/
│   ├── test_cluster.py
│   └── README.md
└── ...
```

## 测试概述

### 测试文件: `test_cluster.py`

包含4个测试用例，直接从全量SWDE评测集中取样测试，用于验证HTML布局聚类功能的准确性和性能。

## 测试用例说明

### 1. test_cluster_single_source_sampling
**功能**: 单一来源聚类 - 从全量评测集取样

**数据集**: 从 `evaluationSet/book/book-abebooks(2000)/` 中取样

### 2. test_cluster_mixed_source_sampling
**功能**: 混合来源聚类 - 从全量评测集取样

**数据集**: 从以下数据集各取一半样本
- `evaluationSet/book/book-abebooks(2000)/`
- `evaluationSet/book/book-amazon(2000)/`

**预期结果**:
- 应该聚类为2-4个主要簇（对应两个不同网站）
- 每个簇的纯度 > 70%

## 运行测试

### 运行所有聚类测试
```bash
python3 -m pytest tests/test_cluster.py -v
```

### 单一来源聚类测试（可配置样本数量）
```bash
# 使用默认50个样本（快速测试，约10-20秒）
python3 -m pytest tests/test_cluster.py::TestCluster::test_cluster_single_source_sampling -v -s

# 使用500个样本（中等规模，约1-2分钟）
TEST_SAMPLE_SIZE=500 python3 -m pytest tests/test_cluster.py::TestCluster::test_cluster_single_source_sampling -v -s

# 使用自定义数量
TEST_SAMPLE_SIZE=100 python3 -m pytest tests/test_cluster.py::TestCluster::test_cluster_single_source_sampling -v -s
```

### 混合来源聚类测试（可配置样本数量）
```bash
# 使用默认50个样本（每个数据集25个，快速测试）
python3 -m pytest tests/test_cluster.py::TestCluster::test_cluster_mixed_source_sampling -v -s

# 使用500个样本（每个数据集250个，中等规模）
TEST_SAMPLE_SIZE=500 python3 -m pytest tests/test_cluster.py::TestCluster::test_cluster_mixed_source_sampling -v -s
```
