"""
Web2JSON Simple API Demo
演示5个主要API的使用方式，所有数据保存在内存中，不落盘
"""
from web2json import (
    Web2JsonConfig,
    extract_data,
    extract_schema,
    infer_code,
    extract_data_with_code,
    classify_html_dir
)
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
env_path = ".env"
load_dotenv(env_path)


# ============================================
# API 1: extract_data - 完整流程
# ============================================
def demo_extract_data():
    """完整流程：生成schema + parser + 解析所有HTML文件"""
    print("\n" + "="*70)
    print("API 1: extract_data - 完整流程（Auto模式")
    print("="*70)

    # Auto模式（自动学习Schema）
    config = Web2JsonConfig(
        name="demo_auto",
        html_path="input_html/",
        iteration_rounds=3
    )

    result = extract_data(config)

    # 打印摘要
    print(f"\n{result.get_summary()}")

    # 打印Schema（前5个字段）
    print("\n=== Schema（前5个字段）===")
    schema_items = list(result.final_schema.items())[:5]
    for field, field_type in schema_items:
        print(f"  {field}: {field_type}")
    if len(result.final_schema) > 5:
        print(f"  ... 还有 {len(result.final_schema) - 5} 个字段")

    # 打印Parser代码（前30行）
    print("\n=== Parser代码（前30行）===")
    code_lines = result.parser_code.split('\n')[:30]
    for i, line in enumerate(code_lines, 1):
        print(f"{i:3d} | {line}")
    if len(result.parser_code.split('\n')) > 30:
        print(f"... 还有 {len(result.parser_code.split('\n')) - 30} 行")

    # 打印解析数据（前2个文件）
    print("\n=== 解析数据（前2个文件）===")
    for item in result.parsed_data[:2]:
        print(f"\n文件: {item['filename']}")
        print(f"数据: {json.dumps(item['data'], indent=2, ensure_ascii=False)[:500]}...")


def demo_extract_data_predefined():
    """Predefined模式（使用预定义Schema）"""
    print("\n" + "="*70)
    print("API 1: extract_data - Predefined模式")
    print("="*70)

    config = Web2JsonConfig(
        name="demo_predefined",
        html_path="input_html/",
        iteration_rounds=3,
        schema={
            "title": "string",
            "author": "string",
            "publish_date": "string",
            "content": "string"
        }
    )

    result = extract_data(config)

    print(f"\n{result.get_summary()}")
    print("\n=== 使用的Schema ===")
    print(json.dumps(result.final_schema, indent=2, ensure_ascii=False))

    print("\n=== 解析数据（第1个文件）===")
    if result.parsed_data:
        print(f"文件: {result.parsed_data[0]['filename']}")
        print(json.dumps(result.parsed_data[0]['data'], indent=2, ensure_ascii=False))


# ============================================
# API 2: extract_schema - 提取Schema
# ============================================
def demo_extract_schema():
    """仅从HTML提取Schema，不生成parser"""
    print("\n" + "="*70)
    print("API 2: extract_schema - 提取Schema")
    print("="*70)

    config = Web2JsonConfig(
        name="demo_schema_only",
        html_path="input_html/",
        iteration_rounds=3
    )

    result = extract_schema(config)

    print(f"\n{result.get_summary()}")

    # 打印最终Schema
    print("\n=== 最终Schema ===")
    print(json.dumps(result.final_schema, indent=2, ensure_ascii=False))

    # 打印中间迭代Schema
    if result.intermediate_schemas:
        print(f"\n=== 中间迭代Schema（第1轮）===")
        print(json.dumps(result.intermediate_schemas[0], indent=2, ensure_ascii=False)[:500])
        print("...")


