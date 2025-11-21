"""
LLM客户端封装 - 使用 LangChain 1.0
支持基于场景的模型配置
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

from dotenv import load_dotenv
from loguru import logger
from langchain_openai import ChatOpenAI

# 加载项目根目录的 .env 文件
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

# 验证
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(f".env 文件路径: {env_path}, API Key未加载")

# 定义场景类型
ScenarioType = Literal["default", "code_gen", "vision", "agent"]


class LLMClient:
    """LLM客户端封装类 - 基于 LangChain 1.0

    支持多种使用方式：
    1. 直接初始化：LLMClient(model="gpt-4")
    2. 从Settings创建：LLMClient.from_settings(settings)
    3. 按场景创建：LLMClient.for_scenario("code_gen")
    """

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
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base = api_base or os.getenv("OPENAI_API_BASE", "http://35.220.164.252:3888/v1")
        self.model = model or os.getenv("DEFAULT_MODEL", "claude-sonnet-4-5-20250929")
        self.temperature = temperature

        # 使用 LangChain 1.0 的 ChatOpenAI（兼容所有模型）
        self.client = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.api_base,
            temperature=self.temperature
        )

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
                - "vision": 视觉理解场景
                - "agent": Agent场景

        Returns:
            LLMClient实例

        Examples:
            >>> # 代码生成场景
            >>> llm = LLMClient.for_scenario("code_gen")
            >>>
            >>> # 视觉理解场景
            >>> llm = LLMClient.for_scenario("vision")
        """
        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE", "http://35.220.164.252:3888/v1")

        # 根据场景选择配置
        scenario_configs = {
            "default": {
                "model": os.getenv("DEFAULT_MODEL", "claude-sonnet-4-5-20250929"),
                "temperature": float(os.getenv("DEFAULT_TEMPERATURE", "0"))
            },
            "code_gen": {
                "model": os.getenv("CODE_GEN_MODEL", "claude-sonnet-4-5-20250929"),
                "temperature": float(os.getenv("CODE_GEN_TEMPERATURE", "0.3"))
            },
            "vision": {
                "model": os.getenv("VISION_MODEL", "qwen-vl-max"),
                "temperature": float(os.getenv("VISION_TEMPERATURE", "0"))
            },
            "agent": {
                "model": os.getenv("AGENT_MODEL", "claude-sonnet-4-5-20250929"),
                "temperature": float(os.getenv("AGENT_TEMPERATURE", "0"))
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
            return response.content

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def vision_completion(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        image_data: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """调用视觉理解API

        Args:
            prompt: 提示文本
            image_url: 图片URL
            image_data: Base64编码的图片数据
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            模型响应文本
        """
        content = [{"type": "text", "text": prompt}]

        if image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
        elif image_data:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_data}"}
            })

        messages = [{"role": "user", "content": content}]

        # 使用 LangChain 1.0 的 invoke 方法
        try:
            response = self.client.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"视觉模型调用失败: {e}")
            raise

