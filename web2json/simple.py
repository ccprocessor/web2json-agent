"""
Simple API for web2json
提供简洁易用的API接口
"""
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from loguru import logger

from web2json.agent import ParserAgent


@dataclass
class ExtractDataResult:
    """完整流程的返回结果"""
    final_schema: Dict                      # 最终Schema
    parser_code: str                        # Parser代码字符串
    parsed_data: List[Dict[str, Any]]       # 所有解析后的数据 [{filename: "xx.html", data: {...}}, ...]

    def to_dict(self) -> Dict:
        """转换为字典（便于序列化到数据库）"""
        return asdict(self)

    def get_summary(self) -> str:
        """获取摘要信息"""
        return f"解析了 {len(self.parsed_data)} 个文件，Schema包含 {len(self.final_schema)} 个字段"


@dataclass
class ExtractSchemaResult:
    """Schema提取结果"""
    final_schema: Dict                      # 最终Schema
    intermediate_schemas: List[Dict]        # 中间迭代的schemas

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    def get_summary(self) -> str:
        """获取摘要信息"""
        return f"Schema包含 {len(self.final_schema)} 个字段，经过 {len(self.intermediate_schemas)} 轮迭代"


@dataclass
class InferCodeResult:
    """代码生成结果"""
    parser_code: str                        # Parser代码字符串
    schema: Dict                            # 使用的Schema

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    def get_summary(self) -> str:
        """获取摘要信息"""
        return f"生成了 {len(self.parser_code)} 字符的Parser代码，基于 {len(self.schema)} 个字段的Schema"


@dataclass
class ParseResult:
    """批量解析结果"""
    parsed_data: List[Dict[str, Any]]       # [{filename: "xx.html", data: {...}}, ...]
    success_count: int                      # 成功解析数量
    failed_count: int                       # 失败数量

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    def get_summary(self) -> str:
        """获取摘要信息"""
        return f"解析了 {self.success_count} 个文件成功，{self.failed_count} 个失败"


@dataclass
class ClusterResult:
    """聚类结果"""
    clusters: Dict[str, List[str]]          # {"cluster_0": ["file1.html", ...], ...}
    labels: List[int]                       # 每个文件的标签
    noise_files: List[str]                  # 噪声点文件列表
    cluster_count: int                      # 聚类数量

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    def get_summary(self) -> str:
        """获取摘要信息"""
        total_files = sum(len(files) for files in self.clusters.values())
        return f"识别出 {self.cluster_count} 个布局簇，共 {total_files} 个文件，{len(self.noise_files)} 个噪声点"


@dataclass
class Web2JsonConfig:
    """Web2JSON统一配置类

    Args:
        name: 运行名称（在output_path下创建此名称的子目录）
        html_path: HTML文件目录
        output_path: 输出主目录（默认为"output"）
        iteration_rounds: 迭代轮数（用于Schema学习的样本数量，默认3）
        schema: Schema模板（可选，为None时使用auto模式，有值时使用predefined模式）
        enable_schema_edit: 是否启用schema人工编辑（默认False，仅在auto模式下有效）
        parser_code: Parser代码内容（可选，用于extract_data_with_code API）
        save: 要保存到本地的内容列表（可选，例如 ['schema', 'code', 'data']）
              为None或空列表时不保存，仅在内存中返回结果

    Example:
        >>> config = Web2JsonConfig(
        ...     name="my_run",
        ...     html_path="html_samples/",
        ...     output_path="output/",
        ...     iteration_rounds=3,
        ...     schema={"title": "string", "author": "string"},
        ...     save=['schema', 'code', 'data']
        ... )
    """
    name: str
    html_path: str
    output_path: str = "output"
    iteration_rounds: int = 3
    schema: Optional[Dict] = None
    enable_schema_edit: bool = False
    parser_code: Optional[str] = None
    save: Optional[List[str]] = None

    def __post_init__(self):
        """验证配置"""
        if self.iteration_rounds < 1:
            raise ValueError(f"iteration_rounds必须大于0，当前值: {self.iteration_rounds}")

    def get_full_output_path(self) -> str:
        """获取完整输出路径"""
        return f"{self.output_path}/{self.name}"

    def should_save(self) -> bool:
        """判断是否需要保存到本地"""
        return self.save is not None and len(self.save) > 0

    def should_save_item(self, item: str) -> bool:
        """判断是否需要保存特定项"""
        return self.should_save() and item in self.save

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
    """从目录或单个文件读取HTML文件列表

    Args:
        directory_path: HTML文件目录路径或单个文件路径

    Returns:
        HTML文件路径列表（绝对路径）

    Raises:
        FileNotFoundError: 路径不存在或没有HTML文件
    """
    path = Path(directory_path)

    if not path.exists():
        raise FileNotFoundError(f"路径不存在: {directory_path}")

    # 如果是单个文件，直接返回
    if path.is_file():
        if path.suffix.lower() in ['.html', '.htm']:
            return [str(path.absolute())]
        else:
            raise ValueError(f"文件不是HTML文件: {directory_path}")

    # 如果是目录，查找所有HTML文件
    if path.is_dir():
        html_files = []
        for ext in ['*.html', '*.htm']:
            html_files.extend(path.glob(ext))

        # 转换为绝对路径字符串并排序
        html_files = sorted([str(f.absolute()) for f in html_files])

        if not html_files:
            raise FileNotFoundError(f"目录中没有找到HTML文件: {directory_path}")

        return html_files

    raise ValueError(f"路径既不是文件也不是目录: {directory_path}")


