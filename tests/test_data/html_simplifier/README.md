# HTML精简测试数据集

本目录包含用于测试HTML精简功能的真实HTML样本，特别是测试ASP.NET网站form标签解包功能。

## 数据来源

这些HTML文件来自SWDE (Structured Web Data Extraction) 数据集，是在修复前会导致内容完全丢失或严重丢失的问题文件。

## 测试文件分类

### 完全内容丢失文件（13B，共12个）

修复前这些文件精简后仅剩 `<html></html>` (13字节)：

1. **aspnet_carquotes.html** (31KB)
   - 域名：auto/carquotes
   - 特点：form紧邻body（Δ1行），全部内容包裹在form内

2. **aspnet_job.html / job_techcentric** (57KB)
   - 域名：job/techcentric
   - 特点：ASP.NET WebForms架构

3. **aspnet_restaurant.html / restaurant_zagat** (73KB)
   - 域名：restaurant/zagat
   - 特点：典型ASP.NET包裹模式

4. **auto_automotive_schema_round_1.html** (126KB)
   - 域名：auto/automotive

5. **auto_motortrend_schema_round_1.html** (107KB)
   - 域名：auto/motortrend

6. **job_careerbuilder_schema_round_1.html** (58KB)
   - 域名：job/careerbuilder

7. **movie_hollywood_schema_round_1.html** (75KB)
   - 域名：movie/hollywood

8. **nbaplayer_slam_schema_round_1.html** (54KB)
   - 域名：nbaplayer/slam

9. **university_collegeprowler_schema_round_1.html** (55KB)
   - 域名：university/collegeprowler

10. **university_collegetoolkit_schema_round_1.html** (76KB)
    - 域名：university/collegetoolkit

11. **university_embark_schema_round_1.html** (39KB)
    - 域名：university/embark

12. **university_princetonreview_schema_round_1.html** (88KB, 精简后58B)
    - 域名：university/princetonreview

### 严重内容丢失文件（>90%丢失，共2个）

13. **camera_ecost_schema_round_1.html** (132KB → 1.4KB, 98.9%丢失)
    - 域名：camera/ecost
    - 特点：form内容占比极高

14. **university_collegenavigator_schema_round_1.html** (83KB → 8KB, 90.6%丢失)
    - 域名：university/collegenavigator
    - 特点：大量form嵌套

## 修复前后对比

### 完全丢失文件（12个）

**修复前**:
- 精简后：13 bytes (`<html></html>`)
- 内容丢失率：100%
- 状态：无法生成解析器

**修复后**:
- 平均精简后：28,446 bytes
- 平均压缩率：58.3%
- 内容保留率：100%
- 状态：解析器生成正常

### 严重丢失文件（2个）

**修复前**:
- camera_ecost: 132KB → 1.4KB (98.9%丢失)
- collegenavigator: 83KB → 8KB (90.6%丢失)

**修复后**:
- camera_ecost: 132KB → 75KB (43.2%压缩)
- collegenavigator: 83KB → 24KB (71.2%压缩)

## 测试覆盖

- **总测试文件数**: 14个
- **总测试用例数**: 20个（包含基础功能测试6个）
- **域名覆盖**:
  - Auto: 3个
  - Jobs: 2个
  - Movies: 1个
  - NBA Players: 1个
  - Restaurants: 1个
  - Universities: 5个
  - Camera: 1个

## 使用方式

### 运行所有测试

```bash
pytest tests/test_html_simplifier.py -v
```

### 只测试真实数据

```bash
pytest tests/test_html_simplifier.py::TestRealWorldData -v
```

### 测试特定文件

```bash
pytest tests/test_html_simplifier.py -k "carquotes" -v
```

## 测试断言

每个真实数据测试包含以下断言：

1. **内容保留**: 精简后大小 > 100字节（防止完全丢失）
2. **最小保留率**: 保留率 > 10%（防止过度丢失）
3. **有效压缩**: 保留率 < 80%（确保精简有效）
4. **最小尺寸**: 精简后 >= 指定阈值（基于文件特性）
5. **结构完整**: 包含div/table/ul等内容标签

## 重要性

这些测试文件代表了HTML精简工具最容易出问题的场景：

- ASP.NET WebForms全包裹架构
- 大量form嵌套
- ViewState等冗余数据
- 复杂的表单结构

通过这些测试，确保form解包功能稳定可靠，防止未来回归。
