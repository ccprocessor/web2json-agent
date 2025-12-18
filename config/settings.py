"""
HtmlParserAgent 配置管理模块
"""
import os
from typing import Optional
from pydantic import BaseModel, Field
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Settings(BaseModel):
    """全局配置"""

    # ============================================
    # API 配置
    # ============================================
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_api_base: str = Field(default_factory=lambda: os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"))

    # ============================================
    # 模型配置
    # ============================================
    # 默认模型（通用场景）
    default_model: str = Field(default_factory=lambda: os.getenv("DEFAULT_MODEL", "claude-sonnet-4-5-20250929"))
    default_temperature: float = Field(default_factory=lambda: float(os.getenv("DEFAULT_TEMPERATURE", "0.3")))

    # Agent
    agent_model: str = Field(default_factory=lambda: os.getenv("AGENT_MODEL", "claude-sonnet-4-5-20250929"))
    agent_temperature: float = Field(default_factory=lambda: float(os.getenv("AGENT_TEMPERATURE", "0")))

    # 代码生成
    code_gen_model: str = Field(default_factory=lambda: os.getenv("CODE_GEN_MODEL", "claude-sonnet-4-5-20250929"))
    code_gen_temperature: float = Field(default_factory=lambda: float(os.getenv("CODE_GEN_TEMPERATURE", "0.3")))
    code_gen_max_tokens: int = Field(default_factory=lambda: int(os.getenv("CODE_GEN_MAX_TOKENS", "16384")))

    # 视觉理解
    vision_model: str = Field(default_factory=lambda: os.getenv("VISION_MODEL", "qwen-vl-max"))
    vision_temperature: float = Field(default_factory=lambda: float(os.getenv("VISION_TEMPERATURE", "0")))
    vision_max_tokens: int = Field(default_factory=lambda: int(os.getenv("VISION_MAX_TOKENS", "16384")))

    # ============================================
    # Agent 配置
    # ============================================
    # 迭代次数由输入URL数量决定，无需配置

    # ============================================
    # 浏览器配置
    # ============================================
    headless: bool = Field(default_factory=lambda: os.getenv("HEADLESS", "true").lower() == "true")
    timeout: int = Field(default_factory=lambda: int(os.getenv("TIMEOUT", "30000")))
    screenshot_full_page: bool = Field(default_factory=lambda: os.getenv("SCREENSHOT_FULL_PAGE", "true").lower() == "true")

    # ============================================
    # HTML精简配置
    # ============================================
    html_simplify_mode: str = Field(default_factory=lambda: os.getenv("HTML_SIMPLIFY_MODE", "xpath"))
    html_keep_attrs: list = Field(default_factory=lambda: [
        attr.strip() for attr in os.getenv("HTML_KEEP_ATTRS", "class,id,href,src,data-id").split(",")
    ])

    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