def _cleanup_unwanted_files(output_path: Path, save_items: List[str], api_type: str = "extract_data"):
    """
    清理不需要保存的文件，只保留save列表中指定的内容

    Args:
        output_path: 输出目录路径
        save_items: 要保存的内容列表（如 ['schema', 'code', 'data']）
        api_type: API类型，用于确定可清理的目录
    """
    import shutil

    if not output_path.exists():
        return

    # 定义各个API支持保存的内容及其对应的文件/目录
    save_mappings = {
        'extract_data': {
            'schema': ['schemas/final_schema.json'],
            'code': ['parsers/final_parser.py'],
            'data': ['result/'],
        },
        'extract_schema': {
            'schema': ['schemas/final_schema.json'],
        },
        'infer_code': {
            'code': ['parsers/final_parser.py'],
            'schema': ['schemas/final_schema.json'],
        },
        'extract_data_with_code': {
            'data': ['result/'],
            'code': ['parsers/final_parser.py'],
        },
        'classify_html_dir': {
            'report': ['cluster_report.json', 'cluster_info.txt'],
            'files': ['clusters/'],
        }
    }

    mapping = save_mappings.get(api_type, {})

    # 第一步：复制需要保留的文件到根目录（方便访问）
    for item in save_items:
        if item == 'schema':
            src = output_path / 'schemas' / 'final_schema.json'
            dst = output_path / 'schema.json'
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
        elif item == 'code':
            src = output_path / 'parsers' / 'final_parser.py'
            dst = output_path / 'final_parser.py'
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)

    # 第二步：删除所有临时目录（如果不需要保留）
    always_remove = ['html_original', 'html_simplified', 'schemas', 'parsers']
    for dir_name in always_remove:
        dir_path = output_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            shutil.rmtree(dir_path)
            logger.debug(f"  已清理临时目录: {dir_name}/")

    # 第三步：清理result目录（如果不需要保留data）
    if 'data' not in save_items:
        result_dir = output_path / 'result'
        if result_dir.exists() and result_dir.is_dir():
            shutil.rmtree(result_dir)
            logger.debug(f"  已清理结果目录: result/")


