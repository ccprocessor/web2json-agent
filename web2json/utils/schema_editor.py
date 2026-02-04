"""
Schema编辑工具
支持schema编辑、字段变化检测等功能
"""
import json
from typing import Dict, Set, Tuple
from pathlib import Path
from loguru import logger


class SchemaEditor:
    """Schema编辑工具类"""

    @staticmethod
    def detect_field_changes(original_schema: Dict, edited_schema: Dict) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        检测schema字段变化

        Args:
            original_schema: 原始schema
            edited_schema: 编辑后的schema

        Returns:
            (added_fields, removed_fields, modified_fields)
            - added_fields: 新增的字段集合
            - removed_fields: 删除的字段集合
            - modified_fields: 修改的字段集合
        """
        original_keys = set(original_schema.keys())
        edited_keys = set(edited_schema.keys())

        added_fields = edited_keys - original_keys
        removed_fields = original_keys - edited_keys

        # 检测字段内容修改（仅检查共同字段）
        common_fields = original_keys & edited_keys
        modified_fields = set()

        for field in common_fields:
            # 比较字段的内容（转换为JSON字符串比较）
            original_content = json.dumps(original_schema[field], sort_keys=True, ensure_ascii=False)
            edited_content = json.dumps(edited_schema[field], sort_keys=True, ensure_ascii=False)

            if original_content != edited_content:
                modified_fields.add(field)

        return added_fields, removed_fields, modified_fields

    @staticmethod
    def has_new_fields(original_schema: Dict, edited_schema: Dict) -> bool:
        """
        检测是否有新增字段

        Args:
            original_schema: 原始schema
            edited_schema: 编辑后的schema

        Returns:
            是否有新增字段
        """
        added_fields, _, _ = SchemaEditor.detect_field_changes(original_schema, edited_schema)
        return len(added_fields) > 0

    @staticmethod
    def wait_for_user_edit(schema_path: str) -> Dict:
        """
        等待用户编辑schema文件

        Args:
            schema_path: schema文件路径

        Returns:
            编辑后的schema字典
        """
        schema_path = Path(schema_path)

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema文件不存在: {schema_path}")

        logger.info(f"\n{'='*70}")
        logger.info(f"Schema编辑模式已启用")
        logger.info(f"{'='*70}")
        logger.info(f"Schema文件路径: {schema_path}")
        logger.info(f"\n请按以下步骤操作:")
        logger.info(f"  1. 打开文件进行编辑: {schema_path}")
        logger.info(f"  2. 编辑完成后保存文件")
        logger.info(f"  3. 在此处按回车键继续...")
        logger.info(f"{'='*70}\n")

        # 等待用户输入
        input("按回车键继续...")

        # 重新加载编辑后的schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            edited_schema = json.load(f)

        logger.info("已加载编辑后的Schema")
        return edited_schema

    @staticmethod
    def print_field_changes(original_schema: Dict, edited_schema: Dict):
        """
        打印字段变化信息

        Args:
            original_schema: 原始schema
            edited_schema: 编辑后的schema
        """
        added_fields, removed_fields, modified_fields = SchemaEditor.detect_field_changes(
            original_schema, edited_schema
        )

        logger.info(f"\n{'='*70}")
        logger.info(f"Schema字段变化检测")
        logger.info(f"{'='*70}")

        if added_fields:
            logger.info(f"新增字段 ({len(added_fields)}个): {', '.join(sorted(added_fields))}")
        else:
            logger.info(f"新增字段: 无")

        if removed_fields:
            logger.warning(f"删除字段 ({len(removed_fields)}个): {', '.join(sorted(removed_fields))}")
        else:
            logger.info(f"删除字段: 无")

        if modified_fields:
            logger.info(f"修改字段 ({len(modified_fields)}个): {', '.join(sorted(modified_fields))}")
        else:
            logger.info(f"修改字段: 无")

        logger.info(f"{'='*70}\n")

    @staticmethod
    def create_schema_template_from_fields(field_names: list) -> dict:
        """
        根据字段名列表生成schema模板

        Args:
            field_names: 字段名列表

        Returns:
            schema模板字典
        """
        schema_template = {}
        for field_name in field_names:
            schema_template[field_name] = {
                "type": "",
                "description": "",
                "value_sample": "",
                "xpaths": [""]
            }
        return schema_template
