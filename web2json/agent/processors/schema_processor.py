"""
Schema 处理器
负责 Schema 的提取、补充和合并
"""
import json
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from web2json.tools import (
    extract_schema_from_html,
    merge_multiple_schemas,
    enrich_schema_with_xpath,
)

from .base_processor import BaseProcessor


class SchemaProcessor(BaseProcessor):
    """Schema 处理器 - 负责 Schema 提取、补充和合并"""

    def __init__(self, schemas_dir: Path, schema_mode: str = 'auto', schema_template: Dict = None):
        """
        初始化 Schema 处理器

        Args:
            schemas_dir: Schema 保存目录
            schema_mode: Schema 模式 (auto/predefined)
            schema_template: 预定义的 Schema 模板
        """
        self.schemas_dir = schemas_dir
        self.schema_mode = schema_mode
        self.schema_template = schema_template

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 Schema（提取或补充）

        根据 schema_mode 选择不同的处理方式：
        - auto: 从 HTML 提取 Schema
        - predefined: 为预定义 Schema 补充 xpath

        Args:
            input_data: {
                'html_content': str,  # HTML 内容
                'idx': int,           # 轮次编号
            }

        Returns:
            {
                'success': bool,
                'idx': int,
                'schema': Dict,           # 提取或补充后的 Schema
                'schema_path': str,       # Schema 文件路径
                'error': str,             # 错误信息（如果失败）
            }
        """
        if self.schema_mode == 'auto':
            return self._extract_schema(input_data)
        elif self.schema_mode == 'predefined':
            return self._enrich_schema(input_data)
        else:
            raise ValueError(f"未知的 schema_mode: {self.schema_mode}")

    def _extract_schema(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """从 HTML 提取 Schema（自动模式）"""
        idx = input_data['idx']
        html_content = input_data['html_content']

        result = {
            'success': False,
            'idx': idx,
        }

        try:
            html_schema = extract_schema_from_html(html_content=html_content)
            logger.success(f"[提取阶段 {idx}] ✓ Schema提取完成（{len(html_schema)} 字段）")

            # 保存 schema
            schema_path = self.schemas_dir / f"html_schema_round_{idx}.json"
            with open(schema_path, 'w', encoding='utf-8') as f:
                json.dump(html_schema, f, ensure_ascii=False, indent=2)

            result.update({
                'success': True,
                'schema': html_schema,
                'schema_path': str(schema_path),
            })

        except Exception as e:
            logger.error(f"[提取阶段 {idx}] ✗ 失败: {str(e)}")
            result['error'] = str(e)

        return result

    def _enrich_schema(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """为预定义 Schema 补充 xpath（预定义模式）"""
        idx = input_data['idx']
        html_content = input_data['html_content']

        result = {
            'success': False,
            'idx': idx,
        }

        try:
            enriched_schema = enrich_schema_with_xpath(
                schema_template=self.schema_template,
                html_content=html_content
            )
            logger.success(f"[补充阶段 {idx}] ✓ Schema补充完成（{len(enriched_schema)} 字段）")

            # 保存 schema
            schema_path = self.schemas_dir / f"enriched_schema_round_{idx}.json"
            with open(schema_path, 'w', encoding='utf-8') as f:
                json.dump(enriched_schema, f, ensure_ascii=False, indent=2)

            result.update({
                'success': True,
                'schema': enriched_schema,
                'schema_path': str(schema_path),
            })

        except Exception as e:
            logger.error(f"[补充阶段 {idx}] ✗ 失败: {str(e)}")
            result['error'] = str(e)

        return result

    def merge_schemas(self, schemas: List[Dict]) -> Dict:
        """
        合并多个 Schema

        Args:
            schemas: Schema 列表

        Returns:
            合并后的 Schema
        """
        final_schema = merge_multiple_schemas(schemas=schemas)
        logger.success(f"✓ 合并完成，最终 Schema 包含 {len(final_schema)} 个字段")

        # 保存最终 Schema
        final_schema_path = self.schemas_dir / "final_schema.json"
        with open(final_schema_path, 'w', encoding='utf-8') as f:
            json.dump(final_schema, f, ensure_ascii=False, indent=2)
        logger.success(f"✓ 最终Schema已保存: {final_schema_path}")

        return final_schema