def extract_data(config: Web2JsonConfig) -> ExtractDataResult:
    """API 1: 从HTML提取数据（完整流程）

    执行完整的工作流程：
    1. 分析HTML样本，学习数据结构（支持预定义schema或自动生成）
    2. 如果enable_schema_edit=True，允许用户手动编辑schema
    3. 生成parser代码
    4. 使用parser解析所有HTML文件
    5. 返回所有结果（schema、code、data）在内存中

    Args:
        config: Web2JsonConfig配置对象
            - schema: 预定义schema（可选），不为空时使用predefined模式
            - enable_schema_edit: 是否启用人工编辑（仅在auto模式下有效）

    Returns:
        ExtractDataResult: 包含final_schema、parser_code、parsed_data的结果对象

    Raises:
        Exception: 执行失败时抛出异常

    Example:
        >>> # 自动模式，不启用人工编辑
        >>> config = Web2JsonConfig(
        ...     name="auto_run",
        ...     html_path="html_samples/",
        ...     iteration_rounds=3
        ... )
        >>> result = extract_data(config)
        >>> print(result.final_schema)  # 打印Schema
        >>> print(result.parsed_data[0])  # 打印第一个解析结果

        >>> # 自动模式，启用人工编辑
        >>> config = Web2JsonConfig(
        ...     name="auto_with_edit",
        ...     html_path="html_samples/",
        ...     enable_schema_edit=True
        ... )
        >>> result = extract_data(config)

        >>> # 预定义模式
        >>> config = Web2JsonConfig(
        ...     name="predefined_run",
        ...     html_path="html_samples/",
        ...     schema={"title": "string", "author": "string"}
        ... )
        >>> result = extract_data(config)
    """
    _setup_logger()

    logger.info(f"[API] extract_data - 完整流程")
    logger.info(f"  HTML路径: {config.html_path}")
    logger.info(f"  模式: {'Predefined' if config.is_predefined_mode() else 'Auto'}")
    logger.info(f"  样本数: {config.iteration_rounds}")
    if config.is_auto_mode():
        logger.info(f"  人工编辑: {'启用' if config.enable_schema_edit else '禁用'}")
    if config.should_save():
        logger.info(f"  保存内容: {', '.join(config.save)}")
        logger.info(f"  输出路径: {config.get_full_output_path()}")

    # 读取HTML文件
    html_files = _read_html_files(config.html_path)
    logger.info(f"找到 {len(html_files)} 个HTML文件")

    # 根据是否需要保存决定使用临时目录还是持久目录
    import tempfile
    import shutil
    import os

    use_temp_dir = not config.should_save()
    if use_temp_dir:
        temp_output_dir = tempfile.mkdtemp(prefix="web2json_")
        output_path = Path(temp_output_dir)
    else:
        output_path = Path(config.get_full_output_path())
        output_path.mkdir(parents=True, exist_ok=True)

    try:
        # 确定schema模式
        if config.is_predefined_mode():
            schema_mode = "predefined"
            schema_template = config.schema
        else:
            schema_mode = "auto"
            schema_template = None

        # 如果启用schema编辑，先生成schema，复制到当前目录让用户编辑
        if config.enable_schema_edit and config.is_auto_mode():
            logger.info("启用Schema编辑模式，将在当前目录生成schema文件供编辑")

            # 步骤1: 先生成schema（不启用编辑）
            agent = ParserAgent(output_dir=str(output_path))
            from web2json.agent.planner import AgentPlanner
            planner = AgentPlanner()
            plan = planner.create_plan(html_files, iteration_rounds=config.iteration_rounds)

            # 执行schema生成
            schema_result = agent.executor.schema_phase.execute(plan['sample_urls'])
            if not schema_result.get('success', False):
                raise Exception(f"Schema生成失败: {schema_result.get('error', '未知错误')}")

            # 步骤2: 将schema复制到当前目录
            schema_file = Path(schema_result.get('final_schema_path'))
            current_dir_schema = Path.cwd() / "schema_for_edit.json"
            shutil.copy2(schema_file, current_dir_schema)

            # 步骤3: 等待用户编辑
            logger.info("="*70)
            logger.info(f"Schema文件已生成: {current_dir_schema}")
            logger.info("")
            logger.info("请按以下步骤操作:")
            logger.info(f"  1. 打开文件进行编辑: {current_dir_schema}")
            logger.info("  2. 编辑完成后保存文件")
            logger.info("  3. 在此处按回车键继续...")
            logger.info("="*70)
            input()

            # 步骤4: 读取编辑后的schema
            with open(current_dir_schema, 'r', encoding='utf-8') as f:
                edited_schema = json.load(f)

            logger.info("✓ 已读取编辑后的Schema")
            logger.info(f"  Schema包含 {len(edited_schema)} 个字段")

            # 步骤5: 继续生成parser和解析数据（使用编辑后的schema）
            agent.executor.final_schema = edited_schema

            # 执行代码生成阶段
            code_result = agent.executor.code_phase.execute(
                final_schema=edited_schema,
                schema_phase_rounds=schema_result['rounds']
            )

            if not code_result.get('success', False):
                raise Exception(f"代码生成失败: {code_result.get('error', '未知错误')}")

            # 批量解析
            parser_path = code_result.get('final_parser', {}).get('parser_path')
            parse_result = agent.executor.parse_all_html_files(
                html_files=html_files,
                parser_path=parser_path
            )

            if not parse_result.get('success', False):
                raise Exception(f"批量解析失败: {parse_result.get('error', '未知错误')}")

            # 清理当前目录的schema文件
            if current_dir_schema.exists():
                os.remove(current_dir_schema)
                logger.info(f"✓ 已清理临时schema文件")

            # 构造result对象（模拟generate_parser的返回）
            result = {
                'success': True,
                'results_dir': parse_result.get('output_dir')
            }
            final_schema = edited_schema
        else:
            # 正常流程：直接调用generate_parser
            agent = ParserAgent(output_dir=str(output_path))
            result = agent.generate_parser(
                html_files=html_files,
                iteration_rounds=config.iteration_rounds,
                schema_mode=schema_mode,
                schema_template=schema_template,
                enable_schema_edit=False  # 不使用内置的编辑模式
            )

            if not result['success']:
                error_msg = result.get('error', '未知错误')
                raise Exception(f"执行失败: {error_msg}")

            # 读取final_schema
            schema_file = output_path / "schemas" / "final_schema.json"
            with open(schema_file, 'r', encoding='utf-8') as f:
                final_schema = json.load(f)

        # 读取生成的文件到内存
        # 读取parser代码
        parser_file = output_path / "parsers" / "final_parser.py"
        with open(parser_file, 'r', encoding='utf-8') as f:
            parser_code = f.read()

        # 3. 读取所有解析后的JSON数据
        results_dir = Path(result.get('results_dir'))
        parsed_data = []
        if results_dir.exists():
            for json_file in sorted(results_dir.glob("*.json")):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    parsed_data.append({
                        'filename': json_file.name.replace('.json', '.html'),
                        'data': data
                    })

        logger.info("✓ 执行成功")
        logger.info(f"  解析了 {len(parsed_data)} 个文件")
        logger.info(f"  Schema包含 {len(final_schema)} 个字段")

        # 返回内存数据对象
        return ExtractDataResult(
            final_schema=final_schema,
            parser_code=parser_code,
            parsed_data=parsed_data
        )

    finally:
        # 根据配置决定清理策略
        if use_temp_dir:
            # 临时目录：完全清理
            if output_path.exists():
                shutil.rmtree(output_path)
        else:
            # 持久目录：选择性清理，只保留save列表中的内容
            _cleanup_unwanted_files(output_path, config.save, api_type="extract_data")
            logger.info(f"✓ 结果已保存到: {output_path}")


