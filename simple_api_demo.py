"""
Web2JSON Simple API Demo
演示5个主要API的使用方式，所有数据保存在内存中
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
    print("API 1: extract_data - 完整流程（Auto模式）")
    print("="*70)

    # Auto模式（自动学习Schema）
    config = Web2JsonConfig(
        name="demo_auto",  # 运行名称（必填）
        html_path="input_html/",  # HTML文件路径（必填）
        iteration_rounds=1  # 迭代轮数（可选，默认3）
        # schema=None  # Schema字典（可选，None时为auto模式）
        # enable_schema_edit=False  # 是否启用人工编辑schema（可选，默认False）
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
        name="demo_predefined",  # 运行名称（必填）
        html_path="input_html/",  # HTML文件路径（必填）
        schema={  # Schema字典（必填，用于predefined模式）
            "title": "string",
            "author": "string",
            "publish_date": "string",
            "content": "string"
        }
        # iteration_rounds=3  # 迭代轮数（可选，默认3）
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
        name="demo_schema_only",  # 运行名称（必填）
        html_path="input_html/",  # HTML文件路径（必填）
        # iteration_rounds=3  # 迭代轮数（可选，默认3）
        # enable_schema_edit=False  # 是否启用人工编辑schema（可选，默认False）
    )

    result = extract_schema(config)

    print(f"\n{result.get_summary()}")

    # 打印最终Schema
    print("\n=== 最终Schema ===")
    print(json.dumps(result.final_schema, indent=2, ensure_ascii=False))

# ============================================
# API 3: infer_code - 生成Parser代码
# ============================================
def demo_infer_code():
    """生成Parser代码（基于预定义Schema）"""
    print("\n" + "="*70)
    print("API 3: infer_code - 基于Schema生成Parser代码")
    print("="*70)

    # 使用手动定义的schema
    my_schema = {
        "title": "string",
        "author": "string",
        "publish_date": "string",
        "content": "string",
        "tags": "list"
    }

    print("\n=== 使用的Schema ===")
    print(json.dumps(my_schema, indent=2, ensure_ascii=False))

    # 使用Config方式调用API
    config = Web2JsonConfig(
        name="infer_code_demo",  # 运行名称（必填）
        html_path="html_samples/",  # HTML样本路径（必填）
        schema=my_schema  # Schema字典（必填）
        # iteration_rounds=3  # 迭代轮数（默认为3）
        # enable_schema_edit=False  # 是否启用人工编辑（可选，此API会忽略）
    )

    code_result = infer_code(config)

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
    """使用已有的Parser代码解析HTML文件（需要预先有parser代码）"""

    parser_code = ""
    # 使用parser代码解析HTML
    print("\n使用Parser解析HTML文件...")
    parse_config = Web2JsonConfig(
        name="parse_demo",  # 运行名称（必填）
        html_path="html_samples/",  # HTML文件路径（必填）
        parser_code=parser_code  # Parser代码（str格式，必填）
    )
    parse_result = extract_data_with_code(parse_config)

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

    # 使用Config方式调用API
    config = Web2JsonConfig(
        name="classify_demo",  # 运行名称（必填）
        html_path="mixed_html/"  # HTML文件路径（必填）
    )
    result = classify_html_dir(config)

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



if __name__ == "__main__":
    print("\n" + "="*70)
    print("Web2JSON Simple API Demo")
    print("="*70)

    # 选择要运行的demo
    print("\n请选择要运行的示例：")
    print("\n基础API示例:")
    print("1. API 1: extract_data - Auto模式（完整流程）")
    print("2. API 1: extract_data - Predefined模式")
    print("3. API 2: extract_schema - 提取Schema")
    print("4. API 3: infer_code - 使用预定义Schema生成Parser")
    print("5. API 4: extract_data_with_code - 使用已有Parser解析")
    print("6. API 5: classify_html_dir - HTML布局分类")
    print("\n0. 退出")

    choice = input("\n请输入选择 (0-6): ")

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
    elif choice == "0":
        print("退出")
    else:
        print("无效选择")
