"""
Agent 执行器
负责执行具体的任务步骤
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from config.settings import settings
from tools import (
    get_html_from_file,  # 从本地文件读取HTML工具
    capture_html_file_screenshot,  # 渲染本地HTML并截图工具
    close_browser,  # 关闭浏览器实例
    generate_parser_code,  # 生成解析代码工具
    extract_schema_from_html,  # 从HTML提取Schema
    extract_schema_from_image,  # 从截图提取Schema
    merge_html_and_visual_schema,  # 合并单个HTML的两种Schema
    merge_multiple_schemas,  # 合并多个HTML的Schema
)
from tools.html_simplifier import simplify_html  # HTML精简工具


class AgentExecutor:
    """Agent执行器，负责执行具体任务"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        self.screenshots_dir = self.output_dir / "screenshots"
        self.parsers_dir = self.output_dir / "parsers"
        self.html_original_dir = self.output_dir / "html_original"  # 原始HTML
        self.html_simplified_dir = self.output_dir / "html_simplified"  # 精简HTML
        self.result_dir = self.output_dir / "result"
        self.schemas_dir = self.output_dir / "schemas"

        self.screenshots_dir.mkdir(exist_ok=True)
        self.parsers_dir.mkdir(exist_ok=True)
        self.html_original_dir.mkdir(exist_ok=True)
        self.html_simplified_dir.mkdir(exist_ok=True)
        self.result_dir.mkdir(exist_ok=True)
        self.schemas_dir.mkdir(exist_ok=True)

        logger.info(f"输出目录已创建：")
        logger.info(f"  - 原始HTML: {self.html_original_dir}")
        logger.info(f"  - 精简HTML: {self.html_simplified_dir}")
    
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

    def _simplify_html_file(self, html_file_path: str, idx: int) -> Dict:
        """
        读取并精简单个HTML文件

        Args:
            html_file_path: HTML文件路径
            idx: 轮次编号

        Returns:
            精简结果，包含HTML路径
        """
        result = {
            'success': False,
            'idx': idx,
            'html_file': html_file_path,
        }

        try:
            # 1. 读取HTML文件内容
            html_content = get_html_from_file.invoke({"file_path": html_file_path})

            # 保存原始HTML
            html_original_path = self.html_original_dir / f"schema_round_{idx}.html"
            with open(html_original_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # 2. 精简HTML
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
                logger.success(f"  [{idx}] ✓ 精简完成（{len(html_content)} → {len(simplified_html)} 字符，压缩 {compression_rate:.1f}%）")

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

    def _take_screenshot(self, html_data: Dict) -> Dict:
        """
        为已准备的HTML拍摄截图

        Args:
            html_data: 包含html_original_path的数据

        Returns:
            截图结果
        """
        idx = html_data['idx']
        result = {
            'success': False,
            'idx': idx,
        }

        try:
            html_original_path = html_data['html_original_path']
            screenshot_path = str(self.screenshots_dir / f"schema_round_{idx}.png")

            screenshot_result = capture_html_file_screenshot.invoke({
                "html_file_path": html_original_path,
                "save_path": screenshot_path
            })
            logger.success(f"  [{idx}] ✓ 截图完成")

            result.update({
                'success': True,
                'screenshot_path': screenshot_result,
            })

        except Exception as e:
            logger.error(f"  [{idx}] ✗ 截图失败: {str(e)}")
            result['error'] = str(e)

        return result

    def _extract_schemas_parallel(self, prepared_data: Dict) -> Dict:
        """
        并行提取单个HTML的两种Schema

        Args:
            prepared_data: 准备好的HTML数据

        Returns:
            包含html_schema和visual_schema的结果
        """
        idx = prepared_data['idx']
        result = {
            'success': False,
            'idx': idx,
        }

        try:
            html_content = prepared_data['html_content']
            screenshot_path = prepared_data['screenshot_path']

            # 并行提取HTML和视觉Schema
            with ThreadPoolExecutor(max_workers=2) as executor:
                logger.info(f"[提取阶段 {idx}] 并行提取HTML和视觉Schema...")

                future_html = executor.submit(
                    extract_schema_from_html.invoke,
                    {"html_content": html_content}
                )
                future_visual = executor.submit(
                    extract_schema_from_image.invoke,
                    {"image_path": screenshot_path}
                )

                html_schema = future_html.result()
                visual_schema = future_visual.result()

            logger.success(f"[提取阶段 {idx}] ✓ Schema提取完成（HTML: {len(html_schema)} 字段, 视觉: {len(visual_schema)} 字段）")

            # 保存schemas
            html_schema_path = self.schemas_dir / f"html_schema_round_{idx}.json"
            with open(html_schema_path, 'w', encoding='utf-8') as f:
                json.dump(html_schema, f, ensure_ascii=False, indent=2)

            visual_schema_path = self.schemas_dir / f"visual_schema_round_{idx}.json"
            with open(visual_schema_path, 'w', encoding='utf-8') as f:
                json.dump(visual_schema, f, ensure_ascii=False, indent=2)

            result.update({
                'success': True,
                'html_schema': html_schema,
                'visual_schema': visual_schema,
                'html_schema_path': str(html_schema_path),
                'visual_schema_path': str(visual_schema_path),
            })

        except Exception as e:
            logger.error(f"[提取阶段 {idx}] ✗ 失败: {str(e)}")
            result['error'] = str(e)

        return result

    def _merge_single_schema(self, extract_result: Dict) -> Dict:
        """
        合并单个HTML的两种Schema

        Args:
            extract_result: 提取结果

        Returns:
            合并后的Schema
        """
        idx = extract_result['idx']
        result = {
            'success': False,
            'idx': idx,
        }

        try:
            html_schema = extract_result['html_schema']
            visual_schema = extract_result['visual_schema']

            logger.info(f"[合并阶段 {idx}] 合并HTML和视觉Schema...")
            merged_schema = merge_html_and_visual_schema.invoke({
                "html_schema": html_schema,
                "visual_schema": visual_schema
            })
            logger.success(f"[合并阶段 {idx}] ✓ Schema已合并（{len(merged_schema)} 字段）")

            # 保存合并后的Schema
            merged_schema_path = self.schemas_dir / f"merged_schema_round_{idx}.json"
            with open(merged_schema_path, 'w', encoding='utf-8') as f:
                json.dump(merged_schema, f, ensure_ascii=False, indent=2)

            result.update({
                'success': True,
                'merged_schema': merged_schema,
                'merged_schema_path': str(merged_schema_path),
            })

        except Exception as e:
            logger.error(f"[合并阶段 {idx}] ✗ 失败: {str(e)}")
            result['error'] = str(e)

        return result

    def _execute_schema_iteration_phase(self, html_files: List[str]) -> Dict:
        """
        执行Schema迭代阶段（并行优化版本）

        5阶段流程：
        1a. 精简阶段：批量精简所有HTML（快速完成，提供进度反馈）
        1b. 截图阶段：串行截图所有HTML（避免浏览器冲突）
        2. 提取阶段：并行提取所有HTML和视觉Schema
        3. 合并阶段：并行合并每个HTML的两种Schema
        4. 最终合并：生成最终Schema

        Args:
            html_files: HTML文件路径列表

        Returns:
            Schema迭代结果
        """
        result = {
            'rounds': [],
            'final_schema': None,
            'success': False,
        }

        # ============ 阶段1a：批量精简所有HTML ============
        logger.info(f"\n{'═'*70}")
        logger.info(f"阶段1a/5: 批量精简HTML文件")
        logger.info(f"{'═'*70}")

        simplified_data_list = []
        for idx, html_file_path in enumerate(html_files, 1):
            logger.info(f"  正在精简 [{idx}/{len(html_files)}]: {Path(html_file_path).name}")
            simplified_data = self._simplify_html_file(html_file_path, idx)
            if simplified_data['success']:
                simplified_data_list.append(simplified_data)
            else:
                logger.error(f"HTML精简失败: {html_file_path}")
                if idx == 1:
                    return result

        if not simplified_data_list:
            logger.error("没有成功精简的HTML文件")
            return result

        logger.success(f"✓ 已精简 {len(simplified_data_list)} 个HTML文件")

        # ============ 阶段1b：批量截图所有HTML ============
        logger.info(f"\n{'═'*70}")
        logger.info(f"阶段1b/5: 批量截图HTML文件（串行，避免浏览器冲突）")
        logger.info(f"{'═'*70}")

        prepared_data_list = []
        for simplified_data in simplified_data_list:
            idx = simplified_data['idx']
            html_name = Path(simplified_data['html_file']).name
            logger.info(f"  正在截图 [{idx}/{len(simplified_data_list)}]: {html_name}")

            screenshot_data = self._take_screenshot(simplified_data)
            if screenshot_data['success']:
                # 合并数据
                combined_data = {**simplified_data, **screenshot_data}
                prepared_data_list.append(combined_data)
            else:
                logger.error(f"截图失败: {html_name}")
                if idx == 1:
                    return result

        if not prepared_data_list:
            logger.error("没有成功截图的HTML文件")
            return result

        logger.success(f"✓ 已截图 {len(prepared_data_list)} 个HTML文件")

        # 关闭浏览器实例（所有截图已完成）
        try:
            close_browser()
        except:
            pass

        # ============ 阶段2：并行提取所有Schema ============
        logger.info(f"\n{'═'*70}")
        logger.info(f"阶段2/5: 并行提取Schema（HTML + 视觉）")
        logger.info(f"  - 并发处理 {len(prepared_data_list)} 个HTML")
        logger.info(f"  - 每个HTML并行提取2种Schema（共 {len(prepared_data_list) * 2} 个API调用）")
        logger.info(f"  - 最大并发数: {min(settings.max_concurrent_extractions, len(prepared_data_list))}")
        logger.info(f"{'═'*70}")

        extract_results = []
        # 使用配置的并发数，避免API限流
        max_workers = min(settings.max_concurrent_extractions, len(prepared_data_list))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_data = {
                executor.submit(self._extract_schemas_parallel, data): data
                for data in prepared_data_list
            }

            for future in as_completed(future_to_data):
                extract_result = future.result()
                if extract_result['success']:
                    extract_results.append(extract_result)

        # 按idx排序
        extract_results.sort(key=lambda x: x['idx'])
        logger.success(f"✓ 已提取 {len(extract_results)} 个HTML的Schema")

        if not extract_results:
            logger.error("没有成功提取的Schema")
            return result

        # ============ 阶段3：并行合并每个HTML的两种Schema ============
        logger.info(f"\n{'═'*70}")
        logger.info(f"阶段3/5: 并行合并Schema（每个HTML的HTML+视觉Schema）")
        logger.info(f"  - 并发合并 {len(extract_results)} 个Schema")
        logger.info(f"  - 最大并发数: {min(settings.max_concurrent_merges, len(extract_results))}")
        logger.info(f"{'═'*70}")

        merge_results = []
        # 使用配置的并发数，避免API限流
        max_workers = min(settings.max_concurrent_merges, len(extract_results))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_extract = {
                executor.submit(self._merge_single_schema, extract_result): extract_result
                for extract_result in extract_results
            }

            for future in as_completed(future_to_extract):
                merge_result = future.result()
                if merge_result['success']:
                    merge_results.append(merge_result)

        # 按idx排序
        merge_results.sort(key=lambda x: x['idx'])
        logger.success(f"✓ 已合并 {len(merge_results)} 个Schema")

        if not merge_results:
            logger.error("没有成功合并的Schema")
            return result

        # ============ 构建轮次结果 ============
        all_merged_schemas = []
        for i, prepared in enumerate(prepared_data_list):
            idx = prepared['idx']
            html_file_path = prepared['html_file']

            # 查找对应的提取和合并结果
            extract_result = next((r for r in extract_results if r['idx'] == idx), None)
            merge_result = next((r for r in merge_results if r['idx'] == idx), None)

            if extract_result and merge_result:
                merged_schema = merge_result['merged_schema']
                all_merged_schemas.append(merged_schema)

                round_result = {
                    'round': idx,
                    'html_file': html_file_path,
                    'url': html_file_path,
                    'html_original_path': prepared['html_original_path'],
                    'html_path': prepared['html_path'],
                    'screenshot': prepared['screenshot_path'],
                    'html_schema': extract_result['html_schema'].copy(),
                    'html_schema_path': extract_result['html_schema_path'],
                    'visual_schema': extract_result['visual_schema'].copy(),
                    'visual_schema_path': extract_result['visual_schema_path'],
                    'merged_schema': merged_schema.copy(),
                    'merged_schema_path': merge_result['merged_schema_path'],
                    'schema': merged_schema.copy(),
                    'schema_path': merge_result['merged_schema_path'],
                    'groundtruth_schema': merged_schema.copy(),
                    'success': True,
                }
                result['rounds'].append(round_result)

        # ============ 阶段4：合并多个Schema，生成最终Schema ============
        if all_merged_schemas:
            logger.info(f"\n{'═'*70}")
            logger.info(f"阶段4/5: 生成最终Schema")
            logger.info(f"  - 合并 {len(all_merged_schemas)} 个Schema")
            logger.info(f"{'═'*70}")

            try:
                final_schema = merge_multiple_schemas.invoke({
                    "schemas": all_merged_schemas
                })
                logger.success(f"✓ 最终Schema已生成，包含 {len(final_schema)} 个字段")

                # 保存最终Schema
                final_schema_path = self.schemas_dir / "final_schema.json"
                with open(final_schema_path, 'w', encoding='utf-8') as f:
                    json.dump(final_schema, f, ensure_ascii=False, indent=2)
                logger.success(f"✓ 最终Schema已保存: {final_schema_path}")

                result['final_schema'] = final_schema
                result['final_schema_path'] = str(final_schema_path)
                result['success'] = True

            except Exception as e:
                logger.error(f"合并多个Schema失败: {str(e)}")
                import traceback
                logger.debug(traceback.format_exc())

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
                # 复用Schema阶段的HTML（精简后的）
                html_path = schema_round.get('html_path')
                html_original_path = schema_round.get('html_original_path')
                if not html_path:
                    logger.error(f"  ✗ Schema阶段第 {idx} 轮缺少HTML路径")
                    continue

                logger.info(f"  [1/2] 复用Schema阶段的精简HTML: {html_path}")
                if html_original_path:
                    logger.debug(f"    原始HTML位置: {html_original_path}")
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                logger.success(f"  ✓ 精简HTML已加载（长度: {len(html_content)} 字符）")

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
            final_parser_path = self.output_dir / "final_parser.py"
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

            # 扫描精简HTML目录下的所有HTML文件
            html_files = sorted(self.html_simplified_dir.glob("*.html"))

            if not html_files:
                logger.warning(f"  精简HTML目录下没有找到HTML文件: {self.html_simplified_dir}")
                # 尝试使用原始HTML目录
                html_files = sorted(self.html_original_dir.glob("*.html"))
                if html_files:
                    logger.info(f"  使用原始HTML目录: {self.html_original_dir}")
                else:
                    logger.error("  原始HTML目录也没有找到HTML文件")
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

    def parse_all_html_files(self, html_files: List[str], parser_path: str) -> Dict:
        """
        使用生成的解析器批量解析所有HTML文件

        Args:
            html_files: 所有HTML文件路径列表
            parser_path: 解析器文件路径

        Returns:
            批量解析结果
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"批量解析阶段：使用生成的解析器解析所有HTML文件")
        logger.info(f"{'='*70}")
        logger.info(f"总文件数: {len(html_files)}")
        logger.info(f"解析器路径: {parser_path}")

        results = {
            'success': True,
            'total_files': len(html_files),
            'parsed_files': [],
            'failed_files': [],
            'output_dir': str(self.result_dir),
        }

        try:
            # 加载解析器
            logger.info("\n加载解析器...")
            parser = self._load_parser(parser_path)
            logger.success("解析器加载成功")

            # 批量解析所有HTML文件
            logger.info(f"\n开始批量解析 {len(html_files)} 个HTML文件...")

            for i, html_file_path in enumerate(html_files, 1):
                html_path = Path(html_file_path)
                logger.info(f"\n[{i}/{len(html_files)}] 解析 {html_path.name}...")

                try:
                    # 读取HTML内容
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()

                    # 使用解析器解析HTML
                    parsed_data = parser.parse(html_content)

                    # 确定保存路径（基于原文件名）
                    json_filename = html_path.stem + '.json'
                    json_path = self.result_dir / json_filename

                    # 保存JSON
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed_data, f, ensure_ascii=False, indent=2)

                    logger.success(f"  ✓ 成功解析，JSON已保存: {json_path.name}")
                    logger.info(f"     提取了 {len(parsed_data)} 个字段")

                    results['parsed_files'].append({
                        'html_file': str(html_path),
                        'json_file': str(json_path),
                        'fields_count': len(parsed_data),
                    })

                except Exception as e:
                    logger.error(f"  ✗ 解析失败: {str(e)}")
                    results['failed_files'].append({
                        'html_file': str(html_path),
                        'error': str(e),
                    })
                    import traceback
                    logger.debug(traceback.format_exc())

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