def extract_schema(config: Web2JsonConfig) -> ExtractSchemaResult:
    """API 2: 从HTML提取Schema

    仅执行Schema学习阶段，不生成parser代码。
    支持人工编辑模式：当enable_schema_edit=True时，等待用户手动编辑schema。

    Args:
        config: Web2JsonConfig配置对象
            - enable_schema_edit: 是否启用人工编辑（默认False）

    Returns:
        ExtractSchemaResult: 包含final_schema和intermediate_schemas的结果对象

    Raises:
        Exception: 执行失败时抛出异常

    Example:
        >>> # 自动生成schema
        >>> config = Web2JsonConfig(
        ...     name="my_schema",
        ...     html_path="html_samples/",
        ...     iteration_rounds=3
        ... )
        >>> result = extract_schema(config)
        >>> print(result.final_schema)
        >>> print(f"经过了 {len(result.intermediate_schemas)} 轮迭代")

        >>> # 启用人工编辑
        >>> config = Web2JsonConfig(
        ...     name="my_schema_edit",
        ...     html_path="html_samples/",
        ...     enable_schema_edit=True
        ... )
        >>> result = extract_schema(config)
    """
    _setup_logger()

    logger.info(f"[API] extract_schema - 提取Schema")
    logger.info(f"  HTML路径: {config.html_path}")
    logger.info(f"  样本数: {config.iteration_rounds}")
    logger.info(f"  人工编辑: {'启用' if config.enable_schema_edit else '禁用'}")
    if config.should_save():
        logger.info(f"  保存内容: {', '.join(config.save)}")
        logger.info(f"  输出路径: {config.get_full_output_path()}")

    # 读取HTML文件
    html_files = _read_html_files(config.html_path)
    logger.info(f"找到 {len(html_files)} 个HTML文件")

    # 根据是否需要保存决定使用临时目录还是持久目录
    import tempfile
    import shutil
    import os

    use_temp_dir = not config.should_save()
    if use_temp_dir:
        temp_output_dir = tempfile.mkdtemp(prefix="web2json_schema_")
        output_path = Path(temp_output_dir)
    else:
        output_path = Path(config.get_full_output_path())
        output_path.mkdir(parents=True, exist_ok=True)

    try:
        # 创建Agent并只执行Schema学习阶段
        agent = ParserAgent(output_dir=str(output_path))

        # 手动执行Schema阶段
        from web2json.agent.planner import AgentPlanner
        planner = AgentPlanner()
        plan = planner.create_plan(html_files, iteration_rounds=config.iteration_rounds)

        # 只执行Schema迭代阶段
        schema_result = agent.executor.schema_phase.execute(plan['sample_urls'])

        if not schema_result.get('success', False):
            error_msg = schema_result.get('error', '未知错误')
            raise Exception(f"Schema生成失败: {error_msg}")

        schema_path = schema_result.get('final_schema_path')

        # 读取最终schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            final_schema = json.load(f)

        # 如果启用人工编辑模式，将schema复制到当前目录让用户编辑
        if config.enable_schema_edit:
            # 将schema复制到当前目录
            current_dir_schema = Path.cwd() / "schema_for_edit.json"
            with open(current_dir_schema, 'w', encoding='utf-8') as f:
                json.dump(final_schema, f, indent=2, ensure_ascii=False)

            # 等待用户编辑
            logger.info("="*70)
            logger.info(f"Schema文件已生成: {current_dir_schema}")
            logger.info("")
            logger.info("请按以下步骤操作:")
            logger.info(f"  1. 打开文件进行编辑: {current_dir_schema}")
            logger.info("  2. 编辑完成后保存文件")
            logger.info("  3. 在此处按回车键继续...")
            logger.info("="*70)
            input()

            # 读取编辑后的schema
            with open(current_dir_schema, 'r', encoding='utf-8') as f:
                edited_schema = json.load(f)

            # 显示变化（简单对比）
            original_fields = set(final_schema.keys())
            edited_fields = set(edited_schema.keys())
            added_fields = edited_fields - original_fields
            removed_fields = original_fields - edited_fields

            if added_fields or removed_fields:
                logger.info("\n✓ Schema已修改:")
                if added_fields:
                    logger.info(f"  新增字段: {', '.join(added_fields)}")
                if removed_fields:
                    logger.info(f"  删除字段: {', '.join(removed_fields)}")
            else:
                logger.info("\n✓ 已读取编辑后的Schema（字段数量未变）")

            logger.info(f"  最终Schema包含 {len(edited_schema)} 个字段")

            # 更新为编辑后的schema
            final_schema = edited_schema

            # 清理当前目录的schema文件
            if current_dir_schema.exists():
                os.remove(current_dir_schema)
                logger.info(f"✓ 已清理临时schema文件")

        # 读取所有中间schema
        intermediate_schemas = []
        schemas_dir = output_path / "schemas"
        if schemas_dir.exists():
            for schema_file in sorted(schemas_dir.glob("merged_schema_round_*.json")):
                with open(schema_file, 'r', encoding='utf-8') as f:
                    intermediate_schemas.append(json.load(f))

        logger.info("✓ Schema提取成功")
        logger.info(f"  Schema包含 {len(final_schema)} 个字段")
        logger.info(f"  经过 {len(intermediate_schemas)} 轮迭代")

        return ExtractSchemaResult(
            final_schema=final_schema,
            intermediate_schemas=intermediate_schemas
        )

    finally:
        # 根据配置决定清理策略
        if use_temp_dir:
            # 临时目录：完全清理
            if output_path.exists():
                shutil.rmtree(output_path)
        else:
            # 持久目录：选择性清理，只保留save列表中的内容
            _cleanup_unwanted_files(output_path, config.save, api_type="extract_schema")
            logger.info(f"✓ 结果已保存到: {output_path}")


