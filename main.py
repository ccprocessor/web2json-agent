"""
HtmlParserAgent 主程序
通过给定URL列表，自动生成网页解析代码
"""
import sys
import argparse
import warnings
from loguru import logger
from agent import ParserAgent

# 过滤 LangSmith UUID v7 警告
warnings.filterwarnings('ignore', message='.*LangSmith now uses UUID v7.*')
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic.v1.main')


def setup_logger():
    """配置日志"""
    logger.remove()  # 移除默认处理器
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/agent_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )


def read_urls_from_file(file_path: str) -> list:
    """从文件读取URL列表

    Args:
        file_path: URL文件路径，每行一个URL

    Returns:
        URL列表
    """
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释行
                if line and not line.startswith('#'):
                    urls.append(line)
        return urls
    except FileNotFoundError:
        logger.error(f"文件不存在: {file_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    setup_logger()

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(
        description='HtmlParserAgent - 智能网页解析代码生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从文件读取URL列表（推荐）
  python main.py -f urls.txt -o output/blog

  # 单个URL（测试用）
  python main.py https://example.com/article

  # 多个URL
  python main.py https://example.com/article1 https://example.com/article2

  # 指定输出目录和页面类型
  python main.py -f urls.txt -o output/blog -t blog_article

  # 不验证，快速生成
  python main.py -f urls.txt --no-validate
        """
    )

    parser.add_argument(
        'urls',
        nargs='*',
        help='URL列表（直接在命令行指定）'
    )
    parser.add_argument(
        '-f', '--file',
        help='URL文件路径（每行一个URL，推荐用于多URL场景）'
    )
    parser.add_argument(
        '-o', '--output',
        default='output',
        help='输出目录（默认: output）'
    )
    parser.add_argument(
        '-t', '--type',
        dest='layout_type',
        help='页面类型（如: blog_article, product_page, news_list）'
    )
    parser.add_argument(
        '-d', '--domain',
        help='域名（可选，自动从URL提取）'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='跳过验证，直接生成代码'
    )

    args = parser.parse_args()

    # 获取URL列表
    urls = []
    if args.file:
        # 从文件读取
        logger.info(f"从文件读取URL: {args.file}")
        urls = read_urls_from_file(args.file)
        logger.info(f"读取到 {len(urls)} 个URL")
    elif args.urls:
        # 从命令行读取
        urls = args.urls
        logger.info(f"从命令行读取 {len(urls)} 个URL")
    else:
        # 没有提供URL，显示帮助
        parser.print_help()
        sys.exit(0)

    if not urls:
        logger.error("没有找到任何URL")
        sys.exit(1)

    logger.info("="*70)
    logger.info("HtmlParserAgent - 智能网页解析代码生成器")
    logger.info("="*70)

    # 创建Agent
    agent = ParserAgent(output_dir=args.output)

    # 生成解析器
    result = agent.generate_parser(
        urls=urls,
        domain=args.domain,
        layout_type=args.layout_type,
        validate=not args.no_validate
    )

    # 输出结果
    if result['success']:
        logger.success("\n✓ 解析器生成成功!")
        logger.info(f"  解析器路径: {result['parser_path']}")
        logger.info(f"  配置路径: {result['config_path']}")

        if not args.no_validate and 'validation_result' in result:
            success_rate = result['validation_result']['success_rate']
            logger.info(f"  验证成功率: {success_rate:.1%}")

        logger.info("\n使用方法:")
        logger.info(f"  python {result['parser_path']} <url_or_html_file>")
    else:
        logger.error("\n✗ 解析器生成失败")
        if 'error' in result:
            logger.error(f"  错误: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

