"""
HtmlParserAgent 配置管理模块
"""
import os
from typing import Optional
from pydantic import BaseModel, Field
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量（优先从当前工作目录加载，其次从包目录）
env_paths = [
    Path.cwd() / ".env",  # 用户工作目录（优先）
    Path(__file__).parent.parent / ".env",  # 包安装目录（fallback）
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break


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
    # 默认迭代轮数（用于Schema学习的样本数量）
    default_iteration_rounds: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_ITERATION_ROUNDS", "3")))

    # Schema模式 (auto: 自动提取和筛选字段, predefined: 使用预定义schema模板)
    schema_mode: str = Field(default_factory=lambda: os.getenv("SCHEMA_MODE", "auto"))

    # 并发控制
    max_concurrent_extractions: int = Field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_EXTRACTIONS", "5")))
    max_concurrent_merges: int = Field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_MERGES", "5")))

    # ============================================
    # 布局聚类配置
    # ============================================
    # DBSCAN聚类参数
    cluster_eps: float = Field(default_factory=lambda: float(os.getenv("CLUSTER_EPS", "0.05")))
    cluster_min_samples: int = Field(default_factory=lambda: int(os.getenv("CLUSTER_MIN_SAMPLES", "2")))

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

    # ============================================
    # SWDE 评估配置
    # ============================================
    swde_dataset_dir: str = Field(default_factory=lambda: os.getenv("SWDE_DATASET_DIR", "evaluationSet"))
    swde_groundtruth_dir: str = Field(default_factory=lambda: os.getenv("SWDE_GROUNDTRUTH_DIR", "evaluationSet/groundtruth"))
    swde_output_dir: str = Field(default_factory=lambda: os.getenv("SWDE_OUTPUT_DIR", "output/swde_results"))
    swde_python_cmd: str = Field(default_factory=lambda: os.getenv("SWDE_PYTHON_CMD", "python3"))
    swde_use_predefined_schema: bool = Field(default_factory=lambda: os.getenv("SWDE_USE_PREDEFINED_SCHEMA", "false").lower() in ("true", "1", "yes"))
    swde_resume: bool = Field(default_factory=lambda: os.getenv("SWDE_RESUME", "false").lower() in ("true", "1", "yes"))
    swde_skip_agent: bool = Field(default_factory=lambda: os.getenv("SWDE_SKIP_AGENT", "false").lower() in ("true", "1", "yes"))
    swde_skip_evaluation: bool = Field(default_factory=lambda: os.getenv("SWDE_SKIP_EVALUATION", "false").lower() in ("true", "1", "yes"))
    swde_force: bool = Field(default_factory=lambda: os.getenv("SWDE_FORCE", "false").lower() in ("true", "1", "yes"))

    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