def infer_code(config: Web2JsonConfig) -> InferCodeResult:
    """API 3: 根据Schema生成Parser代码

    支持两种模式：
    1. Predefined模式：提供schema，直接基于schema生成parser代码
    2. Auto模式：不提供schema，自动从HTML学习schema后生成parser代码

    适用场景：
    - 已经有了schema（通过extract_schema获得或手动编写），需要生成parser代码
    - 没有schema，需要从HTML自动学习schema并生成parser代码

    Args:
        config: Web2JsonConfig配置对象
            - html_path: 必填，HTML文件目录或单个HTML文件路径
            - schema: 可选，Schema字典（None时为auto模式，自动学习）
            - iteration_rounds: 可选，迭代轮数（auto模式时使用，默认3）
            - name: 可选，运行名称（默认值会被忽略）
            - output_path: 可选，输出路径（默认值会被忽略）

    Returns:
        InferCodeResult: 包含parser_code和schema的结果对象

    Raises:
        Exception: 执行失败时抛出异常

    Example:
        >>> # Predefined模式：使用已有的schema
        >>> config = Web2JsonConfig(
        ...     name="my_code",
        ...     html_path="html_samples/",
        ...     schema={"title": "string", "author": "string"}
        ... )
        >>> code_result = infer_code(config)

        >>> # Auto模式：自动学习schema
        >>> config = Web2JsonConfig(
        ...     name="auto_code",
        ...     html_path="html_samples/",
        ...     iteration_rounds=3
        ... )
        >>> code_result = infer_code(config)
        >>> print(f"自动学习的Schema: {code_result.schema}")
    """
    _setup_logger()

    logger.info(f"[API] infer_code - 生成Parser代码")
    logger.info(f"  HTML路径: {config.html_path}")

    # 判断是 predefined 模式还是 auto 模式
    if config.schema:
        logger.info(f"  模式: Predefined（使用提供的Schema）")
        logger.info(f"  Schema字段数: {len(config.schema)}")
    else:
        logger.info(f"  模式: Auto（自动学习Schema）")
        logger.info(f"  迭代轮数: {config.iteration_rounds}")

    if config.should_save():
        logger.info(f"  保存内容: {', '.join(config.save)}")
        logger.info(f"  输出路径: {config.get_full_output_path()}")

    # 处理HTML路径（可能是目录或单个文件）
    html_file_path = Path(config.html_path)
    if html_file_path.is_dir():
        html_files = _read_html_files(config.html_path)
    elif html_file_path.is_file():
        html_files = [str(html_file_path.absolute())]
    else:
        raise FileNotFoundError(f"HTML路径不存在: {config.html_path}")

    logger.info(f"找到 {len(html_files)} 个HTML文件")

    # 根据是否需要保存决定使用临时目录还是持久目录
    import tempfile
    import shutil

    use_temp_dir = not config.should_save()
    if use_temp_dir:
        temp_output_dir = tempfile.mkdtemp(prefix="web2json_code_")
        output_dir = Path(temp_output_dir)
    else:
        output_dir = Path(config.get_full_output_path())
        output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 创建Agent
        agent = ParserAgent(output_dir=str(output_dir))

        # 创建执行计划
        from web2json.agent.planner import AgentPlanner
        planner = AgentPlanner()

        # 根据是否提供schema选择不同的模式
        if config.schema:
            # Predefined模式：使用提供的schema
            agent.executor.schema_mode = "predefined"
            agent.executor.schema_template = config.schema
            agent.executor.schema_processor.schema_mode = "predefined"
            agent.executor.schema_processor.schema_template = config.schema
            agent.executor.schema_phase.schema_mode = "predefined"

            plan = planner.create_plan(html_files, iteration_rounds=min(len(html_files), 3))

            logger.info(f"使用提供的Schema（跳过Schema提取，仅处理HTML）")

            # 运行Schema阶段以处理HTML并构建rounds数据结构
            schema_result = agent.executor.schema_phase.execute(plan['sample_urls'])

            if not schema_result.get('success', False):
                error_msg = schema_result.get('error', '未知错误')
                raise Exception(f"HTML处理失败: {error_msg}")

            # 用提供的schema替换自动生成的schema
            agent.executor.final_schema = config.schema
            final_schema = config.schema

        else:
            # Auto模式：自动学习schema
            agent.executor.schema_mode = "auto"
            agent.executor.schema_processor.schema_mode = "auto"
            agent.executor.schema_phase.schema_mode = "auto"

            plan = planner.create_plan(html_files, iteration_rounds=config.iteration_rounds)

            logger.info(f"自动学习Schema（使用{config.iteration_rounds}个样本）")

            # 运行Schema阶段，自动生成schema
            schema_result = agent.executor.schema_phase.execute(plan['sample_urls'])

            if not schema_result.get('success', False):
                error_msg = schema_result.get('error', '未知错误')
                raise Exception(f"Schema学习失败: {error_msg}")

            # 读取自动生成的schema
            schema_path = schema_result.get('final_schema_path')
            with open(schema_path, 'r', encoding='utf-8') as f:
                import json
                final_schema = json.load(f)

            agent.executor.final_schema = final_schema
            logger.info(f"✓ Schema学习完成，包含 {len(final_schema)} 个字段")

        logger.info(f"开始生成Parser代码...")

        # 执行代码生成阶段
        code_result = agent.executor.code_phase.execute(
            final_schema=final_schema,
            schema_phase_rounds=schema_result['rounds']
        )

        if not code_result.get('success', False):
            error_msg = code_result.get('error', '未知错误')
            raise Exception(f"代码生成失败: {error_msg}")

        parser_path = code_result.get('final_parser', {}).get('parser_path')
        if not parser_path:
            raise Exception("未能获取到parser路径")

        # 读取parser代码到内存
        with open(parser_path, 'r', encoding='utf-8') as f:
            parser_code = f.read()

        logger.info("✓ Parser代码生成成功")
        logger.info(f"  代码长度: {len(parser_code)} 字符")

        return InferCodeResult(
            parser_code=parser_code,
            schema=final_schema
        )

    finally:
        # 根据配置决定清理策略
        if use_temp_dir:
            # 临时目录：完全清理
            if output_dir.exists():
                shutil.rmtree(output_dir)
        else:
            # 持久目录：选择性清理，只保留save列表中的内容
            _cleanup_unwanted_files(output_dir, config.save, api_type="infer_code")
            logger.info(f"✓ 结果已保存到: {output_dir}")


