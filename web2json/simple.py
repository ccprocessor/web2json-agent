"""
Simple API for web2json
提供简洁易用的API接口
"""
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from loguru import logger

from web2json.agent import ParserAgent


@dataclass
class Web2JsonConfig:
    """Web2JSON统一配置类

    Args:
        name: 运行名称（在output_dir下创建此名称的子目录）
        html_path: HTML文件目录
        output_dir: 输出主目录（默认为"output"）
        iteration_rounds: 迭代轮数（用于Schema学习的样本数量，默认3）
        schema: Schema模板（可选，为None时使用auto模式，有值时使用predefined模式）

    Example:
        >>> config = Web2JsonConfig(
        ...     name="my_run",
        ...     html_path="html_samples/",
        ...     output_dir="output/",
        ...     iteration_rounds=3,
        ...     schema={"title": "string", "author": "string"}
        ... )
    """
    name: str
    html_path: str
    output_dir: str = "output"
    iteration_rounds: int = 3
    schema: Optional[Dict] = None

    def __post_init__(self):
        """验证配置"""
        if self.iteration_rounds < 1:
            raise ValueError(f"iteration_rounds必须大于0，当前值: {self.iteration_rounds}")

    def get_output_path(self) -> str:
        """获取完整输出路径"""
        return f"{self.output_dir}/{self.name}"

    def is_auto_mode(self) -> bool:
        """判断是否为auto模式"""
        return self.schema is None or len(self.schema) == 0

    def is_predefined_mode(self) -> bool:
        """判断是否为predefined模式"""
        return not self.is_auto_mode()


