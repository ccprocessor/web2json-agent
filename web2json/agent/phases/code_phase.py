"""
代码迭代阶段管理器
负责协调解析器代码的生成和优化流程
"""
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from web2json.agent.processors import CodeProcessor

from .base_phase import BasePhase


class CodePhase(BasePhase):
    """代码迭代阶段管理器"""

    def __init__(self, code_processor: CodeProcessor, output_dir: Path):
        """
        初始化代码阶段管理器

        Args:
            code_processor: 代码处理器
            output_dir: 输出目录
        """
        self.code_processor = code_processor
        self.output_dir = output_dir

    def execute(
        self,
        final_schema: Dict,
        schema_phase_rounds: List[Dict]
    ) -> Dict[str, Any]:
        """
        执行代码迭代阶段

        复用 Schema 阶段的 HTML，不重复获取网页
        第一轮：基于最终 Schema 生成初始解析代码
        后续轮：基于验证结果优化代码

        Args:
            final_schema: 来自 Schema 迭代阶段的最终 Schema
            schema_phase_rounds: Schema 阶段的轮次数据（包含 HTML）

        Returns:
            {
                'success': bool,
                'rounds': List[Dict],      # 每轮的详细结果
                'parsers': List[Dict],     # 所有生成的解析器
                'final_parser': Dict,      # 最终解析器
            }
        """
        result = {
            'rounds': [],
            'parsers': [],
            'final_parser': None,
            'success': False,
        }

        # 确保有可用的 Schema 阶段数据
        if not schema_phase_rounds:
            logger.error("Schema阶段没有可用的数据")
            return result

        logger.info(f"\n{'='*70}")
        logger.info(f"阶段2: 代码迭代（使用Schema阶段的{len(schema_phase_rounds)}个HTML，{len(schema_phase_rounds)}轮迭代）")
        logger.info(f"{'='*70}")

        current_parser_code = None
        current_parser_path = None

        # 使用 Schema 阶段的轮次数据
        for idx, schema_round in enumerate(schema_phase_rounds, 1):
            if not schema_round.get('success'):
                logger.warning(f"Schema阶段第 {idx} 轮失败，跳过代码生成")
                continue

            logger.info(f"\n{'─'*70}")
            logger.info(f"代码迭代 - 第 {idx}/{len(schema_phase_rounds)} 轮")
            logger.info(f"{'─'*70}")

            try:
                # 复用 Schema 阶段的 HTML（精简后的）
                html_path = schema_round.get('html_path')
                if not html_path:
                    logger.error(f"  ✗ Schema阶段第 {idx} 轮缺少HTML路径")
                    continue

                logger.info(f"  [1/2] 复用Schema阶段的精简HTML")
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                logger.success(f"  ✓ 精简HTML已加载（长度: {len(html_content)} 字符）")

                # 生成或优化解析代码
                code_result = self.code_processor.process({
                    'html_content': html_content,
                    'target_json': final_schema,
                    'idx': idx,
                    'previous_parser_code': current_parser_code,
                    'previous_parser_path': current_parser_path,
                })

                if not code_result['success']:
                    logger.error(f"  ✗ 代码生成失败")
                    if idx == 1:
                        return result
                    continue

                # 更新当前解析器
                current_parser_code = code_result['code']
                current_parser_path = code_result['parser_path']

                # 记录本轮结果（复用 Schema 阶段的数据）
                round_result = {
                    'round': idx,
                    'url': schema_round['url'],
                    'html_path': html_path,
                    'groundtruth_schema': schema_round.get('groundtruth_schema'),
                    'parser_path': current_parser_path,
                    'parser_code': current_parser_code,
                    'parser_result': code_result,
                    'success': True,
                }
                result['rounds'].append(round_result)
                result['parsers'].append(code_result)
                logger.success(f"代码迭代第 {idx} 轮完成")

            except Exception as e:
                logger.error(f"代码迭代第 {idx} 轮失败: {str(e)}")
                import traceback
                logger.debug(traceback.format_exc())

                round_result = {
                    'round': idx,
                    'url': schema_round.get('url'),
                    'error': str(e),
                    'success': False,
                }
                result['rounds'].append(round_result)

                if idx == 1:
                    # 第一轮失败则退出
                    return result

        # 设置最终解析器
        if current_parser_code:
            final_parser = self.code_processor.save_final_parser(
                code=current_parser_code,
                output_dir=self.output_dir,
                config=final_schema
            )
            result['final_parser'] = final_parser
            result['success'] = True

        return result
