"""
web2json-agent - 智能网页解析代码生成器

基于 AI 自动生成网页解析代码，告别手写 XPath 和 CSS 选择器
"""

__version__ = "1.1.3"
__author__ = "YangGuoqiang"
__email__ = "1041206149@qq.com"

# 导入简洁API
from web2json.simple import (
    Web2JsonConfig,
    extract_data,
    extract_schema,
    infer_code,
    extract_data_with_code,
    classify_html_dir
)

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "Web2JsonConfig",
    "extract_data",
    "extract_schema",
    "infer_code",
    "extract_data_with_code",
    "classify_html_dir"
]
