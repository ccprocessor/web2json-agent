"""
Web2JSON Simple API Demo
演示5个主要API的使用方式
"""
from web2json import (
    Web2JsonConfig,
    extract_data,
    extract_schema,
    infer_code,
    extract_data_with_code,
    classify_html_dir
)
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
        name="demo_auto",
        html_path="input_html/",
        output_path="output/",
        iteration_rounds=3
    )

    result_dir = extract_data(config)
    print(f"\n✓ 完成！结果保存在: {result_dir}")
    print(f"  - 数据: {result_dir}/result/")


def demo_extract_data_with_schema_edit():
    """Auto模式 + 人工编辑Schema"""
    print("\n" + "="*70)
    print("API 1: extract_data - Auto模式 + 人工编辑")
    print("="*70)

    config = Web2JsonConfig(
        name="demo_auto_edit",
        html_path="input_html/",
        output_path="output/",
        iteration_rounds=3,
        enable_schema_edit=True  # 启用人工编辑
    )

    result_dir = extract_data(config)
    print(f"\n✓ 完成！结果保存在: {result_dir}")


def demo_extract_data_predefined():
    """Predefined模式（使用预定义Schema）"""
    print("\n" + "="*70)
    print("API 1: extract_data - Predefined模式")
    print("="*70)

    config = Web2JsonConfig(
        name="demo_predefined",
        html_path="input_html/",
        output_path="output/",
        iteration_rounds=3,
        schema={
            "title": "string",
            "author": "string",
            "publish_date": "string",
            "content": "string"
        }
    )

    result_dir = extract_data(config)
    print(f"\n✓ 完成！结果保存在: {result_dir}")


# ============================================
# API 2: extract_schema - 提取Schema
# ============================================
def demo_extract_schema():
    """仅从HTML提取Schema，不生成parser"""
    print("\n" + "="*70)
    print("API 2: extract_schema - 提取Schema（无编辑）")
    print("="*70)

    config = Web2JsonConfig(
        name="demo_schema_only",
        html_path="input_html/",
        output_path="output/",
        iteration_rounds=3
    )

    schema_path = extract_schema(config)
    print(f"\n✓ Schema生成成功: {schema_path}")
    print(f"  你可以查看并调整这个schema，然后用于后续的parser生成")


def demo_extract_schema_with_edit():
    """提取Schema + 人工编辑"""
    print("\n" + "="*70)
    print("API 2: extract_schema - 提取Schema + 人工编辑")
    print("="*70)

    config = Web2JsonConfig(
        name="demo_schema_edit",
        html_path="input_html/",
        output_path="output/",
        iteration_rounds=3,
        enable_schema_edit=True  # 启用人工编辑
    )

    schema_path = extract_schema(config)
    print(f"\n✓ Schema生成成功: {schema_path}")


# ============================================
# API 3: infer_code - 生成Parser代码
# ============================================
def demo_infer_code():
    """根据Schema和HTML生成Parser代码"""
    print("\n" + "="*70)
    print("API 3: infer_code - 生成Parser代码")
    print("="*70)

    # 检查schema是否存在，如果不存在则先生成
    schema_path = "input_html/final_schema.json"
    if not Path(schema_path).exists():
        print(f"\nSchema文件不存在，先生成schema...")
        config = Web2JsonConfig(
            name="demo_schema_only",
            html_path="input_html/",
            output_path="output/",
            iteration_rounds=3
        )
        schema_path = extract_schema(config)
        print(f"✓ Schema生成成功: {schema_path}\n")

    # 使用schema生成parser代码
    parser_path = infer_code(
        schema_path=schema_path,
        html_path="input_html/",
        name="demo_parser"
    )

    print(f"\n✓ Parser生成成功: {parser_path}")
    print(f"  你可以检查parser代码，然后手动使用或通过API 4批量解析")


