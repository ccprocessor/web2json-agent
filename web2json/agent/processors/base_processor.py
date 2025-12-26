"""
处理器基类
定义处理器的标准接口
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseProcessor(ABC):
    """处理器基类，所有处理器都应继承此类"""

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据

        Args:
            input_data: 输入数据字典

        Returns:
            处理结果字典，必须包含 'success' 字段
        """
        pass
