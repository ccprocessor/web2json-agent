"""
HtmlParserAgent 主程序
通过给定HTML文件目录，自动生成网页解析代码
"""
import sys
import argparse
import warnings
from pathlib import Path
from loguru import logger
from web2json.agent import ParserAgent
from web2json.tools.cluster import cluster_html_layouts

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
    eps: float | None = None,
    min_samples: int | None = None,
) -> None:
    """按布局聚类后分别为每个簇生成解析器。

    Args:
        html_files: HTML文件路径列表
        base_output: 输出目录基础路径
        domain: 域名（可选）
        eps: DBSCAN的eps参数，距离 = 1 - similarity，eps越小要求相似度越高（默认使用配置值）
        min_samples: DBSCAN的min_samples参数，形成簇所需的最小样本数（默认使用配置值）
    """
    from pathlib import Path
    import shutil
    from web2json.config.settings import settings

    # 使用配置中的默认值
    if eps is None:
        eps = settings.cluster_eps
    if min_samples is None:
        min_samples = settings.cluster_min_samples

    logger.info("="*70)
    logger.info("HtmlParserAgent - 按布局聚类生成解析器")
    logger.info("="*70)

    # 读取HTML内容用于聚类
    logger.info(f"正在读取 {len(html_files)} 个HTML文件...")
    html_contents = []
    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_contents.append(f.read())
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            sys.exit(1)

    # 使用布局相似度聚类HTML
    logger.info(f"正在进行布局聚类分析 (eps={eps}, min_samples={min_samples})...")
    try:
        labels, sim_mat, clusters = cluster_html_layouts(
            html_contents,
            eps=eps,
            min_samples=min_samples
        )
    except Exception as e:
        logger.error(f"聚类失败: {e}")
        sys.exit(1)

    # 统计聚类结果
    unique_labels = sorted(set(labels))
    noise_count = sum(1 for l in labels if l == -1)
    cluster_count = len([l for l in unique_labels if l != -1])

    logger.info("-"*70)
    logger.info("聚类分析完成:")
    logger.info(f"  总文件数: {len(html_files)}")
    logger.info(f"  识别出的布局簇数: {cluster_count}")
    logger.info(f"  噪声点（未归类）: {noise_count}")
    logger.info("-"*70)

    # 为每个簇输出详细信息
    for lbl in unique_labels:
        cluster_files = [p for p, l in zip(html_files, labels) if l == lbl]
        if lbl == -1:
            logger.info(f"噪声点 (label=-1): {len(cluster_files)} 个文件")
        else:
            logger.info(f"簇 {lbl}: {len(cluster_files)} 个文件")

    logger.info("="*70)

    # 保存聚类结果到文件
    base_output_path = Path(base_output)
    cluster_info_file = base_output_path.parent / f"{base_output_path.name}_cluster_info.txt"
    try:
        with open(cluster_info_file, 'w', encoding='utf-8') as f:
            f.write("HTML布局聚类结果\n")
            f.write("="*70 + "\n\n")
            f.write(f"聚类参数:\n")
            f.write(f"  eps: {eps}\n")
            f.write(f"  min_samples: {min_samples}\n\n")
            f.write(f"聚类统计:\n")
            f.write(f"  总文件数: {len(html_files)}\n")
            f.write(f"  布局簇数: {cluster_count}\n")
            f.write(f"  噪声点数: {noise_count}\n\n")

            for lbl in unique_labels:
                cluster_files = [p for p, l in zip(html_files, labels) if l == lbl]
                f.write(f"\n{'噪声点' if lbl == -1 else f'簇 {lbl}'} ({len(cluster_files)} 个文件):\n")
                for file_path in cluster_files:
                    f.write(f"  - {Path(file_path).name}\n")

        logger.info(f"聚类信息已保存到: {cluster_info_file}")
    except Exception as e:
        logger.warning(f"保存聚类信息失败: {e}")

    # 针对每个簇分别创建 Agent 并生成解析器
    any_failure = False
    successful_clusters = []

    for lbl in unique_labels:
        cluster_files = [p for p, l in zip(html_files, labels) if l == lbl]
        if not cluster_files:
            continue

        # 为噪声点使用特殊命名
        if lbl == -1:
            output_dir = f"{base_output}_noise"
            cluster_name = "噪声点"
        else:
            output_dir = f"{base_output}_cluster{lbl}"
            cluster_name = f"簇 {lbl}"

        logger.info("-" * 70)
        logger.info(f"开始为{cluster_name}生成解析器")
        logger.info(f"  输出目录: {output_dir}")
        logger.info(f"  HTML文件数: {len(cluster_files)}")

        # 将该簇的HTML文件复制到输出目录
        output_path = Path(output_dir)
        cluster_html_dir = output_path / "input_html"
        try:
            cluster_html_dir.mkdir(parents=True, exist_ok=True)
            for src_file in cluster_files:
                dst_file = cluster_html_dir / Path(src_file).name
                shutil.copy2(src_file, dst_file)
            logger.info(f"  已将{len(cluster_files)}个HTML文件复制到: {cluster_html_dir}")
        except Exception as e:
            logger.error(f"复制HTML文件失败: {e}")

        # 创建Agent并生成解析器
        try:
            agent = ParserAgent(output_dir=output_dir)
            result = agent.generate_parser(
                html_files=cluster_files,
                domain=domain,
            )

            if result['success']:
                logger.success(f"\n✓ {cluster_name}的解析器生成成功!")
                successful_clusters.append((lbl, cluster_name, result))
            else:
                any_failure = True
                logger.error(f"\n✗ {cluster_name}的解析器生成失败")
                if 'error' in result:
                    logger.error(f"  错误: {result['error']}")
        except Exception as e:
            any_failure = True
            logger.error(f"\n✗ {cluster_name}的解析器生成失败: {e}")

    # 输出总结
    logger.info("\n" + "="*70)
    logger.info("所有簇的解析器生成完成")
    logger.info("="*70)
    logger.info(f"总簇数: {len(unique_labels)}")
    logger.info(f"成功: {len(successful_clusters)}")
    logger.info(f"失败: {len(unique_labels) - len(successful_clusters)}")

    if successful_clusters:
        logger.info("\n成功生成的解析器:")
        for lbl, name, result in successful_clusters:
            logger.info(f"  {name}: {result['parser_path']}")

    if any_failure:
        logger.warning("\n部分簇的解析器生成失败，请检查日志")
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
  python web2json/main.py -d input_html/ -o output/blog
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
    parser.add_argument(
        '--iteration-rounds',
        type=int,
        default=3,
        help='迭代轮数（用于Schema学习的样本数量，默认: 3）'
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

    # 创建Agent
    agent = ParserAgent(output_dir=args.output)

    # 生成解析器（使用全部HTML文件，不做聚类拆分）
    result = agent.generate_parser(
        html_files=html_files,
        domain=args.domain,
        iteration_rounds=args.iteration_rounds
    )

    # 输出结果
    if not result['success']:
        logger.error("\n✗ 解析器生成失败")
        if 'error' in result:
            logger.error(f"  错误: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

