"""
HtmlParserAgent 使用示例
展示如何使用Agent生成网页解析器
"""
from loguru import logger
from agent import ParserAgent
import sys


# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def example_1_blog_parser():
    """示例1: 生成博客文章解析器 - 多URL测试"""
    print("\n" + "="*70)
    print("示例1: 生成博客文章解析器 - 多URL测试")
    print("="*70)

    # 使用多个URL测试迭代优化功能
    urls = [
        "https://stackoverflow.blog/2025/10/15/secure-coding-in-javascript/",
        "https://stackoverflow.blog/2024/12/18/you-should-keep-a-developer-changelog/",
        "https://stackoverflow.blog/2024/11/13/your-docs-are-your-infrastructure/",
    ]

    agent = ParserAgent(output_dir="output/blog")

    result = agent.generate_parser(
        urls=urls,
        domain="stackoverflow.blog",
        layout_type="blog_article",
        validate=True
    )

    if result['success']:
        print(f"\n✓ 成功! 解析器路径: {result['parser_path']}")
        print(f"\n使用方法:")
        print(f"  python {result['parser_path']} <url_or_html_file>")
    else:
        print(f"\n✗ 失败: {result.get('error')}")


def example_2_multiple_urls():
    """示例2: 使用多个URL生成更通用的解析器"""
    print("\n" + "="*70)
    print("示例2: 使用多个URL生成更通用的解析器")
    print("="*70)
    
    # 提供多个同类型的URL，Agent会分析它们的共同结构
    urls = [
        "https://example.com/article/1",
        "https://example.com/article/2",
        "https://example.com/article/3",
    ]
    
    agent = ParserAgent(output_dir="output/articles")
    
    result = agent.generate_parser(
        urls=urls,
        layout_type="article",
        validate=True
    )
    
    if result['success']:
        print(f"\n✓ 成功! 解析器路径: {result['parser_path']}")


def example_3_no_validation():
    """示例3: 快速生成，不验证"""
    print("\n" + "="*70)
    print("示例3: 快速生成模式（不验证）")
    print("="*70)
    
    urls = ["https://example.com/page"]
    
    agent = ParserAgent(output_dir="output/quick")
    
    result = agent.generate_parser(
        urls=urls,
        validate=False  # 跳过验证，快速生成
    )
    
    if result['success']:
        print(f"\n✓ 成功! 解析器路径: {result['parser_path']}")
        print("\n注意: 未经验证，建议手动测试生成的代码")


def example_4_step_by_step():
    """示例4: 分步使用各个工具"""
    print("\n" + "="*70)
    print("示例4: 分步使用工具")
    print("="*70)
    
    from tools import (
        get_webpage_source,
        capture_webpage_screenshot,
        extract_json_from_image,
        generate_parser_code
    )
    
    url = "https://example.com"
    
    # 步骤1: 获取HTML
    print("\n[1/4] 获取HTML源码...")
    html = get_webpage_source(url)
    print(f"  HTML长度: {len(html)} 字符")
    
    # 步骤2: 截图
    print("\n[2/4] 截图...")
    screenshot_path = capture_webpage_screenshot(url, save_path="temp_screenshot.png")
    print(f"  截图保存到: {screenshot_path}")
    
    # 步骤3: 提取Schema
    print("\n[3/4] 提取JSON Schema...")
    schema = extract_json_from_image(screenshot_path)
    print(f"  提取到 {len(schema)} 个字段")
    
    # 步骤4: 生成代码
    print("\n[4/4] 生成解析代码...")
    result = generate_parser_code(html, schema, output_dir="output/manual")
    print(f"  代码保存到: {result['parser_path']}")


if __name__ == "__main__":
    # 运行示例1
    example_1_blog_parser()
    
    # 取消注释以运行其他示例
    # example_2_multiple_urls()
    # example_3_no_validation()
    # example_4_step_by_step()

