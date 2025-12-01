"""
Agent 执行器
负责执行具体的任务步骤
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, List

from loguru import logger

from tools import (
    get_webpage_source,  # 获取网页源码工具
    capture_webpage_screenshot,  # 截图工具
    extract_json_from_image,  # 提取JSON Schema工具
    refine_schema_from_image,  # Schema迭代优化工具
    generate_parser_code,  # 生成解析代码工具
)


class AgentExecutor:
    """Agent执行器，负责执行具体任务"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        self.screenshots_dir = self.output_dir / "screenshots"
        self.parsers_dir = self.output_dir / "parsers"
        self.html_dir = self.output_dir / "html"
        self.result_dir = self.output_dir / "result"
        self.schemas_dir = self.output_dir / "schemas"

        self.screenshots_dir.mkdir(exist_ok=True)
        self.parsers_dir.mkdir(exist_ok=True)
        self.html_dir.mkdir(exist_ok=True)
        self.result_dir.mkdir(exist_ok=True)
        self.schemas_dir.mkdir(exist_ok=True)
    
    def execute_plan(self, plan: Dict) -> Dict:
        """
        执行计划 - 两阶段迭代执行

        阶段1: Schema迭代（前N个URL）- 获取HTML -> 截图 -> 提取/优化JSON Schema
        阶段2: 代码迭代（后M个URL）- 基于最终Schema生成代码 -> 验证 -> 优化代码

        Args:
            plan: 执行计划

        Returns:
            执行结果
        """
        logger.info("开始执行计划...")

        results = {
            'plan': plan,
            'schema_phase': {
                'rounds': [],
                'final_schema': None,
            },
            'code_phase': {
                'rounds': [],
                'parsers': [],
            },
            'final_parser': None,
            'success': False,
        }

        # 使用所有输入的URL进行迭代
        sample_urls = plan['sample_urls']
        num_urls = len(sample_urls)

        # 阶段1: Schema迭代（使用所有URL）
        logger.info(f"\n{'='*70}")
        logger.info(f"阶段1: Schema迭代（{num_urls}个URL，{num_urls}轮迭代）")
        logger.info(f"{'='*70}")

        schema_result = self._execute_schema_iteration_phase(sample_urls)
        results['schema_phase'] = schema_result

        if not schema_result['success']:
            logger.error("Schema迭代阶段失败")
            return results

        final_schema = schema_result['final_schema']
        logger.success(f"Schema迭代完成，最终Schema包含 {len(final_schema)} 个字段")

        # 阶段2: 代码迭代（复用Schema阶段的HTML）
        logger.info(f"\n{'='*70}")
        logger.info(f"阶段2: 代码迭代（使用Schema阶段的{num_urls}个HTML，{num_urls}轮迭代）")
        logger.info(f"{'='*70}")

        code_result = self._execute_code_iteration_phase(
            sample_urls,  # 仅用于日志，实际使用schema_result['rounds']中的数据
            final_schema,
            schema_result['rounds']  # 传递schema阶段的数据（包含HTML）
        )
        results['code_phase'] = code_result

        if code_result['success']:
            results['final_parser'] = code_result['final_parser']
            results['success'] = True

            # 使用最终解析器解析所有HTML并生成JSON
            logger.info(f"\n{'='*70}")
            logger.info("使用最终解析器解析所有HTML")
            logger.info(f"{'='*70}")
            # 只使用Schema阶段的数据，因为代码阶段复用了Schema阶段的HTML
            self._parse_all_html_with_final_parser(results, schema_result['rounds'])
        else:
            logger.error("代码迭代阶段失败")

        return results

    def _execute_schema_iteration_phase(self, urls: List[str]) -> Dict:
        """
        执行Schema迭代阶段

        第一轮：提取初始Schema
        后续轮：基于新截图优化Schema

        Args:
            urls: URL列表

        Returns:
            Schema迭代结果
        """
        result = {
            'rounds': [],
            'final_schema': None,
            'success': False,
        }

        current_schema = None

        for idx, url in enumerate(urls, 1):
            logger.info(f"\n{'─'*70}")
            logger.info(f"Schema迭代 - 第 {idx}/{len(urls)} 轮")
            logger.info(f"{'─'*70}")

            try:
                # 1. 获取HTML源码
                logger.info(f"  [1/3] 获取HTML源码...")
                html_content = get_webpage_source.invoke({"url": url})
                logger.success(f"  ✓ HTML源码已获取")

                # 保存HTML源码
                html_path = self.html_dir / f"schema_round_{idx}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.success(f"  ✓ HTML已保存: {html_path}")

                # 2. 截图
                logger.info(f"  [2/3] 截图...")
                screenshot_path = str(self.screenshots_dir / f"schema_round_{idx}.png")
                screenshot_result = capture_webpage_screenshot.invoke({
                    "url": url,
                    "save_path": screenshot_path
                })
                logger.success(f"  ✓ 截图已保存: {screenshot_path}")

                # 3. 提取或优化Schema
                if idx == 1:
                    logger.info(f"  [3/3] 提取初始Schema...")
                    current_schema = extract_json_from_image.invoke({
                        "image_path": screenshot_result
                    })
                    logger.success(f"  ✓ 初始Schema已提取，包含 {len(current_schema)} 个字段")
                else:
                    logger.info(f"  [3/3] 优化Schema（基于上一轮）...")
                    current_schema = refine_schema_from_image.invoke({
                        "image_path": screenshot_result,
                        "previous_schema": current_schema
                    })
                    logger.success(f"  ✓ Schema已优化，当前包含 {len(current_schema)} 个字段")

                # 保存本轮Schema
                schema_path = self.schemas_dir / f"schema_round_{idx}.json"
                with open(schema_path, 'w', encoding='utf-8') as f:
                    json.dump(current_schema, f, ensure_ascii=False, indent=2)
                logger.success(f"  ✓ Schema已保存: {schema_path}")

                # 记录本轮结果
                round_result = {
                    'round': idx,
                    'url': url,
                    'html_path': str(html_path),
                    'screenshot': screenshot_result,
                    'schema': current_schema.copy(),
                    'schema_path': str(schema_path),
                    'groundtruth_schema': current_schema.copy(),
                    'success': True,
                }
                result['rounds'].append(round_result)
                logger.success(f"Schema迭代第 {idx} 轮完成")

            except Exception as e:
                logger.error(f"Schema迭代第 {idx} 轮失败: {str(e)}")
                import traceback
                logger.debug(traceback.format_exc())

                round_result = {
                    'round': idx,
                    'url': url,
                    'error': str(e),
                    'success': False,
                }
                result['rounds'].append(round_result)

                if idx == 1:
                    # 第一轮失败则退出
                    return result

        # 设置最终Schema
        if current_schema:
            result['final_schema'] = current_schema
            result['success'] = True

            # 保存最终Schema
            final_schema_path = self.schemas_dir / "final_schema.json"
            with open(final_schema_path, 'w', encoding='utf-8') as f:
                json.dump(current_schema, f, ensure_ascii=False, indent=2)
            logger.success(f"最终Schema已保存: {final_schema_path}")
            result['final_schema_path'] = str(final_schema_path)

        return result

    def _execute_code_iteration_phase(
        self,
        urls: List[str],
        final_schema: Dict,
        schema_phase_rounds: List[Dict]
    ) -> Dict:
        """
        执行代码迭代阶段

        复用Schema阶段的HTML，不重复获取网页和截图
        只进行代码生成和迭代优化

        第一轮：基于最终Schema生成初始解析代码
        后续轮：基于验证结果优化代码

        Args:
            urls: URL列表（应与schema_phase_rounds对应）
            final_schema: 来自Schema迭代阶段的最终Schema
            schema_phase_rounds: Schema阶段的轮次数据（包含HTML）

        Returns:
            代码迭代结果
        """
        result = {
            'rounds': [],
            'parsers': [],
            'final_parser': None,
            'success': False,
        }

        # 确保有可用的Schema阶段数据
        if not schema_phase_rounds:
            logger.error("Schema阶段没有可用的数据")
            return result

        current_parser_code = None
        current_parser_path = None

        # 使用Schema阶段的轮次数据
        for idx, schema_round in enumerate(schema_phase_rounds, 1):
            if not schema_round.get('success'):
                logger.warning(f"Schema阶段第 {idx} 轮失败，跳过代码生成")
                continue

            logger.info(f"\n{'─'*70}")
            logger.info(f"代码迭代 - 第 {idx}/{len(schema_phase_rounds)} 轮")
            logger.info(f"{'─'*70}")

            try:
                # 复用Schema阶段的HTML
                html_path = schema_round.get('html_path')
                if not html_path:
                    logger.error(f"  ✗ Schema阶段第 {idx} 轮缺少HTML路径")
                    continue

                logger.info(f"  [1/2] 复用Schema阶段的HTML: {html_path}")
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                logger.success(f"  ✓ HTML已加载")

                # 生成或优化解析代码
                if idx == 1:
                    logger.info(f"  [2/2] 生成初始解析代码...")
                    parser_result = generate_parser_code.invoke({
                        "html_content": html_content,
                        "target_json": final_schema,
                        "output_dir": str(self.parsers_dir)
                    })
                    logger.success(f"  ✓ 初始解析代码已生成")
                else:
                    logger.info(f"  [2/2] 优化解析代码（基于上一轮）...")
                    parser_result = generate_parser_code.invoke({
                        "html_content": html_content,
                        "target_json": final_schema,
                        "output_dir": str(self.parsers_dir),
                        "previous_parser_code": current_parser_code,
                        "previous_parser_path": current_parser_path,
                        "round_num": idx
                    })
                    logger.success(f"  ✓ 解析代码已优化")

                # 保存解析器代码
                parser_filename = f"parser_round_{idx}.py"
                code_parser_path = self.parsers_dir / parser_filename
                with open(code_parser_path, 'w', encoding='utf-8') as f:
                    f.write(parser_result['code'])
                logger.success(f"  ✓ 解析器已保存: {code_parser_path}")

                # 更新当前解析器
                current_parser_code = parser_result['code']
                current_parser_path = str(code_parser_path)
                parser_result['parser_path'] = current_parser_path

                # 记录本轮结果（复用Schema阶段的数据）
                round_result = {
                    'round': idx,
                    'url': schema_round['url'],
                    'html_path': html_path,
                    'screenshot': schema_round.get('screenshot'),  # 复用Schema阶段的截图
                    'groundtruth_schema': schema_round.get('groundtruth_schema'),  # 复用Schema阶段的groundtruth
                    'parser_path': current_parser_path,
                    'parser_code': current_parser_code,
                    'parser_result': parser_result,
                    'success': True,
                }
                result['rounds'].append(round_result)
                result['parsers'].append(parser_result)
                logger.success(f"代码迭代第 {idx} 轮完成")

            except Exception as e:
                logger.error(f"代码迭代第 {idx} 轮失败: {str(e)}")
                import traceback
                logger.debug(traceback.format_exc())

                round_result = {
                    'round': idx,
                    'url': schema_round.get('url'),
                    'error': str(e),
                    'success': False,
                }
                result['rounds'].append(round_result)

                if idx == 1:
                    # 第一轮失败则退出
                    return result

        # 设置最终解析器
        if current_parser_code:
            # 保存最终解析器
            final_parser_path = self.parsers_dir / "final_parser.py"
            with open(final_parser_path, 'w', encoding='utf-8') as f:
                f.write(current_parser_code)
            logger.success(f"最终解析器已保存: {final_parser_path}")

            result['final_parser'] = {
                'parser_path': str(final_parser_path),
                'code': current_parser_code,
                'config_path': None,  # 可以添加配置文件路径
                'config': final_schema,
            }
            result['success'] = True

        return result

    def _generate_parser_from_schema_phase(
        self,
        final_schema: Dict,
        first_schema_round: Dict
    ) -> Dict:
        """
        当代码迭代阶段没有URL时，使用Schema阶段的HTML生成解析器

        Args:
            final_schema: 最终Schema
            first_schema_round: Schema阶段的第一轮数据

        Returns:
            代码迭代结果
        """
        result = {
            'rounds': [],
            'parsers': [],
            'final_parser': None,
            'success': False,
        }

        try:
            logger.info("使用Schema阶段的第一个HTML生成解析器...")

            # 读取HTML内容
            html_path = first_schema_round.get('html_path')
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 生成解析器
            parser_result = generate_parser_code.invoke({
                "html_content": html_content,
                "target_json": final_schema,
                "output_dir": str(self.parsers_dir)
            })

            # 保存最终解析器
            final_parser_path = self.parsers_dir / "final_parser.py"
            with open(final_parser_path, 'w', encoding='utf-8') as f:
                f.write(parser_result['code'])
            logger.success(f"最终解析器已生成并保存: {final_parser_path}")

            # 设置最终解析器
            result['final_parser'] = {
                'parser_path': str(final_parser_path),
                'code': parser_result['code'],
                'config_path': None,
                'config': final_schema,
            }
            result['parsers'].append(parser_result)
            result['success'] = True

            return result

        except Exception as e:
            logger.error(f"从Schema阶段生成解析器失败: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return result

    def _generate_or_optimize_parser(
        self,
        html_content: str,
        target_json: Dict,
        round_num: int,
        previous_parser_code: str = None,
        parser_path: str = None
    ) -> Dict:
        """
        生成或优化解析代码

        第一轮：从0生成
        后续轮：基于前一轮的代码进行优化

        Args:
            html_content: 当前轮的HTML内容
            target_json: 当前合并的JSON Schema
            round_num: 轮次号
            previous_parser_code: 上一轮的解析代码
            parser_path: 上一轮的解析器文件路径

        Returns:
            生成/优化结果
        """
        if round_num == 1:
            # 第一轮：从0生成
            logger.info("  第一轮: 从0生成解析代码...")
            parser_result = generate_parser_code.invoke({
                "html_content": html_content,
                "target_json": target_json,
                "output_dir": str(self.parsers_dir)
            })
        else:
            # 后续轮：基于前一轮的代码进行优化
            logger.info(f"  第 {round_num} 轮: 基于前一轮代码优化...")
            parser_result = generate_parser_code.invoke({
                "html_content": html_content,
                "target_json": target_json,
                "output_dir": str(self.parsers_dir),
                "previous_parser_code": previous_parser_code,
                "previous_parser_path": parser_path,
                "round_num": round_num
            })

        return parser_result

    def _parse_all_html_with_final_parser(self, results: Dict, all_rounds: List[Dict]) -> None:
        """
        使用最终解析器解析所有HTML文件并生成JSON，保存到result目录

        Args:
            results: 执行结果
            all_rounds: 所有轮次数据（包含schema和code阶段）
        """
        final_parser_path = results['final_parser']['parser_path']

        try:
            # 加载最终解析器
            logger.info(f"  加载最终解析器: {final_parser_path}")
            parser = self._load_parser(final_parser_path)

            # 直接扫描html目录下的所有HTML文件
            html_files = sorted(self.html_dir.glob("*.html"))

            if not html_files:
                logger.warning("  html目录下没有找到HTML文件")
                return

            logger.info(f"  找到 {len(html_files)} 个HTML文件")

            # 遍历所有HTML文件
            for html_path in html_files:
                logger.info(f"  解析 {html_path.name}...")

                try:
                    # 读取HTML内容
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()

                    # 使用解析器解析HTML
                    parsed_data = parser.parse(html_content)

                    # 确定保存路径（基于原文件名），保存到result目录
                    json_filename = html_path.stem + '.json'
                    json_path = self.result_dir / json_filename

                    # 保存JSON
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed_data, f, ensure_ascii=False, indent=2)

                    logger.success(f"  ✓ JSON已保存: {json_path}")
                    logger.info(f"     提取了 {len(parsed_data)} 个字段")

                except Exception as e:
                    logger.error(f"  ✗ 解析 {html_path.name} 失败: {str(e)}")
                    import traceback
                    logger.debug(traceback.format_exc())

            logger.success(f"所有HTML解析完成，结果已保存到: {self.result_dir}")

        except Exception as e:
            logger.error(f"加载最终解析器失败: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())

    def _load_parser(self, parser_path: str):
        """动态加载解析器类"""
        spec = importlib.util.spec_from_file_location("parser_module", parser_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["parser_module"] = module
        spec.loader.exec_module(module)

        # 获取WebPageParser类
        if hasattr(module, 'WebPageParser'):
            return module.WebPageParser()
        else:
            raise Exception("解析器中未找到WebPageParser类")
