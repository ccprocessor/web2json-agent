"""
解析器处理器
负责使用生成的解析器批量解析 HTML 文件
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger
from tqdm import tqdm

from .base_processor import BaseProcessor


class ParserProcessor(BaseProcessor):
    """解析器处理器 - 负责批量解析 HTML 文件"""

    def __init__(self, result_dir: Path):
        """
        初始化解析器处理器

        Args:
            result_dir: 解析结果保存目录
        """
        self.result_dir = result_dir

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用解析器批量解析 HTML 文件

        Args:
            input_data: {
                'html_files': List[str],  # HTML 文件路径列表
                'parser_path': str,       # 解析器文件路径
            }

        Returns:
            {
                'success': bool,
                'total_files': int,
                'parsed_files': List[Dict],   # 成功解析的文件信息
                'failed_files': List[Dict],   # 失败的文件信息
                'output_dir': str,
            }
        """
        html_files = input_data['html_files']
        parser_path = input_data['parser_path']

        logger.info(f"\n{'='*70}")
        logger.info(f"批量解析阶段：解析 {len(html_files)} 个 HTML 文件")
        logger.info(f"{'='*70}")

        results = {
            'success': True,
            'total_files': len(html_files),
            'parsed_files': [],
            'failed_files': [],
            'output_dir': str(self.result_dir),
        }

        try:
            # 加载解析器
            parser = self._load_parser(parser_path)

            # 使用进度条显示解析进度
            with tqdm(total=len(html_files), desc="解析HTML文件", unit="file") as pbar:
                for html_file_path in html_files:
                    html_path = Path(html_file_path)

                    try:
                        # 读取 HTML 内容
                        with open(html_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()

                        # 使用解析器解析 HTML
                        parsed_data = parser.parse(html_content)

                        # 确定保存路径（基于原文件名）
                        json_filename = html_path.stem + '.json'
                        json_path = self.result_dir / json_filename

                        # 保存 JSON
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(parsed_data, f, ensure_ascii=False, indent=2)

                        results['parsed_files'].append({
                            'html_file': str(html_path),
                            'json_file': str(json_path),
                            'fields_count': len(parsed_data),
                        })

                        # 更新进度条
                        pbar.update(1)

                    except Exception as e:
                        # 只在出错时输出日志
                        logger.error(f"✗ 解析失败 ({html_path.name}): {str(e)}")
                        results['failed_files'].append({
                            'html_file': str(html_path),
                            'error': str(e),
                        })
                        import traceback
                        logger.debug(traceback.format_exc())

                        # 更新进度条
                        pbar.update(1)

            # 输出汇总
            logger.info(f"\n{'='*70}")
            logger.info("批量解析完成")
            logger.info(f"{'='*70}")
            logger.success(f"成功解析: {len(results['parsed_files'])}/{len(html_files)} 个文件")
            if results['failed_files']:
                logger.warning(f"失败: {len(results['failed_files'])} 个文件")
            logger.info(f"结果保存目录: {self.result_dir}")
            logger.info(f"{'='*70}\n")

            results['success'] = len(results['parsed_files']) > 0
            return results

        except Exception as e:
            logger.error(f"批量解析过程出错: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            results['success'] = False
            results['error'] = str(e)
            return results

    def _load_parser(self, parser_path: str):
        """动态加载解析器类"""
        spec = importlib.util.spec_from_file_location("parser_module", parser_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["parser_module"] = module
        spec.loader.exec_module(module)

        # 获取 WebPageParser 类
        if hasattr(module, 'WebPageParser'):
            return module.WebPageParser()
        else:
            raise Exception("解析器中未找到WebPageParser类")
