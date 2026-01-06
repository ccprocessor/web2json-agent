"""
Agent 执行器
负责阶段编排和流程控制
"""
from pathlib import Path
from typing import Dict, List

from loguru import logger

from .processors import (
    HtmlProcessor,
    SchemaProcessor,
    CodeProcessor,
    ParserProcessor,
)
from .phases import SchemaPhase, CodePhase


class AgentExecutor:
    """Agent 执行器 - 负责阶段编排"""

    def __init__(self, output_dir: str = "output", schema_mode: str = "auto", schema_template: Dict = None, progress_callback=None):
        """
        初始化执行器

        Args:
            output_dir: 输出目录
            schema_mode: Schema模式 (auto: 自动提取, predefined: 使用预定义模板)
            schema_template: 预定义的Schema模板（当schema_mode=predefined时使用）
            progress_callback: 进度回调函数 callback(phase, step, percentage)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.schema_mode = schema_mode
        self.schema_template = schema_template
        self.progress_callback = progress_callback

        # 创建子目录
        self._setup_directories()

        # 初始化处理器
        self._init_processors()

        # 初始化阶段管理器
        self._init_phases()

        # 验证预定义模式
        if self.schema_mode == "predefined":
            if not self.schema_template:
                raise ValueError("预定义模式需要提供schema_template")
            logger.info(f"  - 预定义Schema字段: {list(self.schema_template.keys())}")

    def _setup_directories(self):
        """创建输出子目录"""
        self.parsers_dir = self.output_dir / "parsers"
        self.html_original_dir = self.output_dir / "html_original"
        self.html_simplified_dir = self.output_dir / "html_simplified"
        self.result_dir = self.output_dir / "result"
        self.schemas_dir = self.output_dir / "schemas"

        for dir_path in [
            self.parsers_dir,
            self.html_original_dir,
            self.html_simplified_dir,
            self.result_dir,
            self.schemas_dir,
        ]:
            dir_path.mkdir(exist_ok=True)

    def _init_processors(self):
        """初始化所有处理器"""
        self.html_processor = HtmlProcessor(
            html_original_dir=self.html_original_dir,
            html_simplified_dir=self.html_simplified_dir,
        )

        self.schema_processor = SchemaProcessor(
            schemas_dir=self.schemas_dir,
            schema_mode=self.schema_mode,
            schema_template=self.schema_template,
        )

        self.code_processor = CodeProcessor(
            parsers_dir=self.parsers_dir,
        )

        self.parser_processor = ParserProcessor(
            result_dir=self.result_dir,
        )

    def _init_phases(self):
        """初始化阶段管理器"""
        self.schema_phase = SchemaPhase(
            html_processor=self.html_processor,
            schema_processor=self.schema_processor,
            schema_mode=self.schema_mode,
            progress_callback=self.progress_callback,
        )

        self.code_phase = CodePhase(
            code_processor=self.code_processor,
            output_dir=self.output_dir,
            progress_callback=self.progress_callback,
        )

    def execute_plan(self, plan: Dict) -> Dict:
        """
        执行计划 - 两阶段迭代

        阶段1: Schema迭代（前N个URL）- 获取HTML -> 提取/优化JSON Schema
        阶段2: 代码迭代（前N个URL）- 基于最终Schema生成代码 -> 验证 -> 优化代码

        Args:
            plan: 执行计划

        Returns:
            执行结果
        """
        logger.info("开始执行计划...")

        results = {
            'plan': plan,
            'schema_phase': {},
            'code_phase': {},
            'final_parser': None,
            'success': False,
        }

        sample_urls = plan['sample_urls']

        # ============ 阶段 1: Schema 迭代 ============
        schema_result = self.schema_phase.execute(sample_urls)
        results['schema_phase'] = schema_result

        if not schema_result['success']:
            logger.error("Schema阶段失败")
            return results

        final_schema = schema_result['final_schema']
        logger.success(f"Schema阶段完成，最终Schema包含 {len(final_schema)} 个字段")

        # ============ 阶段 2: 代码迭代 ============
        code_result = self.code_phase.execute(
            final_schema=final_schema,
            schema_phase_rounds=schema_result['rounds']
        )
        results['code_phase'] = code_result

        if code_result['success']:
            results['final_parser'] = code_result['final_parser']
            results['success'] = True
        else:
            logger.error("代码迭代阶段失败")

        return results

    def parse_all_html_files(self, html_files: List[str], parser_path: str) -> Dict:
        """
        使用生成的解析器批量解析所有HTML文件

        Args:
            html_files: 所有HTML文件路径列表
            parser_path: 解析器文件路径

        Returns:
            批量解析结果
        """
        return self.parser_processor.process({
            'html_files': html_files,
            'parser_path': parser_path,
        })