# ============================================
# API 4: extract_data_with_code - 使用代码解析
# ============================================
def demo_extract_data_with_code():
    """使用Parser代码解析HTML文件"""
    print("\n" + "="*70)
    print("API 4: extract_data_with_code - 使用代码解析")
    print("="*70)

    # 检查parser文件是否存在，如果不存在则先生成
    parser_path = "output/demo_parser/final_parser.py"
    if not Path(parser_path).exists():
        print(f"\nParser文件不存在，先生成parser...")

        # 先检查schema是否存在
        schema_path = "output/demo_schema_only/final_schema.json"
        if not Path(schema_path).exists():
            print(f"Schema文件也不存在，先生成schema...")
            config = Web2JsonConfig(
                name="demo_schema_only",
                html_path="input_html/",
                output_path="output/",
                iteration_rounds=3
            )
            schema_path = extract_schema(config)
            print(f"✓ Schema生成成功: {schema_path}")

        # 生成parser
        parser_path = infer_code(
            schema_path=schema_path,
            html_path="input_html/",
            name="demo_parser"
        )
        print(f"✓ Parser生成成功: {parser_path}\n")

    # 读取parser代码
    with open(parser_path, "r", encoding="utf-8") as f:
        parser_code = f.read()

    # 使用parser代码解析HTML
    results_dir = extract_data_with_code(
        parser_code=parser_code,
        html_path="input_html/",
        name="demo_parse_new"
    )

    print(f"\n✓ 解析完成！结果保存在: {results_dir}")


# ============================================
# API 5: classify_html_dir - HTML分类
# ============================================
def demo_classify_html():
    """对HTML目录进行布局分类"""
    print("\n" + "="*70)
    print("API 5: classify_html_dir - HTML布局分类")
    print("="*70)

    result = classify_html_dir(
        html_path="mixed_html/",
        name="demo_classify"
    )

    print(f"\n✓ 分类完成！")
    print(f"  输出目录: {result['output_dir']}")
    print(f"  识别出的布局类型数: {len(result['clusters'])}")
    print(f"  聚类信息: {result['cluster_info_file']}")


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
        output_path="output/",
        iteration_rounds=2
    )
    schema_path = extract_schema(config_step1)
    print(f"✓ Schema: {schema_path}")

    # 步骤2: 生成Parser代码
    print("\n步骤2: 生成Parser...")
    parser_path = infer_code(
        schema_path=schema_path,
        html_path="input_html/",
        name="workflow_step2"
    )
    print(f"✓ Parser: {parser_path}")

    # 步骤3: 读取Parser代码并批量解析HTML
    print("\n步骤3: 批量解析HTML...")
    with open(parser_path, "r", encoding="utf-8") as f:
        parser_code = f.read()

    results_dir = extract_data_with_code(
        parser_code=parser_code,
        html_path="input_html/",
        name="workflow_step3"
    )
    print(f"✓ 结果: {results_dir}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Web2JSON Simple API Demo")
    print("="*70)

    # 选择要运行的demo
    print("\n请选择要运行的示例：")
    print("1. API 1: extract_data - Auto模式")
    print("2. API 1: extract_data - Auto模式 + 人工编辑")
    print("3. API 1: extract_data - Predefined模式")
    print("4. API 2: extract_schema - 提取Schema")
    print("5. API 2: extract_schema - 提取Schema + 人工编辑")
    print("6. API 3: infer_code - 生成Parser代码")
    print("7. API 4: extract_data_with_code - 使用代码解析")
    print("8. API 5: classify_html_dir - HTML布局分类")
    print("9. 完整工作流示例")
    print("0. 退出")

    choice = input("\n请输入选择 (0-9): ")

    if choice == "1":
        demo_extract_data()
    elif choice == "2":
        demo_extract_data_with_schema_edit()
    elif choice == "3":
        demo_extract_data_predefined()
    elif choice == "4":
        demo_extract_schema()
    elif choice == "5":
        demo_extract_schema_with_edit()
    elif choice == "6":
        demo_infer_code()
    elif choice == "7":
        demo_extract_data_with_code()
    elif choice == "8":
        demo_classify_html()
    elif choice == "9":
        demo_full_workflow()
    elif choice == "0":
        print("退出")
    else:
        print("无效选择")
