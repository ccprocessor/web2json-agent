"""
web2json-agent CLI 入口点
提供 pip 安装后的命令行接口，支持多个子命令
"""
import sys
import argparse
from pathlib import Path
from config.validator import ConfigValidator, check_config_or_guide


def cmd_init(args):
    """初始化配置文件"""
    print("\n🚀 初始化 web2json-agent 配置\n")

    target_dir = Path(args.dir) if args.dir else Path.cwd()
    env_file = ConfigValidator.create_env_file(target_dir)

    print("\n下一步:")
    print(f"  1. 编辑 {env_file}")
    print("  2. 填入你的 API 密钥（OPENAI_API_KEY 和 OPENAI_API_BASE）")
    print("  3. 运行 'web2json check --test-api' 检查API响应")
    print()


def cmd_setup(args):
    """交互式配置向导"""
    print("\n🚀 web2json-agent 交互式配置\n")
    ConfigValidator.interactive_setup()


def cmd_check(args):
    """检查配置"""
    print("\n🔍 检查配置...\n")
    is_valid, missing = ConfigValidator.check_config(verbose=True)

    if not is_valid:
        print("\n❌ 配置不完整")
        print("\n解决方法:")
        print("  1. 运行 'web2json init' 创建配置文件")
        print("  2. 或运行 'web2json setup' 使用交互式配置向导")
        sys.exit(1)

    # 如果基本配置通过，且用户要求测试 API
    if args.test_api:
        print("\n🔌 测试 API 连接...\n")
        api_valid, errors = ConfigValidator.test_api_connection(test_models=True)

        if not api_valid:
            print("\n❌ API 连接测试失败")
            for model_name, error in errors.items():
                print(f"  ✗ {model_name}: {error}")
            print("\n请检查:")
            print("  1. API 密钥是否正确")
            print("  2. API Base URL 是否可访问")
            print("  3. 模型名称是否正确")
            print("  4. 网络连接是否正常")
            sys.exit(1)

    print("\n✅ 所有检查通过！可以开始使用了")
    print("\n示例命令:")
    print("  web2json -d input_html/ -o output/blog")



def cmd_generate(args):
    """生成解析器（主功能）"""
    # 在执行主功能前检查配置
    if not args.skip_config_check:
        check_config_or_guide()

    # 导入并执行主程序
    from main import main as main_func, setup_logger, read_html_files_from_directory
    from agent import ParserAgent
    from loguru import logger

    setup_logger()

    logger.info("="*70)
    logger.info("web2json-agent - 智能网页解析代码生成器")
    logger.info("="*70)

    # 获取HTML文件列表
    logger.info(f"从目录读取HTML文件: {args.directory}")
    html_files = read_html_files_from_directory(args.directory)
    logger.info(f"读取到 {len(html_files)} 个HTML文件")

    # 创建Agent
    agent = ParserAgent(output_dir=args.output)

    # 生成解析器
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


def main():
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        prog='web2json',
        description='web2json-agent - 智能网页解析代码生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 首次使用：初始化配置
  web2json init
  web2json setup          # 或使用交互式配置向导

  # 检查配置
  web2json check
  web2json check --test-api

  # 从目录读取HTML文件并生成解析器
  web2json -d input_html/ -o output/blog

更多信息: https://github.com/ccprocessor/web2json-agent
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # init 命令
    parser_init = subparsers.add_parser('init', help='初始化配置文件')
    parser_init.add_argument(
        '--dir',
        help='配置文件目录（默认: 当前目录）'
    )
    parser_init.set_defaults(func=cmd_init)

    # setup 命令
    parser_setup = subparsers.add_parser('setup', help='交互式配置向导')
    parser_setup.set_defaults(func=cmd_setup)

    # check 命令
    parser_check = subparsers.add_parser('check', help='检查配置')
    parser_check.add_argument(
        '--test-api',
        action='store_true',
        help='测试 API 连接和模型可用性'
    )
    parser_check.set_defaults(func=cmd_check)

    # 主命令参数（生成解析器）
    parser.add_argument(
        '-d', '--directory',
        help='HTML文件目录路径'
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
        '--skip-config-check',
        action='store_true',
        help='跳过配置检查（不推荐）'
    )

    # 解析参数
    args = parser.parse_args()

    # 如果没有指定子命令，检查是否提供了目录参数
    if args.command is None:
        if args.directory:
            # 当作生成命令处理
            cmd_generate(args)
        else:
            # 显示帮助信息
            parser.print_help()
            print("\n💡 提示: 首次使用请先运行 'web2json init' 或 'web2json setup'")
    else:
        # 执行子命令
        args.func(args)


if __name__ == "__main__":
    main()
