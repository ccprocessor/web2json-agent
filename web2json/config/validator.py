"""
配置验证和初始化工具
确保用户正确配置 API 密钥等必需参数
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from loguru import logger
from dotenv import load_dotenv


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
    def test_api_connection(cls, test_models: bool = True) -> Tuple[bool, Dict[str, str]]:
        """
        测试 API 连接和模型可用性

        Args:
            test_models: 是否测试模型连接（默认 True）

        Returns:
            (是否通过, 错误信息字典)
        """
        errors = {}

        # 加载环境变量
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)

        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

        if not api_key:
            errors["api_key"] = "API 密钥未配置"
            return False, errors

        if not test_models:
            return True, {}

        # 测试模型连接
        logger.info("正在测试 API 连接和模型可用性...")

        try:
            from langchain_openai import ChatOpenAI

            # 获取要测试的模型列表
            models_to_test = {
                "Agent模型": os.getenv("AGENT_MODEL", "claude-sonnet-4-5-20250929"),
                "代码生成模型": os.getenv("CODE_GEN_MODEL", "claude-sonnet-4-5-20250929"),
            }

            # 去重（避免重复测试相同模型）
            unique_models = {}
            for name, model in models_to_test.items():
                if model not in unique_models.values():
                    unique_models[name] = model

            # 测试每个模型
            for model_name, model_id in unique_models.items():
                try:
                    logger.info(f"  测试 {model_name}: {model_id}")

                    client = ChatOpenAI(
                        model=model_id,
                        api_key=api_key,
                        base_url=api_base,
                        temperature=0,
                        timeout=10
                    )

                    # 发送简单测试消息
                    response = client.invoke([{"role": "user", "content": "test"}])

                    if response and response.content:
                        logger.success(f"  ✓ {model_name} 连接成功")
                    else:
                        errors[model_name] = "模型返回为空"
                        logger.error(f"  ✗ {model_name} 返回为空")

                except Exception as e:
                    error_msg = str(e)
                    errors[model_name] = error_msg
                    logger.error(f"  ✗ {model_name} 连接失败: {error_msg}")

            # 判断是否全部通过
            if not errors:
                logger.success("\n✓ 所有模型连接测试通过！")
                return True, {}
            else:
                logger.error(f"\n✗ {len(errors)} 个模型连接失败")
                return False, errors

        except ImportError as e:
            errors["import"] = f"依赖库导入失败: {e}"
            logger.error(f"✗ 依赖库导入失败: {e}")
            return False, errors
        except Exception as e:
            errors["unknown"] = f"未知错误: {e}"
            logger.error(f"✗ 测试过程出错: {e}")
            return False, errors

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
# web2json-agent 环境配置文件
# ============================================
# 使用方法: cp .env.example .env
# 然后修改 .env 文件中的配置值

# ============================================
# API 配置（必填）
# ============================================
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# ============================================
# 模型配置（可选，使用默认值）
# ============================================

# Agent 规划和执行
AGENT_MODEL=claude-sonnet-4-5-20250929
AGENT_TEMPERATURE=0

# 代码生成
CODE_GEN_MODEL=claude-sonnet-4-5-20250929
CODE_GEN_TEMPERATURE=0.3
CODE_GEN_MAX_TOKENS=16384

# ============================================
# HTML精简配置（可选）
# ============================================
# 精简模式: xpath, aggressive, conservative
# - xpath: 为Schema提取优化，保留定位属性和内容标签（推荐）
# - aggressive: 激进模式，最大化压缩
# - conservative: 保守模式，保留更多原始结构
HTML_SIMPLIFY_MODE=xpath

# 保留的HTML属性（逗号分隔，仅xpath和aggressive模式有效）
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

        if not is_valid:
            return False

        # 询问是否测试 API 连接
        print("\n是否测试 API 连接和模型可用性？(推荐)")
        test_choice = input("  测试 API? (Y/n): ").strip().lower()

        if test_choice != 'n':
            print("\n🔌 测试 API 连接...\n")
            api_valid, errors = cls.test_api_connection(test_models=True)

            if not api_valid:
                logger.error("\n❌ API 连接测试失败")
                for model_name, error in errors.items():
                    logger.error(f"  ✗ {model_name}: {error}")
                print("\n请检查:")
                print("  1. API 密钥是否正确")
                print("  2. API Base URL 是否可访问")
                print("  3. 模型名称是否正确")
                print("  4. 网络连接是否正常")
                return False

        logger.success("\n✅ 配置完成！现在可以使用 web2json 命令了")
        print("\n示例命令:")
        print("  web2json -d input_html/ -o output/blog")

        return True


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
