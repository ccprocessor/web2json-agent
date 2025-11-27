"""
Prompts 模块
集中管理所有 LLM Prompt 模板
"""

from .code_generator import CodeGeneratorPrompts
from .code_fixer import CodeFixerPrompts
from .visual_understanding import VisualUnderstandingPrompts

__all__ = [
    'CodeGeneratorPrompts',
    'CodeFixerPrompts',
    'VisualUnderstandingPrompts',
]
