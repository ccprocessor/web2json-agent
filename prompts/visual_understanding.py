"""
视觉理解 Prompt 模板
用于从网页截图提取结构化信息

支持两种模式：
- v1: 非固定schema字段（自动识别所有有价值的字段）
- v2: 固定字段模式（仅提取预定义的特定字段）
"""

import os
from pathlib import Path
from typing import Literal


class VisualUnderstandingPrompts:
    """视觉理解 Prompt 模板类"""

    # 模板文件根目录
    TEMPLATE_DIR = Path(__file__).parent / "templates"

    # 支持的版本
    SUPPORTED_VERSIONS = ["v1", "v2"]

    @classmethod
    def _load_template(cls, version: str, template_name: str) -> str:
        """
        加载指定版本的模板文件

        Args:
            version: 版本号 (v1, v2)
            template_name: 模板文件名（不含扩展名）

        Returns:
            模板内容字符串

        Raises:
            ValueError: 如果版本不支持或文件不存在
        """
        if version not in cls.SUPPORTED_VERSIONS:
            raise ValueError(
                f"Unsupported version: {version}. "
                f"Supported versions: {', '.join(cls.SUPPORTED_VERSIONS)}"
            )

        template_path = cls.TEMPLATE_DIR / version / f"{template_name}.txt"

        if not template_path.exists():
            raise FileNotFoundError(
                f"Template file not found: {template_path}"
            )

        with open(template_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    @classmethod
    def get_extraction_prompt(
        cls,
        version: Literal["v1", "v2"] = "v1"
    ) -> str:
        """
        获取结构化信息提取 Prompt（首次生成）

        Args:
            version: prompt版本
                - v1: 非固定schema字段（自动识别）
                - v2: 固定字段模式（预定义字段）

        Returns:
            Prompt 字符串
        """
        base_prompt = cls._load_template(version, "base_prompt")
        task_prompt = cls._load_template(version, "extraction_task")

        return f"{base_prompt}\n\n{task_prompt}"

    @classmethod
    def get_schema_refinement_prompt(
        cls,
        previous_schema: dict,
        version: Literal["v1", "v2"] = "v1"
    ) -> str:
        """
        获取Schema迭代优化Prompt（后续迭代）

        Args:
            previous_schema: 上一轮的Schema
            version: prompt版本
                - v1: 非固定schema字段（自动识别）
                - v2: 固定字段模式（预定义字段）

        Returns:
            Prompt字符串
        """
        import json

        schema_str = json.dumps(previous_schema, ensure_ascii=False, indent=2)
        base_prompt = cls._load_template(version, "base_prompt")
        task_prompt = cls._load_template(version, "refinement_task")

        return f"""## 当前Schema

```json
{schema_str}
```

{base_prompt}

{task_prompt}
"""

    @classmethod
    def get_system_message(
        cls,
        version: Literal["v1", "v2"] = "v1"
    ) -> str:
        """
        获取系统消息

        Args:
            version: prompt版本
                - v1: 非固定schema字段（自动识别）
                - v2: 固定字段模式（预定义字段）

        Returns:
            系统消息字符串
        """
        return cls._load_template(version, "system_message")