def extract_data_with_code(config: Web2JsonConfig) -> ParseResult:
    """API 4: 使用Parser代码解析HTML文件

    使用提供的parser代码来解析HTML文件。
    适用场景：
    - 已经有了parser代码（通过infer_code获得或手动编写）
    - 需要解析新的、结构相同的HTML文件

    Args:
        config: Web2JsonConfig配置对象
            - parser_code: 必填，Parser代码文件路径（.py文件）或代码字符串
            - html_path: 必填，HTML文件目录或单个HTML文件路径
            - name: 可选，运行名称（默认值会被忽略）
            - output_path: 可选，输出路径（默认值会被忽略）
            - iteration_rounds: 可选，迭代轮数（默认值会被忽略）
            - schema: 可选，Schema（默认值会被忽略）

    Returns:
        ParseResult: 包含parsed_data列表的结果对象

    Raises:
        Exception: 执行失败时抛出异常
        ValueError: parser_code未提供时抛出异常
        FileNotFoundError: HTML文件或parser文件不存在

    Example:
        >>> # 使用 .py 文件路径
        >>> parse_config = Web2JsonConfig(
        ...     name="parse_demo",
        ...     html_path="new_html_samples/",
        ...     parser_code="output/blog/parsers/final_parser.py"
        ... )
        >>> parse_result = extract_data_with_code(parse_config)
        >>> for item in parse_result.parsed_data[:2]:
        ...     print(f"文件: {item['filename']}")
        ...     print(f"数据: {item['data']}")
    """
    _setup_logger()

    # 验证必填参数
    if not config.parser_code:
        raise ValueError("extract_data_with_code 需要提供 parser_code 参数")

    # 检测 parser_code 是文件路径还是代码字符串
    parser_code_content = config.parser_code
    parser_code_path = Path(config.parser_code)

    # 判断是否可能是文件路径（包含 .py 扩展名或路径分隔符）
    looks_like_path = '.py' in config.parser_code or '/' in config.parser_code or '\\' in config.parser_code

    if looks_like_path:
        # 如果看起来像文件路径，检查文件是否存在
        if parser_code_path.exists() and parser_code_path.is_file():
            # 文件存在，读取内容
            logger.info(f"[API] extract_data_with_code - 使用代码解析")
            logger.info(f"  Parser文件: {config.parser_code}")
            try:
                with open(parser_code_path, 'r', encoding='utf-8') as f:
                    parser_code_content = f.read()
                logger.info(f"  ✓ Parser代码已加载（{len(parser_code_content)} 字符）")
            except Exception as e:
                raise Exception(f"读取Parser文件失败: {str(e)}")
        else:
            # 文件不存在
            raise FileNotFoundError(
                f"Parser文件不存在: {config.parser_code}\n"
                f"请确认文件路径是否正确，或者传入 Python 代码字符串。"
            )
    else:
        # 当作代码字符串处理
        logger.info(f"[API] extract_data_with_code - 使用代码解析")
        logger.info(f"  Parser代码长度: {len(parser_code_content)} 字符")

    logger.info(f"  HTML路径: {config.html_path}")
    if config.should_save():
        logger.info(f"  保存内容: {', '.join(config.save)}")
        logger.info(f"  输出路径: {config.get_full_output_path()}")

    # 处理HTML路径（可能是目录或单个文件）
    html_file_path = Path(config.html_path)
    if html_file_path.is_dir():
        html_files = _read_html_files(config.html_path)
    elif html_file_path.is_file():
        html_files = [str(html_file_path.absolute())]
    else:
        raise FileNotFoundError(f"HTML路径不存在: {config.html_path}")

    logger.info(f"找到 {len(html_files)} 个HTML文件")

    # 根据是否需要保存决定使用临时目录还是持久目录
    import tempfile
    import shutil

    use_temp_dir = not config.should_save()
    if use_temp_dir:
        temp_output_dir = tempfile.mkdtemp(prefix="web2json_parse_")
        output_dir = Path(temp_output_dir)
    else:
        output_dir = Path(config.get_full_output_path())
        output_dir.mkdir(parents=True, exist_ok=True)

    # 创建临时parser文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp_parser:
        tmp_parser.write(parser_code_content)
        temp_parser_path = tmp_parser.name

    try:
        # 创建Agent并执行批量解析
        agent = ParserAgent(output_dir=str(output_dir))

        # 直接调用批量解析方法
        parse_result = agent.executor.parse_all_html_files(
            html_files=html_files,
            parser_path=temp_parser_path
        )

        if not parse_result.get('success', False):
            error_msg = parse_result.get('error', '未知错误')
            raise Exception(f"批量解析失败: {error_msg}")

        # 读取所有解析后的JSON数据到内存
        results_dir = Path(parse_result.get('output_dir'))
        parsed_data = []
        if results_dir.exists():
            for json_file in sorted(results_dir.glob("*.json")):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    parsed_data.append({
                        'filename': json_file.name.replace('.json', '.html'),
                        'data': data
                    })

        success_count = len(parse_result.get('parsed_files', []))
        failed_count = len(parse_result.get('failed_files', []))

        logger.info("✓ 解析成功")
        logger.info(f"  成功: {success_count} 个文件")
        logger.info(f"  失败: {failed_count} 个文件")

        return ParseResult(
            parsed_data=parsed_data,
            success_count=success_count,
            failed_count=failed_count
        )

    finally:
        # 清理临时parser文件
        import os
        if os.path.exists(temp_parser_path):
            os.unlink(temp_parser_path)

        # 根据配置决定清理策略
        if use_temp_dir:
            # 临时目录：完全清理
            if output_dir.exists():
                shutil.rmtree(output_dir)
        else:
            # 持久目录：选择性清理，只保留save列表中的内容
            _cleanup_unwanted_files(output_dir, config.save, api_type="extract_data_with_code")
            logger.info(f"✓ 结果已保存到: {output_dir}")


