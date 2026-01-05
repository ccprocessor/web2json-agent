"""
LLM客户端封装 - 使用 LangChain 1.0
支持基于场景的模型配置和 Token 追踪
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

import tiktoken
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from loguru import logger
from web2json.config.settings import settings

# 加载项目根目录的 .env 文件
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

# 验证
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(f".env 文件路径: {env_path}, API Key未加载")

# 定义场景类型
ScenarioType = Literal["default", "code_gen", "agent"]


class LLMClient:
    """LLM客户端封装类 - 基于 LangChain 1.0

    支持多种使用方式：
    1. 直接初始化：LLMClient(model="gpt-4")
    2. 从Settings创建：LLMClient.from_settings(settings)
    3. 按场景创建：LLMClient.for_scenario("code_gen")
    
    使用单例模式，同一配置的客户端会共享 token 统计
    """
    
    # 类级别的 token 统计（跨所有实例共享）
    _global_total_input_tokens = 0
    _global_total_completion_tokens = 0
    _global_total_tokens = 0
    _global_request_count = 0
    
    # 单例字典，按 (model, api_base) 作为键
    _instances: Dict[tuple, "LLMClient"] = {}

    def __new__(cls, api_key: Optional[str] = None, api_base: Optional[str] = None,
                model: Optional[str] = None, temperature: float = 0.3):
        """使用单例模式，确保相同配置的客户端共享实例"""
        # 获取实际的配置值（优先使用settings）
        actual_api_base = api_base or settings.openai_api_base
        actual_model = model or settings.default_model

        # 使用 (model, api_base) 作为键
        instance_key = (actual_model, actual_api_base)

        if instance_key not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[instance_key] = instance
            instance._initialized = False  # 标记是否已初始化

        return cls._instances[instance_key]

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3
    ):
        """初始化LLM客户端

        Args:
            api_key: API密钥
            api_base: API基础URL
            model: 模型名称
            temperature: 温度参数
        """
        # 避免重复初始化
        if self._initialized:
            return

        self.api_key = api_key or settings.openai_api_key
        self.api_base = api_base or settings.openai_api_base
        self.model = model or settings.default_model
        self.temperature = temperature

        # 初始化 tokenizer 用于本地 token 计数
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # 如果模型不在 tiktoken 的预设中，使用 cl100k_base 作为默认
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # 使用 LangChain 1.0 的 ChatOpenAI（兼容所有模型）
        self.client = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.api_base,
            temperature=self.temperature
        )

        self._initialized = True
        logger.info(f"LLM客户端初始化完成 - 模型: {self.model}, Base: {self.api_base}")

    @classmethod
    def from_settings(cls, settings, model: Optional[str] = None, temperature: Optional[float] = None):
        """从Settings对象创建LLMClient

        Args:
            settings: Settings配置对象
            model: 可选的模型名称覆盖
            temperature: 可选的温度参数覆盖

        Returns:
            LLMClient实例
        """
        return cls(
            api_key=settings.openai_api_key,
            api_base=settings.openai_api_base,
            model=model or settings.default_model,
            temperature=temperature or settings.default_temperature
        )

    @classmethod
    def for_scenario(cls, scenario: ScenarioType = "default"):
        """根据场景创建LLMClient（推荐使用）

        Args:
            scenario: 使用场景
                - "default": 默认场景
                - "code_gen": 代码生成场景
                - "agent": Agent场景

        Returns:
            LLMClient实例

        Examples:
            >>> # 代码生成场景
            >>> llm = LLMClient.for_scenario("code_gen")
        """
        # 从 settings 获取配置
        api_key = settings.openai_api_key
        api_base = settings.openai_api_base

        # 根据场景选择配置（使用 settings）
        scenario_configs = {
            "default": {
                "model": settings.default_model,
                "temperature": settings.default_temperature
            },
            "code_gen": {
                "model": settings.code_gen_model,
                "temperature": settings.code_gen_temperature
            },
            "agent": {
                "model": settings.agent_model,
                "temperature": settings.agent_temperature
            }
        }

        config = scenario_configs.get(scenario, scenario_configs["default"])

        logger.info(f"创建 {scenario} 场景的LLM客户端 - 模型: {config['model']}")

        return cls(
            api_key=api_key,
            api_base=api_base,
            model=config["model"],
            temperature=config["temperature"]
        )

    def count_tokens(self, text: str) -> int:
        """计算文本的 token 数量

        Args:
            text: 要计算的文本

        Returns:
            token 数量
        """
        if not text:
            return 0
        return len(self.tokenizer.encode(text))

    def update_token_count(self, input_tokens: int, completion_tokens: int = 0) -> None:
        """更新 token 计数并打印统计信息

        Args:
            input_tokens: 输入 token 数
            completion_tokens: 输出 token 数
        """
        # 更新全局统计
        LLMClient._global_total_input_tokens += input_tokens
        LLMClient._global_total_completion_tokens += completion_tokens
        LLMClient._global_total_tokens = (
            LLMClient._global_total_input_tokens + 
            LLMClient._global_total_completion_tokens
        )
        LLMClient._global_request_count += 1

        # 按照指定格式打印 token 消耗
        logger.info(
            f"Token usage: Input={input_tokens}, Completion={completion_tokens}, "
            f"Cumulative Input={LLMClient._global_total_input_tokens}, "
            f"Cumulative Completion={LLMClient._global_total_completion_tokens}, "
            f"Total={input_tokens + completion_tokens}, "
            f"Cumulative Total={LLMClient._global_total_tokens}"
        )

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """调用聊天完成API

        Args:
            messages: 消息列表
            temperature: 温度参数（可选）
            max_tokens: 最大token数（可选）
            **kwargs: 其他参数

        Returns:
            模型响应文本
        """
        try:
            # 使用 LangChain 1.0 的 invoke 方法
            response = self.client.invoke(messages)
            
            # 从响应中提取 token 使用情况
            if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
                usage = response.response_metadata['token_usage']
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                
                # 更新并打印 token 统计
                self.update_token_count(prompt_tokens, completion_tokens)
            else:
                # 如果无法从响应中获取，尝试估算
                logger.warning("无法从响应中获取 token 使用信息，将进行估算")
                # 估算输入 token
                input_text = ""
                for msg in messages:
                    if isinstance(msg, dict) and 'content' in msg:
                        input_text += str(msg['content'])
                input_tokens = self.count_tokens(input_text)
                
                # 估算输出 token
                completion_tokens = self.count_tokens(response.content)
                
                self.update_token_count(input_tokens, completion_tokens)
            
            return response.content

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    @classmethod
    def get_total_usage(cls) -> Dict[str, int]:
        """获取全局累计token使用统计

        Returns:
            包含统计信息的字典
        """
        return {
            "request_count": cls._global_request_count,
            "total_input_tokens": cls._global_total_input_tokens,
            "total_completion_tokens": cls._global_total_completion_tokens,
            "total_tokens": cls._global_total_tokens
        }

    @classmethod
    def reset_usage(cls):
        """重置全局token使用统计"""
        cls._global_total_input_tokens = 0
        cls._global_total_completion_tokens = 0
        cls._global_total_tokens = 0
        cls._global_request_count = 0
        logger.info("Token使用统计已重置")
