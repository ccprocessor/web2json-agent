"""
Simple API for web2json
提供简洁易用的API接口
"""
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from loguru import logger

from web2json.agent import ParserAgent


@dataclass
class Web2JsonConfig:
    """Web2JSON统一配置类

    Args:
        html_path: HTML文件目录
        output_dir: 输出主目录（默认为"output"）
        name: 运行名称（在output_dir下创建此名称的子目录）
        iteration_rounds: 迭代轮数（用于Schema学习的样本数量，默认3）
        schema: Schema模板（可选，为None时使用auto模式，有值时使用predefined模式）
        outputs: 控制保留的输出内容，可选值：["data", "code", "schema"]
                - "data": 保留解析后的JSON数据
                - "code": 保留生成的parser代码
                - "schema": 保留生成的schema文件

    Example:
        >>> config = Web2JsonConfig(
        ...     html_path="html_samples/",
        ...     output_dir="output/",
        ...     name="my_run",
        ...     iteration_rounds=3,
        ...     schema={"title": "string", "author": "string"},
        ...     outputs=["data", "code", "schema"]
        ... )
    """
    html_path: str
    output_dir: str = "output"
    name: str = "web2json_run"
    iteration_rounds: int = 3
    schema: Optional[Dict] = None
    outputs: List[str] = field(default_factory=lambda: ["data", "code", "schema"])
    parser_path: Optional[str] = None  # 用于parse_data API

    def __post_init__(self):
        """验证配置"""
        if self.iteration_rounds < 1:
            raise ValueError(f"iteration_rounds必须大于0，当前值: {self.iteration_rounds}")

        valid_outputs = {"data", "code", "schema"}
        for output in self.outputs:
            if output not in valid_outputs:
                raise ValueError(f"outputs只能包含 {valid_outputs}，当前有无效值: {output}")

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
    logger.remove()  # 移除所有默认处理器
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG"  # 改为DEBUG级别以显示详细信息
    )


def _read_html_files_from_directory(directory_path: str) -> List[str]:
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


def _copy_final_outputs(temp_dir: str, final_dir: str, keep_outputs: List[str]):
    """从临时目录复制最终文件到输出目录

    Args:
        temp_dir: 临时工作目录
        final_dir: 最终输出目录
        keep_outputs: 要保留的输出类型列表
    """
    import shutil

    temp_path = Path(temp_dir)
    final_path = Path(final_dir)

    # 确保最终输出目录存在
    final_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"开始复制最终输出文件...")
    logger.info(f"  临时目录: {temp_path}")
    logger.info(f"  最终目录: {final_path}")
    logger.info(f"  要保留: {keep_outputs}")

    # 定义各类输出的最终文件
    output_files = {
        "data": {
            "source": "result",
            "target": "result",
            "copy_all": True  # 复制整个目录
        },
        "code": {
            "source": "parsers/final_parser.py",
            "target": "parsers/final_parser.py",
            "copy_all": False
        },
        "schema": {
            "source": "schemas/final_schema.json",
            "target": "schemas/final_schema.json",
            "copy_all": False
        }
    }

    # 根据用户配置复制文件
    for output_type in keep_outputs:
        if output_type not in output_files:
            logger.warning(f"未知的输出类型: {output_type}，跳过")
            continue

        config = output_files[output_type]
        source = temp_path / config["source"]
        target = final_path / config["target"]

        logger.debug(f"处理 {output_type}:")
        logger.debug(f"  源: {source}")
        logger.debug(f"  目标: {target}")
        logger.debug(f"  源存在: {source.exists()}")

        if not source.exists():
            logger.warning(f"⚠ 源文件/目录不存在，跳过: {source}")
            continue

        try:
            if config["copy_all"]:
                # 复制整个目录（如result目录）
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(source, target)
                logger.info(f"✓ 已复制 {output_type} 目录到输出")
            else:
                # 复制单个文件
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                logger.info(f"✓ 已复制 {output_type} 文件到输出")
        except Exception as e:
            logger.error(f"✗ 复制 {output_type} 失败: {e}")

    logger.info(f"文件复制完成")


def _cleanup_temp_dir(temp_dir: str):
    """清理临时目录

    Args:
        temp_dir: 临时目录路径
    """
    import shutil

    temp_path = Path(temp_dir)
    if temp_path.exists():
        shutil.rmtree(temp_path)
        logger.debug(f"已清理临时目录: {temp_dir}")