def classify_html_dir(config: Web2JsonConfig) -> ClusterResult:
    """API 5: 对HTML目录进行布局分类

    根据HTML页面的布局相似度进行聚类分析，将相似布局的页面分组。
    适用场景：
    - 混合了多种页面布局的HTML文件集合（如列表页、详情页混在一起）
    - 需要先了解HTML文件的布局分布情况
    - 需要将不同布局的页面分开处理

    Args:
        config: Web2JsonConfig配置对象
            - html_path: 必填，HTML文件目录路径
            - name: 可选，运行名称（默认值会被忽略）
            - output_path: 可选，输出路径（默认值会被忽略）
            - iteration_rounds: 可选，迭代轮数（默认值会被忽略）
            - schema: 可选，Schema（默认值会被忽略）
            - parser_code: 可选，Parser代码（默认值会被忽略）

    Returns:
        ClusterResult: 包含clusters、labels、noise_files的结果对象

    Raises:
        Exception: 执行失败时抛出异常

    Example:
        >>> config = Web2JsonConfig(
        ...     name="classify_demo",
        ...     html_path="mixed_html/"
        ... )
        >>> result = classify_html_dir(config)
        >>> print(result.get_summary())
        >>> print(f"簇0包含: {len(result.clusters['cluster_0'])} 个文件")
        >>> for cluster_name, files in result.clusters.items():
        ...     print(f"{cluster_name}: {files[:3]}")
    """
    _setup_logger()

    logger.info(f"[API] classify_html_dir - HTML布局分类")
    logger.info(f"  HTML路径: {config.html_path}")
    if config.should_save():
        logger.info(f"  保存内容: {', '.join(config.save)}")
        logger.info(f"  输出路径: {config.get_full_output_path()}")

    # 读取HTML文件
    html_files = _read_html_files(config.html_path)
    logger.info(f"找到 {len(html_files)} 个HTML文件")

    # 读取所有HTML内容
    logger.info("正在读取HTML内容...")
    html_contents = []
    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_contents.append(f.read())
        except Exception as e:
            raise Exception(f"读取文件失败 {file_path}: {e}")

    # 执行聚类分析
    logger.info("正在进行布局聚类分析...")
    from web2json.tools.cluster import cluster_html_layouts_optimized

    try:
        labels, sim_mat, clusters = cluster_html_layouts_optimized(
            html_contents,
            use_knn_graph=True
        )
    except Exception as e:
        raise Exception(f"聚类失败: {e}")

    # 统计聚类结果
    unique_labels = sorted(set(labels))
    noise_count = sum(1 for l in labels if l == -1)
    cluster_count = len([l for l in unique_labels if l != -1])

    logger.info("✓ 聚类分析完成")
    logger.info(f"  总文件数: {len(html_files)}")
    logger.info(f"  识别出的布局簇数: {cluster_count}")
    logger.info(f"  噪声点（未归类）: {noise_count}")

    # 构建聚类结果
    clusters_dict = {}
    noise_files = []

    for lbl in unique_labels:
        cluster_files = [p for p, l in zip(html_files, labels) if l == lbl]
        if not cluster_files:
            continue

        if lbl == -1:
            noise_files = cluster_files
        else:
            clusters_dict[f"cluster_{lbl}"] = cluster_files

        logger.info(f"  {'噪声点' if lbl == -1 else f'簇 {lbl}'}: {len(cluster_files)} 个文件")

    logger.info("✓ 分类完成")

    # 如果需要保存，写入文件
    if config.should_save():
        import shutil
        output_path = Path(config.get_full_output_path())
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存报告
        if config.should_save_item('report'):
            # 保存JSON格式的报告
            report_json = output_path / 'cluster_report.json'
            with open(report_json, 'w', encoding='utf-8') as f:
                json.dump({
                    'clusters': clusters_dict,
                    'labels': labels,
                    'noise_files': noise_files,
                    'cluster_count': cluster_count,
                    'total_files': len(html_files)
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"  ✓ 报告已保存: {report_json}")

            # 保存文本格式的摘要
            info_txt = output_path / 'cluster_info.txt'
            with open(info_txt, 'w', encoding='utf-8') as f:
                f.write(f"HTML布局聚类分析结果\n")
                f.write(f"{'='*70}\n\n")
                f.write(f"总文件数: {len(html_files)}\n")
                f.write(f"识别出的布局簇数: {cluster_count}\n")
                f.write(f"噪声点（未归类）: {noise_count}\n\n")
                for lbl in sorted(set(labels)):
                    cluster_files = [p for p, l in zip(html_files, labels) if l == lbl]
                    if lbl == -1:
                        f.write(f"噪声点: {len(cluster_files)} 个文件\n")
                    else:
                        f.write(f"簇 {lbl}: {len(cluster_files)} 个文件\n")
                    for file_path in cluster_files[:5]:
                        f.write(f"  - {Path(file_path).name}\n")
                    if len(cluster_files) > 5:
                        f.write(f"  ... 还有 {len(cluster_files)-5} 个文件\n")
                    f.write("\n")
            logger.info(f"  ✓ 摘要已保存: {info_txt}")

        # 复制文件到聚类目录
        if config.should_save_item('files'):
            clusters_dir = output_path / 'clusters'
            clusters_dir.mkdir(exist_ok=True)

            for lbl in sorted(set(labels)):
                cluster_files = [p for p, l in zip(html_files, labels) if l == lbl]
                if not cluster_files:
                    continue

                if lbl == -1:
                    cluster_subdir = clusters_dir / 'noise'
                else:
                    cluster_subdir = clusters_dir / f'cluster_{lbl}'

                cluster_subdir.mkdir(exist_ok=True)

                for src_file in cluster_files:
                    src = Path(src_file)
                    dst = cluster_subdir / src.name
                    shutil.copy2(src, dst)

            logger.info(f"  ✓ 文件已复制到: {clusters_dir}")

        logger.info(f"✓ 结果已保存到: {output_path}")

    return ClusterResult(
        clusters=clusters_dict,
        labels=labels,
        noise_files=noise_files,
        cluster_count=cluster_count
    )