# ============================================
# API 3: infer_code - 生成Parser代码
# ============================================
def demo_infer_code():
    """根据Schema和HTML生成Parser代码"""
    print("\n" + "="*70)
    print("API 3: infer_code - 生成Parser代码")
    print("="*70)

    # 步骤1: 先提取schema
    print("\n步骤1: 提取Schema...")
    config = Web2JsonConfig(
        name="demo_schema",
        html_path="input_html/",
        iteration_rounds=3
    )
    schema_result = extract_schema(config)
    print(f"✓ {schema_result.get_summary()}")

    # 步骤2: 使用schema生成parser代码
    print("\n步骤2: 生成Parser代码...")
    code_result = infer_code(
        schema=schema_result.final_schema,
        html_path="input_html/"
    )

    print(f"\n{code_result.get_summary()}")

    # 打印Parser代码（前40行）
    print("\n=== Parser代码（前40行）===")
    code_lines = code_result.parser_code.split('\n')[:40]
    for i, line in enumerate(code_lines, 1):
        print(f"{i:3d} | {line}")
    if len(code_result.parser_code.split('\n')) > 40:
        print(f"... 还有 {len(code_result.parser_code.split('\n')) - 40} 行")


# ============================================
# API 4: extract_data_with_code - 使用代码解析
# ============================================
def demo_extract_data_with_code():
    """使用Parser代码解析HTML文件"""
    print("\n" + "="*70)
    print("API 4: extract_data_with_code - 使用代码解析")
    print("="*70)

    # 步骤1: 先提取schema
    print("\n步骤1: 提取Schema...")
    config = Web2JsonConfig(
        name="demo_schema",
        html_path="input_html/",
        iteration_rounds=3
    )
    schema_result = extract_schema(config)
    print(f"✓ {schema_result.get_summary()}")

    # 步骤2: 生成parser代码
    print("\n步骤2: 生成Parser代码...")
    code_result = infer_code(
        schema=schema_result.final_schema,
        html_path="input_html/"
    )
    print(f"✓ {code_result.get_summary()}")

    # 步骤3: 使用parser代码解析HTML
    print("\n步骤3: 使用Parser解析HTML...")
    parse_result = extract_data_with_code(
        parser_code=code_result.parser_code,
        html_path="input_html/"
    )

    print(f"\n{parse_result.get_summary()}")

    # 打印解析结果（前2个文件）
    print("\n=== 解析结果（前2个文件）===")
    for item in parse_result.parsed_data[:2]:
        print(f"\n文件: {item['filename']}")
        print(json.dumps(item['data'], indent=2, ensure_ascii=False)[:300])
        print("...")


# ============================================
# API 5: classify_html_dir - HTML分类
# ============================================
def demo_classify_html():
    """对HTML目录进行布局分类"""
    print("\n" + "="*70)
    print("API 5: classify_html_dir - HTML布局分类")
    print("="*70)

    # 检查目录是否存在
    if not Path("mixed_html/").exists():
        print("\n⚠ 警告: mixed_html/ 目录不存在，跳过此demo")
        print("  提示: 创建 mixed_html/ 目录并放入不同布局的HTML文件以测试此功能")
        return

    result = classify_html_dir(html_path="mixed_html/")

    print(f"\n{result.get_summary()}")

    # 打印各个簇的信息
    print("\n=== 聚类详情 ===")
    for cluster_name, files in result.clusters.items():
        print(f"\n{cluster_name}: {len(files)} 个文件")
        for file_path in files[:3]:  # 打印前3个文件
            print(f"  - {Path(file_path).name}")
        if len(files) > 3:
            print(f"  ... 还有 {len(files) - 3} 个文件")

    if result.noise_files:
        print(f"\n噪声点: {len(result.noise_files)} 个文件")
        for file_path in result.noise_files[:3]:
            print(f"  - {Path(file_path).name}")


