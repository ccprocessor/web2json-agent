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

    def create_plan(self, html_files: List[str], domain: str = None, layout_type: str = None) -> Dict:
        """
        创建解析任务计划

        Args:
            html_files: 待解析的HTML文件路径列表
            domain: 域名（可选）
            layout_type: 布局类型（可选，如：blog, article, product等）

        Returns:
            执行计划字典
        """
        logger.info(f"正在为 {len(html_files)} 个HTML文件创建执行计划...")

        # 如果没有提供域名，使用默认值
        if not domain:
            domain = "local_html_files"

        # 使用所有输入的HTML文件
        sample_files = html_files
        num_samples = len(html_files)

        # 构建标准执行计划
        plan = {
            'domain': domain,
            'layout_type': layout_type or 'unknown',
            'total_files': len(html_files),
            'sample_files': sample_files,  # HTML文件路径列表
            'sample_urls': sample_files,   # 为了兼容性，保留这个字段
            'num_samples': num_samples,
            'steps': [
                'read_html_file',       # 1. 读取HTML文件
                'capture_screenshot',   # 2. 渲染并截图
                'extract_schema',       # 3. 提取JSON Schema
                'generate_code',        # 4. 生成解析代码
            ],
        }

        logger.success(f"执行计划创建完成:")
        logger.info(f"  域名: {domain}")
        logger.info(f"  布局类型: {layout_type or '自动识别'}")
        logger.info(f"  HTML文件数量: {num_samples}")
        logger.info(f"  Schema迭代: {num_samples}轮")
        logger.info(f"  代码迭代: {num_samples}轮")
        logger.info(f"  执行步骤: {len(plan['steps'])} 个")

        return plan
