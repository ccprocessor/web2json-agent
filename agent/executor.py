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
        执行计划
        
        Args:
            plan: 执行计划
        
        Returns:
            执行结果
        """
        logger.info("开始执行计划...")
        
        results = {
            'plan': plan,
            'samples': [],
            'final_parser': None,
            'success': False,
        }
        
        # 处理每个样本URL
        for idx, url in enumerate(plan['sample_urls'], 1):
            logger.info(f"处理样本 {idx}/{len(plan['sample_urls'])}: {url}")
            
            try:
                sample_result = self._process_url(url, idx)
                results['samples'].append(sample_result)
            except Exception as e:
                logger.error(f"处理URL失败: {str(e)}")
                results['samples'].append({
                    'url': url,
                    'error': str(e),
                    'success': False
                })
        
        # 生成最终的解析器
        if results['samples']:
            results['final_parser'] = self._generate_final_parser(results['samples'], plan)
            results['success'] = results['final_parser'] is not None
        
        return results
    
    def _process_url(self, url: str, idx: int) -> Dict:
        """处理单个URL"""
        result = {
            'url': url,
            'html': None,
            'screenshot': None,
            'schema': None,
            'success': False,
        }
        
        try:
            # 1. 获取HTML源码
            logger.info("  [1/3] 获取HTML源码...")
            result['html'] = get_webpage_source.invoke({"url": url})

            # 2. 截图
            logger.info("  [2/3] 截图...")
            screenshot_path = str(self.screenshots_dir / f"sample_{idx}.png")
            result['screenshot'] = capture_webpage_screenshot.invoke({
                "url": url,
                "save_path": screenshot_path
            })

            # 3. 提取JSON Schema
            logger.info("  [3/3] 提取JSON Schema...")
            result['schema'] = extract_json_from_image.invoke({
                "image_path": result['screenshot']
            })

            result['success'] = True
            logger.success(f"  样本处理完成")
            
        except Exception as e:
            logger.error(f"  处理失败: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def _generate_final_parser(self, samples: List[Dict], plan: Dict) -> Dict:
        """生成最终的解析器"""
        logger.info("生成最终解析器...")

        # 获取所有成功的样本
        successful_samples = [s for s in samples if s.get('success')]

        if not successful_samples:
            logger.error("没有成功的样本，无法生成解析器")
            return None

        logger.info(f"成功处理 {len(successful_samples)}/{len(samples)} 个样本")

        try:
            # 合并所有样本的schema
            merged_schema = self._merge_schemas(successful_samples)
            logger.info(f"合并后的Schema包含 {len(merged_schema)} 个字段")

            # 使用第一个样本的HTML作为参考
            reference_html = successful_samples[0]['html']

            # 生成解析代码 - 使用 .invoke() 调用工具
            parser_result = generate_parser_code.invoke({
                "html_content": reference_html,
                "target_json": merged_schema,
                "output_dir": str(self.parsers_dir)
            })

            logger.success(f"解析器生成完成: {parser_result['parser_path']}")
            return parser_result

        except Exception as e:
            logger.error(f"生成解析器失败: {str(e)}")
            return None

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

