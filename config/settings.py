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
    # Agent
    agent_model: str = Field(default_factory=lambda: os.getenv("AGENT_MODEL", "claude-sonnet-4-5-20250929"))
    agent_temperature: float = Field(default_factory=lambda: float(os.getenv("AGENT_TEMPERATURE", "0")))

    # 代码生成
    code_gen_model: str = Field(default_factory=lambda: os.getenv("CODE_GEN_MODEL", "claude-sonnet-4-5-20250929"))
    code_gen_temperature: float = Field(default_factory=lambda: float(os.getenv("CODE_GEN_TEMPERATURE", "0.3")))
    code_gen_max_tokens: int = Field(default_factory=lambda: int(os.getenv("CODE_GEN_MAX_TOKENS", "8192")))

    # 视觉理解
    vision_model: str = Field(default_factory=lambda: os.getenv("VISION_MODEL", "qwen-vl-max"))
    vision_temperature: float = Field(default_factory=lambda: float(os.getenv("VISION_TEMPERATURE", "0")))
    vision_max_tokens: int = Field(default_factory=lambda: int(os.getenv("VISION_MAX_TOKENS", "4096")))

    # ============================================
    # Agent 配置
    # ============================================
    max_iterations: int = Field(default_factory=lambda: int(os.getenv("MAX_ITERATIONS", "5")))
    success_threshold: float = Field(default_factory=lambda: float(os.getenv("SUCCESS_THRESHOLD", "0.8")))
    min_sample_size: int = Field(default_factory=lambda: int(os.getenv("MIN_SAMPLE_SIZE", "2")))

    # ============================================
    # 浏览器配置
    # ============================================
    headless: bool = Field(default_factory=lambda: os.getenv("HEADLESS", "true").lower() == "true")
    timeout: int = Field(default_factory=lambda: int(os.getenv("TIMEOUT", "30000")))
    screenshot_full_page: bool = Field(default_factory=lambda: os.getenv("SCREENSHOT_FULL_PAGE", "true").lower() == "true")

    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
