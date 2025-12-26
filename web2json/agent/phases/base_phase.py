"""
阶段管理器基类
定义阶段的标准接口
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePhase(ABC):
    """阶段管理器基类，所有阶段管理器都应继承此类"""

    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        执行阶段流程

        Returns:
            阶段执行结果，必须包含 'success' 字段
        """
        pass
