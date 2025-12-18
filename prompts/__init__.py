"""
Prompts 模块
集中管理所有 LLM Prompt 模板
"""

from .code_generator import CodeGeneratorPrompts
from .schema_extraction import SchemaExtractionPrompts
from .schema_merge import SchemaMergePrompts

__all__ = [
    'CodeGeneratorPrompts',
    'SchemaExtractionPrompts',
    'SchemaMergePrompts',
]