def _setup_logger():
    """配置日志显示"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )


def _read_html_files(directory_path: str) -> List[str]:
    """从目录读取HTML文件列表

    Args:
        directory_path: HTML文件目录路径

    Returns:
        HTML文件路径列表（绝对路径）

    Raises:
        FileNotFoundError: 目录不存在或没有HTML文件
        ValueError: 路径不是目录
    """
    dir_path = Path(directory_path)

    if not dir_path.exists():
        raise FileNotFoundError(f"目录不存在: {directory_path}")

    if not dir_path.is_dir():
        raise ValueError(f"路径不是一个目录: {directory_path}")

    # 查找所有HTML文件
    html_files = []
    for ext in ['*.html', '*.htm']:
        html_files.extend(dir_path.glob(ext))

    # 转换为绝对路径字符串并排序
    html_files = sorted([str(f.absolute()) for f in html_files])

    if not html_files:
        raise FileNotFoundError(f"目录中没有找到HTML文件: {directory_path}")

    return html_files


def extract_html_to_json(config: Web2JsonConfig) -> str:
    """API 1: 从HTML提取JSON数据（完整流程）

    执行完整的工作流程：
    1. 分析HTML样本，学习数据结构
    2. 生成parser代码
    3. 使用parser解析所有HTML文件
    4. 输出所有结果（schema、parser、JSON数据）

    Args:
        config: Web2JsonConfig配置对象

    Returns:
        输出目录路径

    Raises:
        Exception: 执行失败时抛出异常

    Example:
        >>> config = Web2JsonConfig(
        ...     name="my_run",
        ...     html_path="html_samples/",
        ...     output_dir="output/",
        ...     iteration_rounds=3
        ... )
        >>> result_dir = extract_html_to_json(config)
        >>> print(f"结果保存在: {result_dir}")
    """
    _setup_logger()

    logger.info(f"[API] extract_html_to_json - 完整流程")
    logger.info(f"  HTML路径: {config.html_path}")
    logger.info(f"  输出目录: {config.get_output_path()}")
    logger.info(f"  模式: {'Predefined' if config.is_predefined_mode() else 'Auto'}")
    logger.info(f"  样本数: {config.iteration_rounds}")

    # 读取HTML文件
    html_files = _read_html_files(config.html_path)
    logger.info(f"找到 {len(html_files)} 个HTML文件")

    # 确定输出目录
    output_path = Path(config.get_output_path()).absolute()
    output_path.mkdir(parents=True, exist_ok=True)

    # 确定schema模式
    if config.is_predefined_mode():
        schema_mode = "predefined"
        schema_template = config.schema
    else:
        schema_mode = "auto"
        schema_template = None

    # 创建Agent并执行完整流程
    agent = ParserAgent(output_dir=str(output_path))
    result = agent.generate_parser(
        html_files=html_files,
        iteration_rounds=config.iteration_rounds,
        schema_mode=schema_mode,
        schema_template=schema_template
    )

    if not result['success']:
        error_msg = result.get('error', '未知错误')
        raise Exception(f"执行失败: {error_msg}")

    logger.info("✓ 执行成功")
    logger.info(f"  Parser: {result.get('parser_path')}")
    logger.info(f"  结果目录: {result.get('results_dir')}")

    return str(output_path)


def infer_html_to_schema(config: Web2JsonConfig) -> str:
    """API 2: 从HTML推断Schema

    仅执行Schema学习阶段，不生成parser代码。
    适用场景：
    - 想先了解HTML的数据结构
    - 需要基于自动生成的schema进行调整后再生成parser

    Args:
        config: Web2JsonConfig配置对象

    Returns:
        Schema文件路径

    Raises:
        Exception: 执行失败时抛出异常

    Example:
        >>> config = Web2JsonConfig(
        ...     name="my_schema",
        ...     html_path="html_samples/",
        ...     output_dir="output/",
        ...     iteration_rounds=3
        ... )
        >>> schema_path = infer_html_to_schema(config)
        >>> print(f"Schema保存在: {schema_path}")
    """
    _setup_logger()

    logger.info(f"[API] infer_html_to_schema - 仅生成Schema")
    logger.info(f"  HTML路径: {config.html_path}")
    logger.info(f"  输出目录: {config.get_output_path()}")
    logger.info(f"  样本数: {config.iteration_rounds}")

    # 读取HTML文件
    html_files = _read_html_files(config.html_path)
    logger.info(f"找到 {len(html_files)} 个HTML文件")

    # 确定输出目录
    output_path = Path(config.get_output_path()).absolute()
    output_path.mkdir(parents=True, exist_ok=True)

    # 创建Agent并只执行Schema学习阶段
    agent = ParserAgent(output_dir=str(output_path))

    # 手动执行Schema阶段
    from web2json.agent.planner import AgentPlanner
    planner = AgentPlanner()
    plan = planner.create_plan(html_files, iteration_rounds=config.iteration_rounds)

    # 只执行Schema迭代阶段
    schema_result = agent.executor.schema_phase.run(plan)

    if not schema_result.get('success', False):
        error_msg = schema_result.get('error', '未知错误')
        raise Exception(f"Schema生成失败: {error_msg}")

    schema_path = schema_result.get('final_schema_path')
    logger.info("✓ Schema生成成功")
    logger.info(f"  Schema路径: {schema_path}")

    return schema_path


def generate_html_parser(config: Web2JsonConfig) -> str:
    """API 3: 生成HTML Parser代码

    执行完整的parser生成流程（包括Schema学习和代码生成），但不解析HTML文件。
    适用场景：
    - 只需要parser代码，后续手动使用
    - 需要检查生成的parser代码

    Args:
        config: Web2JsonConfig配置对象

    Returns:
        Parser文件路径

    Raises:
        Exception: 执行失败时抛出异常

    Example:
        >>> config = Web2JsonConfig(
        ...     name="my_parser",
        ...     html_path="html_samples/",
        ...     output_dir="output/",
        ...     iteration_rounds=3,
        ...     schema={"title": "string", "author": "string"}
        ... )
        >>> parser_path = generate_html_parser(config)
        >>> print(f"Parser保存在: {parser_path}")
    """
    _setup_logger()

    logger.info(f"[API] generate_html_parser - 仅生成Parser代码")
    logger.info(f"  HTML路径: {config.html_path}")
    logger.info(f"  输出目录: {config.get_output_path()}")
    logger.info(f"  模式: {'Predefined' if config.is_predefined_mode() else 'Auto'}")
    logger.info(f"  样本数: {config.iteration_rounds}")

    # 读取HTML文件
    html_files = _read_html_files(config.html_path)
    logger.info(f"找到 {len(html_files)} 个HTML文件")

    # 确定输出目录
    output_path = Path(config.get_output_path()).absolute()
    output_path.mkdir(parents=True, exist_ok=True)

    # 确定schema模式
    if config.is_predefined_mode():
        schema_mode = "predefined"
        schema_template = config.schema
    else:
        schema_mode = "auto"
        schema_template = None

    # 创建Agent
    agent = ParserAgent(output_dir=str(output_path))

    # 创建执行计划
    from web2json.agent.planner import AgentPlanner
    planner = AgentPlanner()
    plan = planner.create_plan(html_files, iteration_rounds=config.iteration_rounds)

    # 更新schema模式
    if schema_mode == "predefined":
        agent.executor.schema_mode = schema_mode
        agent.executor.schema_template = schema_template
        agent.executor.schema_processor.schema_mode = schema_mode
        agent.executor.schema_processor.schema_template = schema_template
        agent.executor.schema_phase.schema_mode = schema_mode

    # 执行计划（生成parser但不批量解析）
    execution_result = agent.executor.execute_plan(plan)

    if not execution_result['success']:
        error_msg = execution_result.get('error', '未知错误')
        raise Exception(f"Parser生成失败: {error_msg}")

    parser_path = execution_result['final_parser']['parser_path']
    logger.info("✓ Parser生成成功")
    logger.info(f"  Parser路径: {parser_path}")

    return parser_path


def parse_html_with_parser(config: Web2JsonConfig, parser_path: str) -> str:
    """API 4: 使用已有Parser解析HTML文件

    使用已经生成的parser来解析新的HTML文件。
    适用场景：
    - 已经有了一个训练好的parser
    - 需要解析新的、结构相同的HTML文件

    Args:
        config: Web2JsonConfig配置对象
        parser_path: Parser文件路径

    Returns:
        结果目录路径（包含所有解析后的JSON文件）

    Raises:
        Exception: 执行失败时抛出异常
        FileNotFoundError: Parser文件不存在

    Example:
        >>> config = Web2JsonConfig(
        ...     name="parse_new_data",
        ...     html_path="new_html_samples/",
        ...     output_dir="output/"
        ... )
        >>> result_dir = parse_html_with_parser(
        ...     config,
        ...     parser_path="output/my_run/parsers/final_parser.py"
        ... )
        >>> print(f"结果保存在: {result_dir}")
    """
    _setup_logger()

    logger.info(f"[API] parse_html_with_parser - 使用已有Parser解析")
    logger.info(f"  HTML路径: {config.html_path}")
    logger.info(f"  Parser路径: {parser_path}")
    logger.info(f"  输出目录: {config.get_output_path()}")

    # 检查parser文件是否存在
    parser_file = Path(parser_path)
    if not parser_file.exists():
        raise FileNotFoundError(f"Parser文件不存在: {parser_path}")

    # 读取HTML文件
    html_files = _read_html_files(config.html_path)
    logger.info(f"找到 {len(html_files)} 个HTML文件")

    # 确定输出目录
    output_path = Path(config.get_output_path()).absolute()
    output_path.mkdir(parents=True, exist_ok=True)

    # 创建Agent并执行批量解析
    agent = ParserAgent(output_dir=str(output_path))

    # 直接调用批量解析方法
    parse_result = agent.executor.parse_all_html_files(
        html_files=html_files,
        parser_path=str(parser_file.absolute())
    )

    if not parse_result.get('success', False):
        error_msg = parse_result.get('error', '未知错误')
        raise Exception(f"批量解析失败: {error_msg}")

    results_dir = parse_result.get('output_dir')
    logger.info("✓ 解析成功")
    logger.info(f"  成功: {len(parse_result.get('parsed_files', []))} 个文件")
    logger.info(f"  结果目录: {results_dir}")

    return results_dir

