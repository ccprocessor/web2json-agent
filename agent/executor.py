"""
Agent 执行器
负责执行具体的任务步骤
"""
from typing import Dict, List
from pathlib import Path
from loguru import logger
from tools import (
    get_webpage_source,  # 获取网页源码工具
    capture_webpage_screenshot, # 截图工具
    extract_json_from_image, # 提取JSON Schema工具
    generate_parser_code, # 生成解析代码工具
)


class AgentExecutor:
    """Agent执行器，负责执行具体任务"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.screenshots_dir = self.output_dir / "screenshots"
        self.parsers_dir = self.output_dir / "parsers"
        self.screenshots_dir.mkdir(exist_ok=True)
        self.parsers_dir.mkdir(exist_ok=True)
    
    def execute_plan(self, plan: Dict) -> Dict:
        """
        执行计划 - 多轮迭代执行

        第一轮：获取HTML -> 截图 -> 提取JSON Schema -> 生成解析代码
        后续轮：获取HTML -> 截图 -> 合并JSON Schema -> 优化解析代码

        Args:
            plan: 执行计划
        
        Returns:
            执行结果
        """
        logger.info("开始执行计划...")
        
        results = {
            'plan': plan,
            'rounds': [],  # 每一轮的结果
            'final_parser': None,
            'success': False,
        }
        
        # 初始化
        merged_schema = {}
        current_parser_code = None
        parser_path = None

        # 多轮执行
        max_rounds = len(plan['sample_urls'])
        for round_num in range(1, max_rounds + 1):
            logger.info(f"\n{'='*70}")
            logger.info(f"第 {round_num} 轮处理")
            logger.info(f"{'='*70}")

            url = plan['sample_urls'][round_num - 1]
            round_result = self._execute_round(
                url=url,
                round_num=round_num,
                merged_schema=merged_schema,
                previous_parser_code=current_parser_code,
                parser_path=parser_path
            )

            results['rounds'].append(round_result)

            if round_result['success']:
                # 更新合并的schema
                merged_schema = round_result['merged_schema']
                current_parser_code = round_result['parser_code']
                parser_path = round_result['parser_path']
                results['final_parser'] = round_result['parser_result']
                results['success'] = True
            else:
                logger.error(f"第 {round_num} 轮处理失败")
                if round_num == 1:
                    # 第一轮失败则退出
                    break

        return results
    
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
            logger.info(f"  [1/4] 获取HTML源码...")
            result['html'] = get_webpage_source.invoke({"url": url})
            logger.success(f"  ✓ HTML源码已获取")

            # 2. 截图
            logger.info(f"  [2/4] 截图...")
            screenshot_path = str(self.screenshots_dir / f"round_{round_num}.png")
            result['screenshot'] = capture_webpage_screenshot.invoke({
                "url": url,
                "save_path": screenshot_path
            })
            logger.success(f"  ✓ 截图已保存: {screenshot_path}")

            # 3. 提取JSON Schema（作为groundtruth）
            logger.info(f"  [3/4] 提取JSON Schema...")
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
            logger.info(f"  [4/4] 生成/优化解析代码...")
            parser_result = self._generate_or_optimize_parser(
                html_content=result['html'],
                target_json=result['merged_schema'],
                round_num=round_num,
                previous_parser_code=previous_parser_code,
                parser_path=parser_path
            )

            result['parser_path'] = parser_result['parser_path']
            result['parser_code'] = parser_result['code']
            result['parser_result'] = parser_result
            result['success'] = True
            logger.success(f"  ✓ 解析代码已生成/优化")
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
                logger.debug(f"  + 新增字段: {field_name}")
            else:
                # 现有字段，更新信息
                existing = merged[field_name]
                # 保留现有的类型、描述等，但可以根据需要更新
                if 'description' in field_data and 'description' not in existing:
                    existing['description'] = field_data['description']
                logger.debug(f"  ~ 更新字段: {field_name}")

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

