"""
工具模块
提供网页解析所需的各种工具
"""
from .webpage_source import get_html_from_file
from .webpage_screenshot import capture_html_file_screenshot, close_browser
from .code_generator import generate_parser_code
from .schema_extraction import (
    extract_schema_from_html,
    # extract_schema_from_image,  # 已禁用视觉Schema提取
    # merge_html_and_visual_schema,  # 已禁用HTML和视觉Schema合并
    merge_multiple_schemas,
    enrich_schema_with_xpath
)
from .cluster import cluster_html_layouts
from .html_layout_cosin import get_feature, similarity

__all__ = [
    'get_html_from_file',
    'capture_html_file_screenshot',
    'close_browser',
    'generate_parser_code',
    'extract_schema_from_html',
    # 'extract_schema_from_image',  # 已禁用
    # 'merge_html_and_visual_schema',  # 已禁用
    'merge_multiple_schemas',
    'enrich_schema_with_xpath',
    'cluster_html_layouts',
    'get_feature',
    'similarity',
]

