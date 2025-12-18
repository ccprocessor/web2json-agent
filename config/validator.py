"""
配置验证和初始化工具
确保用户正确配置 API 密钥等必需参数
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from loguru import logger


class ConfigValidator:
    """配置验证器"""

    # 必需的环境变量
    REQUIRED_VARS = {
        "OPENAI_API_KEY": "OpenAI API 密钥（或兼容的 API 密钥）",
    }

    # 可选但推荐的环境变量
    RECOMMENDED_VARS = {
        "OPENAI_API_BASE": "API 基础 URL（默认: https://api.openai.com/v1）",
        "AGENT_MODEL": "Agent 使用的模型（默认: claude-sonnet-4-5-20250929）",
        "CODE_GEN_MODEL": "代码生成模型（默认: claude-sonnet-4-5-20250929）",
        "VISION_MODEL": "视觉理解模型（默认: qwen-vl-max）",
    }

    @classmethod
    def check_config(cls, verbose: bool = True) -> Tuple[bool, List[str]]:
        """
        检查配置是否完整

        Args:
            verbose: 是否输出详细信息

        Returns:
            (是否通过, 缺失的必需配置列表)
        """
        missing_required = []
        missing_recommended = []

        # 检查必需配置
        for var, desc in cls.REQUIRED_VARS.items():
            value = os.getenv(var)
            if not value or value.strip() == "":
                missing_required.append((var, desc))

        # 检查推荐配置
        if verbose:
            for var, desc in cls.RECOMMENDED_VARS.items():
                value = os.getenv(var)
                if not value or value.strip() == "":
                    missing_recommended.append((var, desc))

        # 输出检查结果
        if verbose:
            if not missing_required and not missing_recommended:
                logger.success("✓ 配置检查通过")
                return True, []

            if missing_required:
                logger.error("\n缺少必需的配置项:")
                for var, desc in missing_required:
                    logger.error(f"  ✗ {var}: {desc}")

            if missing_recommended:
                logger.warning("\n缺少推荐的配置项（将使用默认值）:")
                for var, desc in missing_recommended:
                    logger.warning(f"  ! {var}: {desc}")

        return len(missing_required) == 0, [var for var, _ in missing_required]

    @classmethod
    def create_env_file(cls, target_dir: Optional[Path] = None) -> Path:
        """
        创建 .env 配置文件模板

        Args:
            target_dir: 目标目录（默认为当前工作目录）

        Returns:
            创建的 .env 文件路径
        """
        if target_dir is None:
            target_dir = Path.cwd()

        env_file = target_dir / ".env"

        # 检查是否已存在
        if env_file.exists():
            logger.warning(f".env 文件已存在: {env_file}")
            response = input("是否覆盖? (y/N): ").strip().lower()
            if response != 'y':
                logger.info("取消创建")
                return env_file

        # 读取模板
        template_path = Path(__file__).parent.parent / ".env.example"
        if template_path.exists():
            template_content = template_path.read_text(encoding="utf-8")
        else:
            # 如果模板不存在，使用内置模板
            template_content = cls._get_default_template()

        # 写入文件
        env_file.write_text(template_content, encoding="utf-8")
        logger.success(f"✓ 已创建配置文件: {env_file}")

        return env_file

    @classmethod
    def _get_default_template(cls) -> str:
        """获取默认配置模板"""
        return """# ============================================
# API 配置 (必需)
# ============================================
# OpenAI API 密钥（或兼容 OpenAI API 的服务密钥）
OPENAI_API_KEY=your_api_key_here

# API 基础 URL（如使用第三方服务，修改此项）
OPENAI_API_BASE=https://api.openai.com/v1

# ============================================
# 模型配置 (可选，使用默认值即可)
# ============================================
# Agent 模型
AGENT_MODEL=claude-sonnet-4-5-20250929
AGENT_TEMPERATURE=0

# 代码生成模型
CODE_GEN_MODEL=claude-sonnet-4-5-20250929
CODE_GEN_TEMPERATURE=0.3
CODE_GEN_MAX_TOKENS=8192

# 视觉理解模型
VISION_MODEL=qwen-vl-max
VISION_TEMPERATURE=0
VISION_MAX_TOKENS=4096

# ============================================
# 浏览器配置
# ============================================
HEADLESS=true
TIMEOUT=30000
SCREENSHOT_FULL_PAGE=true