def extract_data(config: Web2JsonConfig) -> str:
    """完整流程：生成parser + 解析所有HTML文件

    这是主要的API函数，执行完整的工作流程：
    1. 分析HTML样本，学习数据结构
    2. 生成parser代码
    3. 使用parser解析所有HTML文件
    4. 只复制用户需要的输出到最终目录

    Args:
        config: Web2JsonConfig配置对象

    Returns:
        输出目录路径

    Raises:
        Exception: 执行失败时抛出异常

    Example:
        >>> config = Web2JsonConfig(
        ...     html_path="html_samples/",
        ...     output_dir="output/",
        ...     name="my_run",
        ...     iteration_rounds=3,
        ...     outputs=["data", "code"]
        ... )
        >>> result_dir = extract_data(config)
        >>> print(f"结果保存在: {result_dir}")
    """
    _setup_logger()

    logger.info(f"开始执行 extract_data")
    logger.info(f"  HTML路径: {config.html_path}")
    logger.info(f"  输出目录: {config.get_output_path()}")
    logger.info(f"  模式: {'Predefined' if config.is_predefined_mode() else 'Auto'}")
    logger.info(f"  样本数: {config.iteration_rounds}")
    logger.info(f"  保留输出: {config.outputs}")

    # 读取HTML文件
    html_files = _read_html_files_from_directory(config.html_path)
    logger.info(f"找到 {len(html_files)} 个HTML文件")

    # 创建临时工作目录（隐藏目录）
    import time
    timestamp = int(time.time())
    temp_dir = f".temp_web2json_{timestamp}_{config.name}"
    temp_path = Path(temp_dir).absolute()

    # 最终输出目录
    final_output_path = config.get_output_path()

    try:
        logger.debug(f"临时工作目录: {temp_path}")

        # 确定schema模式
        if config.is_predefined_mode():
            schema_mode = "predefined"
            schema_template = config.schema
        else:
            schema_mode = "auto"
            schema_template = None

        # 创建Agent并在临时目录中执行
        agent = ParserAgent(output_dir=str(temp_path))
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

        # 从临时目录复制最终文件到输出目录
        _copy_final_outputs(str(temp_path), final_output_path, config.outputs)

    finally:
        # 清理临时目录
        _cleanup_temp_dir(str(temp_path))

    return final_output_path


def parse_data(config: Web2JsonConfig) -> str:
    """使用已有parser解析HTML文件

    这是第二个主要API，用于使用已经生成的parser来解析新的HTML文件。
    适用场景：
    - 已经有了一个训练好的parser
    - 需要解析新的、结构相同的HTML文件

    Args:
        config: Web2JsonConfig配置对象，必须包含parser_path

    Returns:
        结果目录路径（包含所有解析后的JSON文件）

    Raises:
        Exception: 执行失败时抛出异常
        ValueError: 未提供parser_path时抛出

    Example:
        >>> config = Web2JsonConfig(
        ...     html_path="new_html_samples/",
        ...     output_dir="output/",
        ...     name="parse_new_data",
        ...     parser_path="output/my_run/parsers/final_parser.py",
        ...     outputs=["data"]
        ... )
        >>> result_dir = parse_data(config)
        >>> print(f"结果保存在: {result_dir}")
    """
    _setup_logger()

    if not config.parser_path:
        raise ValueError("parse_data API 必须提供 parser_path 参数")

    logger.info(f"开始执行 parse_data")
    logger.info(f"  HTML路径: {config.html_path}")
    logger.info(f"  Parser路径: {config.parser_path}")
    logger.info(f"  输出目录: {config.get_output_path()}")

    # 检查parser文件是否存在
    parser_file = Path(config.parser_path)
    if not parser_file.exists():
        raise FileNotFoundError(f"Parser文件不存在: {config.parser_path}")

    # 读取HTML文件
    html_files = _read_html_files_from_directory(config.html_path)
    logger.info(f"找到 {len(html_files)} 个HTML文件")

    # 创建临时工作目录（隐藏目录）
    import time
    timestamp = int(time.time())
    temp_dir = f".temp_web2json_{timestamp}_{config.name}"
    temp_path = Path(temp_dir).absolute()

    # 最终输出目录
    final_output_path = config.get_output_path()

    try:
        logger.debug(f"临时工作目录: {temp_path}")

        # 创建Agent并执行批量解析（在临时目录）
        agent = ParserAgent(output_dir=str(temp_path))

        # 直接调用批量解析方法
        parse_result = agent.executor.parse_all_html_files(
            html_files=html_files,
            parser_path=str(parser_file.absolute())
        )

        if not parse_result.get('success', False):
            error_msg = parse_result.get('error', '未知错误')
            raise Exception(f"批量解析失败: {error_msg}")

        logger.info("✓ 解析成功")

        # 从临时目录复制最终文件到输出目录
        _copy_final_outputs(str(temp_path), final_output_path, config.outputs)

    finally:
        # 清理临时目录
        _cleanup_temp_dir(str(temp_path))

    return final_output_path


# 为了保持向后兼容，保留旧的函数名作为别名
def generate_parser(config: Web2JsonConfig) -> str:
    """生成parser代码（保留向后兼容）

    实际上调用extract_data，但只保留code输出

    Returns:
        parser文件的完整路径
    """
    # 修改outputs只保留code
    original_outputs = config.outputs
    config.outputs = ["code"]

    try:
        output_path = extract_data(config)
        parser_path = Path(output_path) / "parsers" / "final_parser.py"
        return str(parser_path)
    finally:
        # 恢复原始配置
        config.outputs = original_outputs


def generate_schema(config: Web2JsonConfig) -> str:
    """生成schema（保留向后兼容）

    实际上调用extract_data，但只保留schema输出

    Returns:
        schema文件的完整路径
    """
    # 修改outputs只保留schema
    original_outputs = config.outputs
    config.outputs = ["schema"]

    try:
        output_path = extract_data(config)
        schema_path = Path(output_path) / "schemas" / "final_schema.json"
        return str(schema_path)
    finally:
        # 恢复原始配置
        config.outputs = original_outputs
