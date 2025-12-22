"""
HtmlParserAgent 主程序
通过给定HTML文件目录，自动生成网页解析代码
"""
import sys
import argparse
import warnings
from pathlib import Path
from loguru import logger
from agent import ParserAgent
from tools.cluster import cluster_html_layouts

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


def read_html_files_from_directory(directory_path: str) -> list:
    """从目录读取HTML文件列表

    Args:
        directory_path: HTML文件目录路径

    Returns:
        HTML文件路径列表（绝对路径）
    """
    html_files = []
    try:
        dir_path = Path(directory_path)
        if not dir_path.exists():
            logger.error(f"目录不存在: {directory_path}")
            sys.exit(1)

        if not dir_path.is_dir():
            logger.error(f"路径不是一个目录: {directory_path}")
            sys.exit(1)

        # 查找所有HTML文件
        for ext in ['*.html', '*.htm']:
            html_files.extend(dir_path.glob(ext))

        # 转换为绝对路径字符串并排序
        html_files = sorted([str(f.absolute()) for f in html_files])

        if not html_files:
            logger.error(f"目录中没有找到HTML文件: {directory_path}")
            sys.exit(1)

        return html_files
    except Exception as e:
        logger.error(f"读取目录失败: {e}")
        sys.exit(1)


def generate_parsers_by_layout_clusters(
    html_files: list,
    base_output: str,
    domain: str | None = None,
) -> None:
    """按布局聚类后分别为每个簇生成解析器。

    这是一个可选的辅助方法，不在 main 的默认流程中强制调用。
    """

    # 读取HTML内容用于聚类
    html_contents = []
    for file_path in html_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_contents.append(f.read())

    # 使用布局相似度聚类HTML
    labels, sim_mat, clusters = cluster_html_layouts(html_contents)
    unique_labels = sorted(set(labels))

    logger.info("="*70)
    logger.info("HtmlParserAgent - 按布局簇生成解析器")
    logger.info("="*70)
    logger.info(f"共得到 {len(unique_labels)} 个簇（含噪声 -1），准备分别生成解析器")

    any_failure = False

    # 针对每个簇分别创建 Agent 并生成解析器
    for lbl in unique_labels:
        cluster_files = [p for p, l in zip(html_files, labels) if l == lbl]
        if not cluster_files:
            continue

        output_dir = f"{base_output}_cluster{lbl}"
        logger.info("-" * 70)
        logger.info(f"开始为簇 {lbl} 生成解析器，输出目录: {output_dir}")
        logger.info(f"该簇包含 {len(cluster_files)} 个HTML文件")

        agent = ParserAgent(output_dir=output_dir)
        result = agent.generate_parser(
            html_files=cluster_files,
            domain=domain,
        )

        if result['success']:
            logger.success(f"\n✓ 簇 {lbl} 的解析器生成成功!")
            logger.info(f"  解析器路径: {result['parser_path']}")
            logger.info(f"  配置路径: {result['config_path']}")
            logger.info("  使用方法:")
            logger.info(f"    python {result['parser_path']} <url_or_html_file>")
        else:
            any_failure = True
            logger.error(f"\n✗ 簇 {lbl} 的解析器生成失败")
            if 'error' in result:
                logger.error(f"  错误: {result['error']}")

    if any_failure:
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
  # 从目录读取HTML文件并生成解析器
  python main.py -d input_html/ -o output/blog
        """
    )

    parser.add_argument(
        '-d', '--directory',
        required=True,
        help='HTML文件目录路径（包含多个HTML源码文件）'
    )
    parser.add_argument(
        '-o', '--output',
        default='output',
        help='输出目录（默认: output）'
    )
    parser.add_argument(
        '--domain',
        help='域名（可选）'
    )
    parser.add_argument(
        '--cluster',
        action='store_true',
        help='是否按布局聚类分别生成解析器（默认: 否，使用全部HTML生成单个解析器）'
    )

    args = parser.parse_args()

    # 获取HTML文件列表
    logger.info(f"从目录读取HTML文件: {args.directory}")
    html_files = read_html_files_from_directory(args.directory)
    logger.info(f"读取到 {len(html_files)} 个HTML文件")

    # 根据 cluster 参数选择生成方式
    if args.cluster:
        # 按布局聚类分别生成解析器
        generate_parsers_by_layout_clusters(
            html_files=html_files,
            base_output=args.output,
            domain=args.domain,
        )
        return

    logger.info("="*70)
    logger.info("HtmlParserAgent - 智能网页解析代码生成器")
    logger.info("="*70)

    # 创建Agent
    agent = ParserAgent(output_dir=args.output)

    # 生成解析器（使用全部HTML文件，不做聚类拆分）
    result = agent.generate_parser(
        html_files=html_files,
        domain=args.domain
    )

    # 输出结果
    if result['success']:
        logger.success("\n✓ 解析器生成成功!")
        logger.info(f"  解析器路径: {result['parser_path']}")
        logger.info(f"  配置路径: {result['config_path']}")

        logger.info("\n使用方法:")
        logger.info(f"  python {result['parser_path']} <url_or_html_file>")
    else:
        logger.error("\n✗ 解析器生成失败")
        if 'error' in result:
            logger.error(f"  错误: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