# ============================================
# 完整工作流示例
# ============================================
def demo_full_workflow():
    """演示完整的工作流程"""
    print("\n" + "="*70)
    print("完整工作流示例")
    print("="*70)

    # 步骤1: 提取Schema
    print("\n步骤1: 提取Schema...")
    config_step1 = Web2JsonConfig(
        name="workflow_step1",
        html_path="input_html/",
        iteration_rounds=2
    )
    schema_result = extract_schema(config_step1)
    print(f"✓ {schema_result.get_summary()}")

    # 步骤2: 生成Parser代码
    print("\n步骤2: 生成Parser...")
    code_result = infer_code(
        schema=schema_result.final_schema,
        html_path="input_html/"
    )
    print(f"✓ {code_result.get_summary()}")

    # 步骤3: 批量解析HTML
    print("\n步骤3: 批量解析HTML...")
    parse_result = extract_data_with_code(
        parser_code=code_result.parser_code,
        html_path="input_html/"
    )
    print(f"✓ {parse_result.get_summary()}")

    # 展示最终结果
    print("\n=== 最终结果摘要 ===")
    print(f"Schema字段数: {len(schema_result.final_schema)}")
    print(f"Parser代码行数: {len(code_result.parser_code.split(chr(10)))}")
    print(f"成功解析文件数: {parse_result.success_count}")
    print(f"失败文件数: {parse_result.failed_count}")

    # 打印第一个解析结果
    if parse_result.parsed_data:
        print(f"\n=== 示例数据（第1个文件）===")
        print(f"文件: {parse_result.parsed_data[0]['filename']}")
        print(json.dumps(parse_result.parsed_data[0]['data'], indent=2, ensure_ascii=False))


# ============================================
# 数据传输示例：将内存数据保存到其他地方
# ============================================
def demo_data_transfer():
    """演示如何将内存数据传输到数据库或其他地方"""
    print("\n" + "="*70)
    print("数据传输示例（内存数据 -> 数据库/服务器）")
    print("="*70)

    config = Web2JsonConfig(
        name="demo_transfer",
        html_path="input_html/",
        iteration_rounds=2
    )

    result = extract_data(config)

    print(f"\n{result.get_summary()}")

    # 示例1: 转换为字典（便于序列化）
    print("\n=== 示例1: 转换为字典 ===")
    result_dict = result.to_dict()
    print(f"字典键: {list(result_dict.keys())}")
    print(f"可以直接保存到JSON文件或数据库")

    # 示例2: 保存到JSON字符串
    print("\n=== 示例2: 序列化为JSON ===")
    json_str = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    print(f"JSON字符串长度: {len(json_str)} 字符")
    print(f"前200个字符: {json_str[:200]}...")

    # 示例3: 模拟发送到API（伪代码）
    print("\n=== 示例3: 发送到远程API（伪代码）===")
    print("import requests")
    print("response = requests.post(")
    print("    'https://api.example.com/upload',")
    print("    json=result.to_dict()")
    print(")")

    # 示例4: 模拟保存到数据库（伪代码）
    print("\n=== 示例4: 保存到数据库（伪代码）===")
    print("import pymongo")
    print("client = pymongo.MongoClient('mongodb://localhost:27017/')")
    print("db = client['web2json']")
    print("db.results.insert_one({")
    print("    'timestamp': datetime.now(),")
    print("    'data': result.to_dict()")
    print("})")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Web2JSON Simple API Demo ")
    print("="*70)

    # 选择要运行的demo
    print("\n请选择要运行的示例：")
    print("1. API 1: extract_data - Auto模式")
    print("2. API 1: extract_data - Predefined模式")
    print("3. API 2: extract_schema - 提取Schema")
    print("4. API 3: infer_code - 生成Parser代码")
    print("5. API 4: extract_data_with_code - 使用代码解析")
    print("6. API 5: classify_html_dir - HTML布局分类")
    print("7. 完整工作流示例")
    print("8. 数据传输示例")
    print("0. 退出")

    choice = input("\n请输入选择 (0-8): ")

    if choice == "1":
        demo_extract_data()
    elif choice == "2":
        demo_extract_data_predefined()
    elif choice == "3":
        demo_extract_schema()
    elif choice == "4":
        demo_infer_code()
    elif choice == "5":
        demo_extract_data_with_code()
    elif choice == "6":
        demo_classify_html()
    elif choice == "7":
        demo_full_workflow()
    elif choice == "8":
        demo_data_transfer()
    elif choice == "0":
        print("退出")
    else:
        print("无效选择")
