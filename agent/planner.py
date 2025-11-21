"""
Agent 规划器
负责分析任务并生成执行计划
"""
import os
from typing import List, Dict
from loguru import logger
from langchain_openai import ChatOpenAI
from config.settings import settings


class AgentPlanner:
    """Agent规划器，负责任务分析和计划生成"""

    def __init__(self):
        # 使用 LangChain 1.0 的 ChatOpenAI
        self.llm = ChatOpenAI(
            model=settings.agent_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            temperature=settings.agent_temperature
        )
    
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
        
        # 构建规划提示词
        prompt = self._build_planning_prompt(urls, domain, layout_type)

        # 调用LLM生成计划 - 使用 LangChain 1.0 的 invoke
        messages = [
            {"role": "system", "content": "你是一个专业的网页解析任务规划助手。"},
            {"role": "user", "content": prompt}
        ]
        response = self.llm.invoke(messages)
        
        # 解析计划
        plan = self._parse_plan(response.content, urls, domain, layout_type)
        
        logger.success(f"执行计划创建完成: {plan['steps']} 个步骤")
        return plan
    
    def _extract_domain(self, url: str) -> str:
        """从URL中提取域名"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def _build_planning_prompt(self, urls: List[str], domain: str, layout_type: str) -> str:
        """构建规划提示词"""
        urls_text = "\n".join([f"- {url}" for url in urls[:5]])  # 最多显示5个
        
        prompt = f"""
你需要为以下网页解析任务创建执行计划：

域名: {domain or '未指定'}
布局类型: {layout_type or '未指定'}
URL数量: {len(urls)}
示例URL:
{urls_text}

任务目标：
生成一个Python解析器，能够从这些URL中提取结构化数据。

请分析这些URL，并制定执行计划。计划应包括：
1. 需要处理的URL数量（建议从1-3个样本开始）
2. 每个URL需要执行的步骤（获取源码、截图、提取JSON、生成代码）
3. 验证策略（如何验证生成的代码是否正确）
4. 迭代优化策略（如果初次生成的代码不够好，如何改进）

请以简洁的文本形式返回计划，不要使用JSON格式。
"""
        return prompt
    
    def _parse_plan(self, response: str, urls: List[str], domain: str, layout_type: str) -> Dict:
        """解析LLM返回的计划"""
        # 简化版：直接创建标准计划
        # 实际应用中可以让LLM返回结构化的计划
        
        # 选择样本URL（最多3个）
        sample_urls = urls[:min(3, len(urls))]
        
        plan = {
            'domain': domain,
            'layout_type': layout_type or 'unknown',
            'total_urls': len(urls),
            'sample_urls': sample_urls,
            'steps': [
                'fetch_html',      # 获取HTML源码
                'capture_screenshot',  # 截图
                'extract_schema',  # 提取JSON Schema
                'generate_code',   # 生成解析代码
                'validate_code',   # 验证代码
            ],
            'llm_analysis': response,
            'max_iterations': settings.max_iterations,
            'success_threshold': settings.success_threshold,
        }
        
        return plan

