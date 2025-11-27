"""
Agent 规划器
负责分析任务并生成执行计划（简化版，无需 LLM）
"""
from typing import List, Dict
from urllib.parse import urlparse
from loguru import logger
from config.settings import settings


class AgentPlanner:
    """Agent规划器，负责任务分析和计划生成"""

    def __init__(self):
        """初始化规划器（不再需要 LLM）"""
        pass

    def create_plan(self, urls: List[str], domain: str = None, layout_type: str = None) -> Dict:
        """
        创建解析任务计划

        Args:
            urls: 待解析的URL列表
            domain: 域名（可选）
            layout_type: 布局类型（可选，如：blog, article, product等）

        Returns:
            执行计划字典
        """
        logger.info(f"正在为 {len(urls)} 个URL创建执行计划...")

        # 自动推断域名
        if not domain and urls:
            domain = self._extract_domain(urls[0])

        # 选择样本URL（最多3个，确保至少2个）
        num_samples = max(min(len(urls), 3), min(len(urls), settings.min_sample_size))
        sample_urls = urls[:num_samples]

        # 构建标准执行计划
        plan = {
            'domain': domain,
            'layout_type': layout_type or 'unknown',
            'total_urls': len(urls),
            'sample_urls': sample_urls,
            'num_samples': num_samples,
            'steps': [
                'fetch_html',           # 1. 获取HTML源码
                'capture_screenshot',   # 2. 截图
                'extract_schema',       # 3. 提取JSON Schema
                'generate_code',        # 4. 生成解析代码
                'validate_code',        # 5. 验证代码
            ],
            'max_iterations': settings.max_iterations,
            'success_threshold': settings.success_threshold,
        }

        logger.success(f"执行计划创建完成:")
        logger.info(f"  域名: {domain}")
        logger.info(f"  布局类型: {layout_type or '自动识别'}")
        logger.info(f"  总URL数: {len(urls)}")
        logger.info(f"  样本URL数: {num_samples}")
        logger.info(f"  执行步骤: {len(plan['steps'])} 个")
        logger.info(f"  最大迭代次数: {plan['max_iterations']}")
        logger.info(f"  成功率阈值: {plan['success_threshold']:.0%}")

        return plan

    def _extract_domain(self, url: str) -> str:
        """从URL中提取域名"""
        parsed = urlparse(url)
        return parsed.netloc
