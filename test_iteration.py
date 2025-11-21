"""
测试迭代优化功能
通过降低成功率阈值来触发迭代优化
"""
from loguru import logger
from agent import ParserAgent
import sys
import os

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def test_iteration_with_multiple_urls():
    """测试多URL迭代优化"""
    print("\n" + "="*70)
    print("测试: 多URL迭代优化功能")
    print("="*70)
    
    # 使用多个不同类型的URL来增加难度
    urls = [
        "https://stackoverflow.blog/2025/10/15/secure-coding-in-javascript/",
        "https://stackoverflow.blog/2024/12/18/you-should-keep-a-developer-changelog/",
        "https://stackoverflow.blog/2024/11/13/your-docs-are-your-infrastructure/",
    ]
    
    # 临时设置更高的成功率阈值来触发迭代（如果需要）
    # 或者我们可以使用不同结构的URL
    
    agent = ParserAgent(output_dir="output/iteration_test")
    
    result = agent.generate_parser(
        urls=urls,
        domain="stackoverflow.blog",
        layout_type="blog_article",
        validate=True
    )
    
    if result['success']:
        print(f"\n✓ 成功! 解析器路径: {result['parser_path']}")
        print(f"\n验证结果:")
        if result['validation_result']:
            print(f"  成功率: {result['validation_result']['success_rate']:.1%}")
            print(f"  是否通过: {result['validation_result']['passed']}")
            print(f"  测试数量: {len(result['validation_result']['tests'])}")
    else:
        print(f"\n✗ 失败: {result.get('error')}")


def test_iteration_with_mixed_urls():
    """测试混合URL（不同网站）来触发迭代优化"""
    print("\n" + "="*70)
    print("测试: 混合URL迭代优化（预期会触发迭代）")
    print("="*70)
    
    # 使用结构差异较大的URL
    urls = [
        "https://stackoverflow.blog/2025/10/15/secure-coding-in-javascript/",
        "https://news.ycombinator.com/",  # 完全不同的网站结构
    ]
    
    agent = ParserAgent(output_dir="output/mixed_test")
    
    result = agent.generate_parser(
        urls=urls,
        layout_type="article",
        validate=True
    )
    
    if result['success']:
        print(f"\n✓ 成功! 解析器路径: {result['parser_path']}")
        if result['validation_result']:
            print(f"  成功率: {result['validation_result']['success_rate']:.1%}")
    else:
        print(f"\n✗ 失败: {result.get('error')}")


def test_schema_merging():
    """测试Schema合并逻辑"""
    print("\n" + "="*70)
    print("测试: Schema合并逻辑")
    print("="*70)
    
    urls = [
        "https://stackoverflow.blog/2025/10/15/secure-coding-in-javascript/",
        "https://stackoverflow.blog/2024/12/18/you-should-keep-a-developer-changelog/",
        "https://stackoverflow.blog/2024/11/13/your-docs-are-your-infrastructure/",
    ]
    
    agent = ParserAgent(output_dir="output/schema_merge_test")
    
    # 只执行到生成代码，不验证
    result = agent.generate_parser(
        urls=urls,
        domain="stackoverflow.blog",
        layout_type="blog_article",
        validate=False  # 不验证，只看Schema合并
    )
    
    if result['success']:
        print(f"\n✓ Schema合并成功!")
        
        # 查看每个样本的Schema
        samples = result['execution_result']['samples']
        print(f"\n样本Schema统计:")
        for i, sample in enumerate(samples, 1):
            if sample.get('success'):
                schema = sample.get('schema', {})
                print(f"  样本 {i}: {len(schema)} 个字段")
                print(f"    字段: {', '.join(list(schema.keys())[:5])}...")
        
        # 查看合并后的配置
        config = result['execution_result']['final_parser'].get('config', {})
        print(f"\n合并后的Schema: {len(config)} 个字段")
        
        # 显示必需字段和可选字段
        required_fields = [k for k, v in config.items() if v.get('required', True)]
        optional_fields = [k for k, v in config.items() if not v.get('required', True)]
        
        print(f"\n必需字段 ({len(required_fields)}): {', '.join(required_fields[:5])}...")
        if optional_fields:
            print(f"可选字段 ({len(optional_fields)}): {', '.join(optional_fields[:5])}...")


if __name__ == "__main__":
    # 测试1: 多URL处理和Schema合并
    test_schema_merging()
    
    # 测试2: 正常的多URL迭代
    # test_iteration_with_multiple_urls()
    
    # 测试3: 混合URL（可能触发迭代优化）
    # test_iteration_with_mixed_urls()

