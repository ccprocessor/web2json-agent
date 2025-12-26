"""
代码生成处理器
负责解析器代码的生成和优化
"""
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from web2json.tools import generate_parser_code

from .base_processor import BaseProcessor


class CodeProcessor(BaseProcessor):
    """代码处理器 - 负责生成和优化解析器代码"""

    def __init__(self, parsers_dir: Path):
        """
        初始化代码处理器

        Args:
            parsers_dir: 解析器代码保存目录
        """
        self.parsers_dir = parsers_dir

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成或优化解析器代码

        Args:
            input_data: {
                'html_content': str,            # HTML 内容
                'target_json': Dict,            # 目标 Schema
                'idx': int,                     # 轮次编号
                'previous_parser_code': str,    # 上一轮的代码（可选）
                'previous_parser_path': str,    # 上一轮的路径（可选）
            }

        Returns:
            {
                'success': bool,
                'idx': int,
                'code': str,              # 生成的代码
                'parser_path': str,       # 代码文件路径
                'error': str,             # 错误信息（如果失败）
            }
        """
        html_content = input_data['html_content']
        target_json = input_data['target_json']
        idx = input_data['idx']
        previous_parser_code = input_data.get('previous_parser_code')
        previous_parser_path = input_data.get('previous_parser_path')

        result = {
            'success': False,
            'idx': idx,
        }

        try:
            # 构建调用参数
            invoke_params = {
                "html_content": html_content,
                "target_json": target_json,
                "output_dir": str(self.parsers_dir)
            }

            # 如果是优化模式（有上一轮的代码）
            if previous_parser_code:
                invoke_params.update({
                    "previous_parser_code": previous_parser_code,
                    "previous_parser_path": previous_parser_path,
                    "round_num": idx
                })

            # 调用代码生成工具
            parser_result = generate_parser_code.invoke(invoke_params)

            # 保存解析器代码
            parser_filename = f"parser_round_{idx}.py"
            parser_path = self.parsers_dir / parser_filename
            with open(parser_path, 'w', encoding='utf-8') as f:
                f.write(parser_result['code'])

            logger.success(f"  ✓ 已生成: {parser_filename}")

            result.update({
                'success': True,
                'code': parser_result['code'],
                'parser_path': str(parser_path),
            })

        except Exception as e:
            logger.error(f"  ✗ 代码生成失败: {str(e)}")
            result['error'] = str(e)

        return result

    def save_final_parser(self, code: str, output_dir: Path, config: Dict) -> Dict:
        """
        保存最终解析器

        Args:
            code: 解析器代码
            output_dir: 输出目录
            config: 配置信息（Schema）

        Returns:
            最终解析器信息
        """
        final_parser_path = output_dir / "final_parser.py"
        with open(final_parser_path, 'w', encoding='utf-8') as f:
            f.write(code)
        logger.success(f"最终解析器已保存: {final_parser_path}")

        return {
            'parser_path': str(final_parser_path),
            'code': code,
            'config_path': None,
            'config': config,
        }
