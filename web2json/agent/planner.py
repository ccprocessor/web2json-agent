"""
Agent 规划器
负责分析任务并生成执行计划（简化版，无需 LLM）
"""
from typing import List, Dict
from pathlib import Path
from loguru import logger
from web2json.config.settings import settings


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
            'phases': [
                'schema_phase',     # 阶段1: Schema迭代 - HTML处理 + Schema提取/补充 + 合并
                'code_phase',       # 阶段2: 代码迭代 - 代码生成和优化
                'parse_phase',      # 阶段3: 批量解析 - 使用最终解析器解析所有HTML
            ],
            'steps': [
                # Schema 阶段步骤
                'simplify_html',        # 1. 读取并精简HTML文件
                'extract_schema',       # 2. 提取/补充Schema
                'merge_schema',         # 3. 合并多个Schema
                # Code 阶段步骤
                'generate_parser',      # 4. 生成解析器代码
                'optimize_parser',      # 5. 优化解析器代码
                # Parse 阶段步骤
                'batch_parse',          # 6. 批量解析所有HTML
            ],
        }

        logger.success(f"执行计划创建完成: 域名={domain}, 总文件={len(html_files)}, 学习样本={num_samples}, 迭代={num_samples}轮, 批量解析={len(html_files)}个")

        return plan
