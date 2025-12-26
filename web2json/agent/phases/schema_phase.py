"""
Schema 迭代阶段管理器
负责协调 HTML 处理和 Schema 提取/补充的完整流程
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from web2json.config.settings import settings
from web2json.agent.processors import HtmlProcessor, SchemaProcessor

from .base_phase import BasePhase


class SchemaPhase(BasePhase):
    """Schema 迭代阶段管理器"""

    def __init__(
        self,
        html_processor: HtmlProcessor,
        schema_processor: SchemaProcessor,
        schema_mode: str = 'auto'
    ):
        """
        初始化 Schema 阶段管理器

        Args:
            html_processor: HTML 处理器
            schema_processor: Schema 处理器
            schema_mode: Schema 模式 (auto/predefined)
        """
        self.html_processor = html_processor
        self.schema_processor = schema_processor
        self.schema_mode = schema_mode

    def execute(self, html_files: List[str]) -> Dict[str, Any]:
        """
        执行 Schema 迭代阶段

        3 个步骤：
        1. 批量简化所有 HTML
        2. 并行提取/补充 Schema
        3. 合并最终 Schema

        Args:
            html_files: HTML 文件路径列表

        Returns:
            {
                'success': bool,
                'rounds': List[Dict],        # 每轮的详细结果
                'final_schema': Dict,        # 最终合并的 Schema
                'final_schema_path': str,    # 最终 Schema 文件路径
            }
        """
        result = {
            'rounds': [],
            'final_schema': None,
            'success': False,
        }

        logger.info(f"\n{'='*70}")
        if self.schema_mode == "auto":
            logger.info(f"阶段1: Schema迭代 - 自动模式（{len(html_files)}个URL，{len(html_files)}轮迭代）")
        else:
            logger.info(f"阶段1: Schema补充 - 预定义模式（{len(html_files)}个URL，{len(html_files)}轮迭代）")
        logger.info(f"{'='*70}")

        # ============ 步骤 1：批量简化所有 HTML ============
        logger.info(f"\n{'═'*70}")
        logger.info(f"阶段1/3: 批量简化HTML文件")
        logger.info(f"{'═'*70}")

        simplified_data_list = []
        for idx, html_file_path in enumerate(html_files, 1):
            logger.info(f"  正在精简 [{idx}/{len(html_files)}]: {Path(html_file_path).name}")
            simplified_data = self.html_processor.process({
                'html_file': html_file_path,
                'idx': idx
            })
            if simplified_data['success']:
                simplified_data_list.append(simplified_data)
            else:
                logger.error(f"HTML精简失败: {html_file_path}")
                if idx == 1:
                    return result

        if not simplified_data_list:
            logger.error("没有成功精简的HTML文件")
            return result

        logger.success(f"✓ 已精简 {len(simplified_data_list)} 个HTML文件")

        # ============ 步骤 2：并行提取/补充 Schema ============
        logger.info(f"\n{'═'*70}")
        if self.schema_mode == "auto":
            logger.info(f"阶段2/3: 并行提取 HTML Schema（并发数: {min(settings.max_concurrent_extractions, len(simplified_data_list))}）")
        else:
            logger.info(f"阶段2/3: 并行补充 xpath（并发数: {min(settings.max_concurrent_extractions, len(simplified_data_list))}）")
        logger.info(f"{'═'*70}")

        schema_results = []
        # 使用配置的并发数，避免 API 限流
        max_workers = min(settings.max_concurrent_extractions, len(simplified_data_list))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_data = {
                executor.submit(
                    self.schema_processor.process,
                    {'html_content': data['html_content'], 'idx': data['idx']}
                ): data
                for data in simplified_data_list
            }

            for future in as_completed(future_to_data):
                schema_result = future.result()
                if schema_result['success']:
                    schema_results.append(schema_result)

        # 按 idx 排序
        schema_results.sort(key=lambda x: x['idx'])
        logger.success(f"✓ 已处理 {len(schema_results)} 个HTML的Schema")

        if not schema_results:
            logger.error("没有成功处理的Schema")
            return result

        # ============ 构建轮次结果 ============
        all_schemas = []
        for i, simplified in enumerate(simplified_data_list):
            idx = simplified['idx']
            html_file_path = simplified['html_file']

            # 查找对应的 Schema 结果
            schema_result = next((r for r in schema_results if r['idx'] == idx), None)

            if schema_result:
                schema = schema_result['schema']
                all_schemas.append(schema)

                round_result = {
                    'round': idx,
                    'html_file': html_file_path,
                    'url': html_file_path,
                    'html_original_path': simplified['html_original_path'],
                    'html_path': simplified['html_path'],
                    'html_schema': schema.copy(),
                    'html_schema_path': schema_result['schema_path'],
                    'schema': schema.copy(),
                    'schema_path': schema_result['schema_path'],
                    'groundtruth_schema': schema.copy(),
                    'success': True,
                }
                result['rounds'].append(round_result)

        # ============ 步骤 3：合并多个 Schema，生成最终 Schema ============
        if all_schemas:
            logger.info(f"\n{'═'*70}")
            logger.info(f"阶段3/3: 合并 {len(all_schemas)} 个 Schema")
            logger.info(f"{'═'*70}")

            try:
                final_schema = self.schema_processor.merge_schemas(all_schemas)

                result['final_schema'] = final_schema
                result['final_schema_path'] = str(
                    self.schema_processor.schemas_dir / "final_schema.json"
                )
                result['success'] = True

            except Exception as e:
                logger.error(f"合并多个Schema失败: {str(e)}")
                import traceback
                logger.debug(traceback.format_exc())

        return result
