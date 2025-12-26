"""
Agent 编排器
整合规划器和执行器，提供统一的Agent接口
"""
import json
from typing import List, Dict, Optional
from pathlib import Path
from loguru import logger
from .planner import AgentPlanner
from .executor import AgentExecutor
from web2json.config.settings import settings


class ParserAgent:
    """
    HTML解析器生成Agent

    通过给定一组HTML文件，自动生成能够解析这些页面的Python代码
    """

    def __init__(self, output_dir: str = "output", schema_mode: str = None, schema_template: Dict = None):
        """
        初始化Agent

        Args:
            output_dir: 输出目录
            schema_mode: Schema模式 (auto: 自动提取, predefined: 使用预定义模板)
            schema_template: 预定义的Schema模板（当schema_mode=predefined时使用）
        """
        self.planner = AgentPlanner()
        self.schema_mode = schema_mode or settings.schema_mode
        self.schema_template = schema_template
        self.executor = AgentExecutor(
            output_dir=output_dir,
            schema_mode=self.schema_mode,
            schema_template=self.schema_template
        )
        self.output_dir = Path(output_dir)


    def generate_parser(
        self,
        html_files: List[str],
        domain: str = None,
        iteration_rounds: int = None,
        schema_mode: str = None,
        schema_template: str = None
    ) -> Dict:
        """
        生成解析器

        流程：
        1. 规划：分析HTML文件并制定执行计划
        2. 执行：
           - 阶段1: Schema迭代 - 提取并优化Schema（或使用预定义Schema补充xpath）
           - 阶段2: 代码迭代 - 生成并优化解析代码
        3. 批量解析：使用生成的解析器解析所有HTML文件
        4. 总结：生成执行总结

        Args:
            html_files: HTML文件路径列表
            domain: 域名（可选）
            iteration_rounds: 迭代轮数（用于Schema学习的样本数量），默认为3
            schema_mode: Schema模式 (auto/predefined)，覆盖初始化时的设置
            schema_template: 预定义schema模板文件路径（JSON格式）

        Returns:
            生成结果
        """
        # 如果提供了schema_mode参数，更新模式
        if schema_mode:
            self.schema_mode = schema_mode
            self.executor.schema_mode = schema_mode

        # 如果是预定义模式，加载schema模板
        if self.schema_mode == "predefined":
            if schema_template:
                # 支持两种类型：字典对象或文件路径字符串
                if isinstance(schema_template, dict):
                    # 直接使用字典对象（来自交互式输入）
                    logger.info(f"使用交互式输入的Schema模板")
                    self.schema_template = schema_template
                    self.executor.schema_template = self.schema_template
                    logger.info(f"Schema模板包含字段: {list(self.schema_template.keys())}")
                else:
                    # 从文件加载schema模板
                    template_path = Path(schema_template)
                    if not template_path.exists():
                        raise FileNotFoundError(f"Schema模板文件不存在: {schema_template}")

                    logger.info(f"加载预定义Schema模板: {schema_template}")
                    with open(template_path, 'r', encoding='utf-8') as f:
                        self.schema_template = json.load(f)
                    self.executor.schema_template = self.schema_template
                    logger.info(f"Schema模板加载成功，包含字段: {list(self.schema_template.keys())}")

            if not self.schema_template:
                raise ValueError("预定义模式需要提供schema_template参数")

        logger.info(f"Schema模式: {self.schema_mode}")
        logger.info("="*70)

        # 第一步：规划
        logger.info("\n[步骤 1/4] 任务规划")
        plan = self.planner.create_plan(html_files, domain, iteration_rounds)

        # 第二步：执行（两阶段迭代）
        logger.info("\n[步骤 2/4] 执行计划 - 两阶段迭代")
        execution_result = self.executor.execute_plan(plan)

        if not execution_result['success']:
            logger.error("执行失败，无法生成解析器")
            return {
                'success': False,
                'error': '执行失败',
                'execution_result': execution_result
            }

        # 第三步：批量解析所有HTML文件
        logger.info("\n[步骤 3/4] 批量解析所有HTML文件")
        parser_path = execution_result['final_parser']['parser_path']
        all_html_files = plan['all_html_files']

        parse_result = self.executor.parse_all_html_files(
            html_files=all_html_files,
            parser_path=parser_path
        )

        # 第四步：总结
        logger.info("\n[步骤 4/4] 生成总结")
        summary = self._generate_summary(execution_result, parse_result)

        return {
            'success': True,
            'plan': plan,
            'execution_result': execution_result,
            'parse_result': parse_result,
            'summary': summary,
            'parser_path': execution_result['final_parser']['parser_path'],
            'config_path': execution_result['final_parser'].get('config_path'),
            'results_dir': parse_result.get('output_dir'),
        }

    def _generate_summary(self, execution_result: Dict, parse_result: Dict = None) -> str:
        """生成执行总结"""
        lines = []
        lines.append("\n" + "="*70)
        lines.append("执行总结")
        lines.append("="*70)

        # Schema迭代阶段结果
        schema_phase = execution_result.get('schema_phase', {})
        schema_rounds = schema_phase.get('rounds', [])
        schema_success_rounds = [r for r in schema_rounds if r.get('success')]
        lines.append(f"\nSchema迭代阶段: {len(schema_success_rounds)}/{len(schema_rounds)} 轮成功")

        if schema_phase.get('final_schema'):
            final_schema_size = len(schema_phase['final_schema'])
            lines.append(f"  最终Schema字段数: {final_schema_size}")

        if schema_phase.get('final_schema_path'):
            lines.append(f"  最终Schema路径: {schema_phase['final_schema_path']}")

        # 代码迭代阶段结果
        code_phase = execution_result.get('code_phase', {})
        code_rounds = code_phase.get('rounds', [])
        code_success_rounds = [r for r in code_rounds if r.get('success')]
        lines.append(f"\n代码迭代阶段: {len(code_success_rounds)}/{len(code_rounds)} 轮成功")

        # 解析器生成结果
        if execution_result.get('final_parser'):
            parser_path = execution_result['final_parser']['parser_path']

        # 批量解析结果
        if parse_result:
            lines.append(f"\n批量解析阶段:")
            lines.append(f"  成功解析: {len(parse_result.get('parsed_files', []))}/{parse_result.get('total_files', 0)} 个文件")
            if parse_result.get('failed_files'):
                lines.append(f"  失败: {len(parse_result['failed_files'])} 个文件")
            lines.append(f"  结果保存目录: {parse_result.get('output_dir', '')}")

        lines.append("="*70)

        summary = "\n".join(lines)
        logger.info(summary)

        return summary