# ============================================
# HTML精简配置
# ============================================
# 精简模式: xpath/aggressive/conservative
HTML_SIMPLIFY_MODE=xpath
# 保留的HTML属性（逗号分隔）
HTML_KEEP_ATTRS=class,id,href,src,data-id
"""

    @classmethod
    def show_config_guide(cls):
        """显示配置指南"""
        print("\n" + "=" * 70)
        print("web2json-agent 配置指南")
        print("=" * 70)

        print("\n1️⃣  初始化配置文件:")
        print("   web2json init")

        print("\n2️⃣  编辑 .env 文件，填入你的 API 密钥:")
        print("   # 必需配置")
        print("   OPENAI_API_KEY=your_api_key_here")
        print("   OPENAI_API_BASE=https://your-api-base-url.com/v1")

        print("\n3️⃣  验证配置:")
        print("   web2json check")

        print("\n4️⃣  开始使用:")
        print("   web2json -d input_html/ -o output/blog")

        print("\n📖 详细文档:")
        print("   https://github.com/ccprocessor/web2json-agent")

        print("\n" + "=" * 70 + "\n")

    @classmethod
    def interactive_setup(cls) -> bool:
        """
        交互式配置向导

        Returns:
            是否成功完成配置
        """
        print("\n" + "=" * 70)
        print("web2json-agent 配置向导")
        print("=" * 70)

        print("\n请按照提示输入配置信息（按 Enter 使用默认值）\n")

        config_values: Dict[str, str] = {}

        # 收集必需配置
        print("📌 必需配置:")
        for var, desc in cls.REQUIRED_VARS.items():
            current_value = os.getenv(var, "")
            prompt = f"  {desc}\n  [{var}]: "
            value = input(prompt).strip()
            if value:
                config_values[var] = value
            elif current_value:
                config_values[var] = current_value
                print(f"    → 使用当前值")
            else:
                logger.error(f"✗ {var} 是必需的")
                return False

        # 收集推荐配置
        print("\n📝 推荐配置（可选，按 Enter 使用默认值）:")
        for var, desc in cls.RECOMMENDED_VARS.items():
            current_value = os.getenv(var, "")
            prompt = f"  {desc}\n  [{var}]: "
            value = input(prompt).strip()
            if value:
                config_values[var] = value
            elif current_value:
                config_values[var] = current_value

        # 生成配置文件
        print("\n正在生成配置文件...")
        env_file = Path.cwd() / ".env"

        # 读取现有内容或使用模板
        if env_file.exists():
            content = env_file.read_text(encoding="utf-8")
        else:
            content = cls._get_default_template()

        # 更新配置值
        for var, value in config_values.items():
            # 替换或添加配置项
            import re
            pattern = rf'^{var}=.*$'
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, f'{var}={value}', content, flags=re.MULTILINE)
            else:
                content += f'\n{var}={value}\n'

        # 写入文件
        env_file.write_text(content, encoding="utf-8")
        logger.success(f"\n✓ 配置已保存到: {env_file}")

        # 重新加载环境变量
        from dotenv import load_dotenv
        load_dotenv(env_file, override=True)

        # 验证配置
        print("\n正在验证配置...")
        is_valid, _ = cls.check_config(verbose=True)

        if is_valid:
            logger.success("\n✅ 配置完成！现在可以使用 web2json 命令了")
            print("\n示例命令:")
            print("  web2json -d input_html/ -o output/blog")

        return is_valid


def check_config_or_guide():
    """
    检查配置，如果配置不完整则显示配置指南
    用于 CLI 启动时调用
    """
    is_valid, missing = ConfigValidator.check_config(verbose=False)

    if not is_valid:
        logger.error("❌ 配置不完整，缺少以下必需配置:")
        for var in missing:
            desc = ConfigValidator.REQUIRED_VARS.get(var, "")
            logger.error(f"  • {var}: {desc}")

        print("\n" + "=" * 70)
        print("请先完成配置:")
        print("  1. 运行: web2json init")
        print("  2. 编辑 .env 文件，填入你的 API 密钥")
        print("  3. 再次运行你的命令")
        print("\n或者运行交互式配置向导:")
        print("  web2json setup")
        print("=" * 70 + "\n")

        sys.exit(1)

    return True
