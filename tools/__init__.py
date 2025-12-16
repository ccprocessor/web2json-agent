"""
工具模块
提供网页解析所需的各种工具
"""
from .webpage_source import get_webpage_source, get_html_from_file
from .webpage_screenshot import capture_webpage_screenshot, capture_html_file_screenshot
from .visual_understanding import extract_json_from_image, refine_schema_from_image
from .code_generator import generate_parser_code
from .code_fixer import fix_parser_code
from .schema_extraction import (
    extract_schema_from_html,
    extract_schema_from_image,
    merge_html_and_visual_schema,
    merge_multiple_schemas
)

__all__ = [
    'get_webpage_source',
    'get_html_from_file',
    'capture_webpage_screenshot',
    'capture_html_file_screenshot',
    'extract_json_from_image',
    'refine_schema_from_image',
    'generate_parser_code',
    'fix_parser_code',
    'extract_schema_from_html',
    'extract_schema_from_image',
    'merge_html_and_visual_schema',
    'merge_multiple_schemas',
]

