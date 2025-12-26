"""
HTML 处理器
负责 HTML 文件的读取和简化
"""
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from web2json.config.settings import settings
from web2json.tools import get_html_from_file
from web2json.tools.html_simplifier import simplify_html

from .base_processor import BaseProcessor


class HtmlProcessor(BaseProcessor):
    """HTML 处理器 - 负责 HTML 读取和简化"""

    def __init__(self, html_original_dir: Path, html_simplified_dir: Path):
        """
        初始化 HTML 处理器

        Args:
            html_original_dir: 原始 HTML 保存目录
            html_simplified_dir: 简化后 HTML 保存目录
        """
        self.html_original_dir = html_original_dir
        self.html_simplified_dir = html_simplified_dir

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        读取并简化单个 HTML 文件

        Args:
            input_data: {
                'html_file': str,  # HTML 文件路径
                'idx': int,        # 轮次编号
            }

        Returns:
            {
                'success': bool,
                'idx': int,
                'html_file': str,
                'html_content': str,          # 处理后的 HTML 内容
                'html_original_path': str,    # 原始 HTML 路径
                'html_path': str,             # 最终使用的 HTML 路径
                'error': str,                 # 错误信息（如果失败）
            }
        """
        html_file_path = input_data['html_file']
        idx = input_data['idx']

        result = {
            'success': False,
            'idx': idx,
            'html_file': html_file_path,
        }

        try:
            # 1. 读取 HTML 文件内容
            html_content = get_html_from_file.invoke({"file_path": html_file_path})

            # 保存原始 HTML
            html_original_path = self.html_original_dir / f"schema_round_{idx}.html"
            with open(html_original_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # 2. 精简 HTML
            try:
                mode = settings.html_simplify_mode
                keep_attrs = settings.html_keep_attrs if mode != 'conservative' else None

                simplified_html = simplify_html(
                    html_content,
                    mode=mode,
                    keep_attrs=keep_attrs
                )
                html_simplified_path = self.html_simplified_dir / f"schema_round_{idx}.html"
                with open(html_simplified_path, 'w', encoding='utf-8') as f:
                    f.write(simplified_html)

                compression_rate = (1 - len(simplified_html) / len(html_content)) * 100
                logger.success(
                    f"  [{idx}] ✓ 精简完成（{len(html_content)} → {len(simplified_html)} 字符，"
                    f"压缩 {compression_rate:.1f}%）"
                )

                html_path = html_simplified_path
                html_for_processing = simplified_html
            except Exception as e:
                logger.warning(f"  [{idx}] ⚠ 精简失败: {e}，使用原始HTML")
                html_path = html_original_path
                html_for_processing = html_content

            result.update({
                'success': True,
                'html_content': html_for_processing,
                'html_original_path': str(html_original_path),
                'html_path': str(html_path),
            })

        except Exception as e:
            logger.error(f"  [{idx}] ✗ 失败: {str(e)}")
            result['error'] = str(e)

        return result
