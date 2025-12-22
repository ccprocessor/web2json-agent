"""
Agent 规划器
负责分析任务并生成执行计划（简化版，无需 LLM）
"""
from typing import List, Dict
from pathlib import Path
from loguru import logger
from config.settings import settings


class AgentPlanner:
    """Agent规划器，负责任务分析和计划生成"""

    def __init__(self):
        """初始化规划器（不再需要 LLM）"""
        pass

    def create_plan(self, html_files: List[str], domain: str = None, iteration_rounds: int = None) -> Dict:
        """
        创建解析任务计划

        Args:
            html_files: 待解析的HTML文件路径列表
            domain: 域名（可选）
            iteration_rounds: 迭代轮数（用于Schema学习的样本数量），默认使用配置值

        Returns:
            执行计划字典
        """
        logger.info(f"正在为 {len(html_files)} 个HTML文件创建执行计划...")

        # 如果没有提供域名，使用默认值
        if not domain:
            domain = "local_html_files"

        # 如果没有指定迭代轮数，使用配置中的默认值
        if iteration_rounds is None:
            iteration_rounds = settings.default_iteration_rounds

        # 确保迭代轮数不超过总文件数
        iteration_rounds = min(iteration_rounds, len(html_files))

        # 选择用于迭代学习的样本（前N个）
        sample_files = html_files[:iteration_rounds]
        num_samples = len(sample_files)

        # 构建标准执行计划
        plan = {
            'domain': domain,
            'total_files': len(html_files),
            'all_html_files': html_files,  # 所有HTML文件（用于后续批量解析）
            'sample_files': sample_files,  # 用于迭代学习的样本
            'sample_urls': sample_files,   # 为了兼容性，保留这个字段
            'num_samples': num_samples,
            'iteration_rounds': iteration_rounds,
            'steps': [
                'read_html_file',       # 1. 读取HTML文件
                'capture_screenshot',   # 2. 渲染并截图
                'extract_schema',       # 3. 提取JSON Schema
                'generate_code',        # 4. 生成解析代码
                'parse_all_html',       # 5. 使用生成的解析器解析所有HTML
            ],
        }

        logger.success(f"执行计划创建完成:")
        logger.info(f"  域名: {domain}")
        logger.info(f"  总HTML文件数量: {len(html_files)}")
        logger.info(f"  迭代学习样本数量: {num_samples}")
        logger.info(f"  Schema迭代: {num_samples}轮")
        logger.info(f"  代码迭代: {num_samples}轮")
        logger.info(f"  批量解析数量: {len(html_files)}个")
        logger.info(f"  执行步骤: {len(plan['steps'])} 个")

        return plan
