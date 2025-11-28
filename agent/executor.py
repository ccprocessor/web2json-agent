"""
Agent 执行器
负责执行具体的任务步骤
"""
import json
import sys
import importlib.util
from typing import Dict, List
from pathlib import Path
from loguru import logger
from tools import (
    get_webpage_source,  # 获取网页源码工具
    capture_webpage_screenshot, # 截图工具
    extract_json_from_image, # 提取JSON Schema工具
    refine_schema_from_image, # Schema迭代优化工具
    generate_parser_code, # 生成解析代码工具
)
from config.settings import settings


class AgentExecutor:
    """Agent执行器，负责执行具体任务"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        self.screenshots_dir = self.output_dir / "screenshots"
        self.parsers_dir = self.output_dir / "parsers"
        self.html_dir = self.output_dir / "html"
        self.json_dir = self.output_dir / "json"
        self.schemas_dir = self.output_dir / "schemas"

        self.screenshots_dir.mkdir(exist_ok=True)
        self.parsers_dir.mkdir(exist_ok=True)
        self.html_dir.mkdir(exist_ok=True)
        self.json_dir.mkdir(exist_ok=True)
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

        # 获取配置的URL数量
        schema_url_count = settings.schema_iteration_url_count
        code_url_count = settings.code_iteration_url_count
        sample_urls = plan['sample_urls']

        # 验证URL数量足够
        total_urls_needed = schema_url_count + code_url_count
        if len(sample_urls) < total_urls_needed:
            logger.warning(f"URL数量不足：需要{total_urls_needed}个，实际{len(sample_urls)}个")
            schema_url_count = min(schema_url_count, len(sample_urls))
            code_url_count = max(0, len(sample_urls) - schema_url_count)

        # 阶段1: Schema迭代
        logger.info(f"\n{'='*70}")
        logger.info(f"阶段1: Schema迭代（使用前 {schema_url_count} 个URL）")
        logger.info(f"{'='*70}")

        schema_urls = sample_urls[:schema_url_count]
        schema_result = self._execute_schema_iteration_phase(schema_urls)
        results['schema_phase'] = schema_result

        if not schema_result['success']:
            logger.error("Schema迭代阶段失败")
            return results

        final_schema = schema_result['final_schema']
        logger.success(f"Schema迭代完成，最终Schema包含 {len(final_schema)} 个字段")

        # 阶段2: 代码迭代
        logger.info(f"\n{'='*70}")
        logger.info(f"阶段2: 代码迭代（使用后 {code_url_count} 个URL）")
        logger.info(f"{'='*70}")

        code_urls = sample_urls[schema_url_count:schema_url_count + code_url_count]
        code_result = self._execute_code_iteration_phase(
            code_urls,
            final_schema,
            schema_result['rounds']  # 传递schema阶段的数据用于后续验证
        )
        results['code_phase'] = code_result

        if code_result['success']:
            results['final_parser'] = code_result['final_parser']
            results['success'] = True

            # 使用最终解析器解析所有HTML并生成JSON
            logger.info(f"\n{'='*70}")
            logger.info("使用最终解析器解析所有HTML")
            logger.info(f"{'='*70}")
            all_rounds = schema_result['rounds'] + code_result['rounds']
            self._parse_all_html_with_final_parser(results, all_rounds)
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

        第一轮：基于最终Schema生成初始解析代码
        后续轮：基于验证结果优化代码

        Args:
            urls: URL列表
            final_schema: 来自Schema迭代阶段的最终Schema
            schema_phase_rounds: Schema阶段的轮次数据

        Returns:
            代码迭代结果
        """
        result = {
            'rounds': [],
            'parsers': [],
            'final_parser': None,
            'success': False,
        }

        # 如果没有分配URL，使用Schema阶段的第一个HTML生成代码
        if not urls:
            logger.warning("代码迭代阶段没有分配URL，将使用Schema阶段的第一个HTML生成解析器")
            if schema_phase_rounds and schema_phase_rounds[0].get('success'):
                return self._generate_parser_from_schema_phase(final_schema, schema_phase_rounds[0])
            else:
                logger.error("Schema阶段没有可用的HTML数据")
                return result

        current_parser_code = None
        current_parser_path = None

        for idx, url in enumerate(urls, 1):
            logger.info(f"\n{'─'*70}")
            logger.info(f"代码迭代 - 第 {idx}/{len(urls)} 轮")
            logger.info(f"{'─'*70}")

            try:
                # 1. 获取HTML源码
                logger.info(f"  [1/4] 获取HTML源码...")
                html_content = get_webpage_source.invoke({"url": url})
                logger.success(f"  ✓ HTML源码已获取")

                # 保存HTML源码
                html_path = self.html_dir / f"code_round_{idx}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.success(f"  ✓ HTML已保存: {html_path}")

                # 2. 截图（用于groundtruth）
                logger.info(f"  [2/4] 截图...")
                screenshot_path = str(self.screenshots_dir / f"code_round_{idx}.png")
                screenshot_result = capture_webpage_screenshot.invoke({
                    "url": url,
                    "save_path": screenshot_path
                })
                logger.success(f"  ✓ 截图已保存: {screenshot_path}")

                # 3. 提取groundtruth（用于后续验证）
                logger.info(f"  [3/4] 提取groundtruth...")
                groundtruth_schema = extract_json_from_image.invoke({
                    "image_path": screenshot_result
                })
                logger.success(f"  ✓ Groundtruth已提取")

                # 4. 生成或优化解析代码
                if idx == 1:
                    logger.info(f"  [4/4] 生成初始解析代码...")
                    parser_result = generate_parser_code.invoke({
                        "html_content": html_content,
                        "target_json": final_schema,
                        "output_dir": str(self.parsers_dir)
                    })
                    logger.success(f"  ✓ 初始解析代码已生成")
                else:
                    logger.info(f"  [4/4] 优化解析代码（基于上一轮）...")
                    parser_result = generate_parser_code.invoke({
                        "html_content": html_content,
                        "target_json": final_schema,
                        "output_dir": str(self.parsers_dir),
                        "previous_parser_code": current_parser_code,
                        "previous_parser_path": current_parser_path,
                        "round_num": idx
                    })
                    logger.success(f"  ✓ 解析代码已优化")

                # 5. 保存解析器代码
                code_parser_path = self.parsers_dir / f"code_round_{idx}.py"
                with open(code_parser_path, 'w', encoding='utf-8') as f:
                    f.write(parser_result['code'])
                logger.success(f"  ✓ 解析器已保存: {code_parser_path}")

                # 更新当前解析器
                current_parser_code = parser_result['code']
                current_parser_path = str(code_parser_path)
                parser_result['parser_path'] = current_parser_path

                # 记录本轮结果
                round_result = {
                    'round': idx,
                    'url': url,
                    'html': html_content,
                    'html_path': str(html_path),
                    'screenshot': screenshot_result,
                    'groundtruth_schema': groundtruth_schema,
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
                    'url': url,
                    'error': str(e),
                    'success': False,
                }
                result['rounds'].append(round_result)

                if idx == 1:
                    # 第一轮失败则退出
                    return result

        # 设置最终解析器
        if current_parser_code:
            result['final_parser'] = {
                'parser_path': current_parser_path,
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

            # 保存解析器代码
            parser_path = self.parsers_dir / "generated_parser.py"
            with open(parser_path, 'w', encoding='utf-8') as f:
                f.write(parser_result['code'])
            logger.success(f"解析器已生成并保存: {parser_path}")

            # 设置最终解析器
            result['final_parser'] = {
                'parser_path': str(parser_path),
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

    def _execute_round(
        self,
        url: str,
        round_num: int,
        merged_schema: Dict,
        previous_parser_code: str = None,
        parser_path: str = None
    ) -> Dict:
        """
        执行单一轮次

        Args:
            url: 处理的URL
            round_num: 轮次号
            merged_schema: 之前合并的schema
            previous_parser_code: 上一轮的解析代码
            parser_path: 上一轮的解析器路径

        Returns:
            轮次结果
        """
        result = {
            'round': round_num,
            'url': url,
            'html': None,
            'screenshot': None,
            'schema': None,
            'merged_schema': merged_schema,
            'parser_path': None,
            'parser_code': None,
            'parser_result': None,
            'groundtruth_schema': None,
            'success': False,
        }
        
        try:
            # 1. 获取HTML源码
            logger.info(f"  [1/5] 获取HTML源码...")
            result['html'] = get_webpage_source.invoke({"url": url})
            logger.success(f"  ✓ HTML源码已获取")

            # 保存HTML源码
            html_path = self.html_dir / f"round_{round_num}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(result['html'])
            result['html_path'] = str(html_path)
            logger.success(f"  ✓ HTML已保存: {html_path}")

            # 2. 截图
            logger.info(f"  [2/5] 截图...")
            screenshot_path = str(self.screenshots_dir / f"round_{round_num}.png")
            result['screenshot'] = capture_webpage_screenshot.invoke({
                "url": url,
                "save_path": screenshot_path
            })
            logger.success(f"  ✓ 截图已保存: {screenshot_path}")

            # 3. 提取JSON Schema（作为groundtruth）
            logger.info(f"  [3/5] 提取JSON Schema...")
            this_round_schema = extract_json_from_image.invoke({
                "image_path": result['screenshot']
            })
            result['schema'] = this_round_schema
            result['groundtruth_schema'] = this_round_schema
            logger.success(f"  ✓ JSON Schema已提取，包含 {len(this_round_schema)} 个字段")

            # 合并schema（第一轮直接使用，后续轮合并）
            if round_num == 1:
                result['merged_schema'] = this_round_schema
                logger.info(f"  第一轮: 直接使用新schema")
            else:
                result['merged_schema'] = self._merge_schemas_incremental(
                    merged_schema,
                    this_round_schema
                )
                logger.info(f"  第 {round_num} 轮: 合并schema，现共 {len(result['merged_schema'])} 个字段")

            # 4. 生成/优化解析代码
            logger.info(f"  [4/5] 生成/优化解析代码...")
            parser_result = self._generate_or_optimize_parser(
                html_content=result['html'],
                target_json=result['merged_schema'],
                round_num=round_num,
                previous_parser_code=previous_parser_code,
                parser_path=parser_path
            )
            logger.success(f"  ✓ 解析代码已生成/优化")

            # 5. 保存解析器代码
            logger.info(f"  [5/5] 保存解析器...")
            round_parser_path = self.parsers_dir / f"round_{round_num}.py"
            with open(round_parser_path, 'w', encoding='utf-8') as f:
                f.write(parser_result['code'])
            logger.success(f"  ✓ 解析器已保存: {round_parser_path}")

            result['parser_path'] = str(round_parser_path)
            result['parser_code'] = parser_result['code']
            result['parser_result'] = parser_result
            result['parser_result']['parser_path'] = str(round_parser_path)  # 更新路径
            result['success'] = True

            logger.success(f"第 {round_num} 轮处理完成")

        except Exception as e:
            logger.error(f"第 {round_num} 轮处理失败: {str(e)}")
            result['error'] = str(e)
            import traceback
            result['traceback'] = traceback.format_exc()

        return result
    
    def _merge_schemas_incremental(self, old_schema: Dict, new_schema: Dict) -> Dict:
        """
        增量合并Schema

        策略：
        1. 保留所有旧schema中的字段
        2. 添加新schema中的新字段
        3. 对于重复的字段，合并字段信息
        """
        if not old_schema:
            return new_schema.copy()

        merged = old_schema.copy()

        for field_name, field_data in new_schema.items():
            if field_name not in merged:
                # 新字段
                merged[field_name] = field_data.copy()
                msg = f"  + 新增字段: {field_name}"
                logger.debug(msg)
                print(msg)  # 同时打印到控制台
            else:
                # 现有字段，更新信息
                existing = merged[field_name]
                # 保留现有的类型、描述等，但可以根据需要更新
                if 'description' in field_data and 'description' not in existing:
                    existing['description'] = field_data['description']
                msg = f"  ~ 更新字段: {field_name}"
                logger.debug(msg)
                print(msg)  # 同时打印到控制台

        return merged

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

    def _merge_schemas(self, samples: List[Dict]) -> Dict:
        """
        合并多个样本的Schema，提取公共字段

        策略：
        1. 统计每个字段在所有样本中出现的次数
        2. 出现在50%以上样本中的字段被认为是必需字段
        3. 其他字段标记为可选字段
        """
        if len(samples) == 1:
            return samples[0]['schema']

        logger.info(f"合并 {len(samples)} 个样本的Schema...")

        # 统计字段出现次数
        field_counts = {}
        field_info = {}

        for sample in samples:
            schema = sample.get('schema', {})
            for field_name, field_data in schema.items():
                if field_name not in field_counts:
                    field_counts[field_name] = 0
                    field_info[field_name] = field_data
                field_counts[field_name] += 1

        # 计算阈值（50%）
        threshold = len(samples) * 0.5

        # 构建合并后的Schema
        merged_schema = {}
        for field_name, count in field_counts.items():
            field_data = field_info[field_name].copy()

            # 标记字段是否为必需
            if count >= threshold:
                field_data['required'] = True
                field_data['frequency'] = f"{count}/{len(samples)}"
                merged_schema[field_name] = field_data
                logger.debug(f"  必需字段: {field_name} (出现 {count}/{len(samples)} 次)")
            else:
                field_data['required'] = False
                field_data['frequency'] = f"{count}/{len(samples)}"
                merged_schema[field_name] = field_data
                logger.debug(f"  可选字段: {field_name} (出现 {count}/{len(samples)} 次)")

        return merged_schema

    def _parse_all_html_with_final_parser(self, results: Dict, all_rounds: List[Dict]) -> None:
        """
        使用最终解析器解析所有HTML文件并生成JSON

        Args:
            results: 执行结果
            all_rounds: 所有轮次数据（包含schema和code阶段）
        """
        final_parser_path = results['final_parser']['parser_path']

        try:
            # 加载最终解析器
            logger.info(f"  加载最终解析器: {final_parser_path}")
            parser = self._load_parser(final_parser_path)

            # 遍历所有轮次的HTML
            for round_result in all_rounds:
                if not round_result.get('success'):
                    continue

                round_num = round_result['round']
                html_path = round_result.get('html_path')

                if not html_path:
                    logger.warning(f"  轮次 {round_num} 没有HTML路径，跳过")
                    continue

                # 读取HTML内容
                try:
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                except Exception as e:
                    logger.warning(f"  读取 {html_path} 失败: {e}")
                    continue

                logger.info(f"  解析轮次 {round_num} 的HTML...")

                try:
                    # 使用解析器解析HTML
                    parsed_data = parser.parse(html_content)

                    # 确定保存路径（基于原文件名）
                    json_filename = Path(html_path).stem + '.json'
                    json_path = self.json_dir / json_filename

                    # 保存JSON
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed_data, f, ensure_ascii=False, indent=2)

                    logger.success(f"  ✓ JSON已保存: {json_path}")
                    logger.info(f"     提取了 {len(parsed_data)} 个字段")

                    # 将JSON路径添加到结果中
                    round_result['json_path'] = str(json_path)
                    round_result['parsed_data'] = parsed_data

                except Exception as e:
                    logger.error(f"  ✗ 轮次 {round_num} 解析失败: {str(e)}")
                    import traceback
                    logger.debug(traceback.format_exc())

            logger.success("所有HTML解析完成")

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
