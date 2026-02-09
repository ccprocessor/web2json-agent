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

    def __init__(self, result_dir: Path, save_to_disk: bool = True):
        """
        初始化解析器处理器

        Args:
            result_dir: 解析结果保存目录
            save_to_disk: 是否保存到磁盘（默认True，False时仅在内存中处理）
        """
        self.result_dir = result_dir
        self.save_to_disk = save_to_disk

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
                'output_dir': str,            # 仅在save_to_disk=True时有值
                'parsed_data': List[Dict],    # 解析后的数据（包含filename和data）
            }
        """
        html_files = input_data['html_files']
        parser_path = input_data['parser_path']

        # 只有保存模式才打印详细的阶段信息
        if self.save_to_disk:
            logger.info(f"\n{'='*70}")
            logger.info(f"批量解析阶段：解析 {len(html_files)} 个 HTML 文件")
            logger.info(f"{'='*70}")

        results = {
            'success': True,
            'total_files': len(html_files),
            'parsed_files': [],
            'failed_files': [],
            'output_dir': str(self.result_dir) if self.save_to_disk else '',
            'parsed_data': [],  # 存储解析后的数据（filename + data）
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

                        # 规范化解析结果中的Unicode字符
                        parsed_data = self._normalize_result(parsed_data)

                        # 根据模式选择处理方式
                        if self.save_to_disk:
                            # 保存模式：写入磁盘
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
                        else:
                            # 内存模式：只保存到内存
                            results['parsed_files'].append({
                                'html_file': str(html_path),
                                'fields_count': len(parsed_data),
                            })

                        # 总是收集到 parsed_data（供 API 返回）
                        results['parsed_data'].append({
                            'filename': html_path.name,
                            'data': parsed_data
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
            if self.save_to_disk:
                # 保存模式：打印完整的汇总信息
                logger.info(f"\n{'='*70}")
                logger.info("批量解析完成")
                logger.info(f"{'='*70}")
                logger.success(f"成功解析: {len(results['parsed_files'])}/{len(html_files)} 个文件")
                if results['failed_files']:
                    logger.warning(f"失败: {len(results['failed_files'])} 个文件")
                logger.info(f"结果保存目录: {self.result_dir}")
                logger.info(f"{'='*70}\n")
            # 内存模式：不打印保存相关信息（进度条已经显示了解析进度）

            results['success'] = len(results['parsed_files']) > 0
            return results

        except Exception as e:
            logger.error(f"批量解析过程出错: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            results['success'] = False
            results['error'] = str(e)
            return results

    def _normalize_text(self, text: str) -> str:
        """
        规范化文本中的Unicode特殊字符

        Args:
            text: 原始文本

        Returns:
            规范化后的文本
        """
        if not text or not isinstance(text, str):
            return text

        # 将各种Unicode连字符转换为标准ASCII连字符
        text = text.replace('\u2013', '-')  # en dash
        text = text.replace('\u2014', '-')  # em dash
        text = text.replace('\u2015', '-')  # horizontal bar
        text = text.replace('\u2212', '-')  # minus sign

        # 将Unicode引号转换为标准引号
        text = text.replace('\u2018', "'")  # left single quotation mark
        text = text.replace('\u2019', "'")  # right single quotation mark
        text = text.replace('\u201c', '"')  # left double quotation mark
        text = text.replace('\u201d', '"')  # right double quotation mark

        # 规范化空白字符
        text = text.replace('\u00a0', ' ')  # non-breaking space
        text = text.replace('\u2002', ' ')  # en space
        text = text.replace('\u2003', ' ')  # em space
        text = text.replace('\u2009', ' ')  # thin space

        return text

    def _normalize_result(self, data: Any) -> Any:
        """
        递归规范化解析结果中的所有文本

        Args:
            data: 解析结果（可以是dict, list, str或其他类型）

        Returns:
            规范化后的数据
        """
        if isinstance(data, dict):
            return {key: self._normalize_result(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._normalize_result(item) for item in data]
        elif isinstance(data, str):
            return self._normalize_text(data)
        else:
            return data

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
