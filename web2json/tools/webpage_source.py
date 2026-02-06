"""
获取网页源码工具
从本地HTML文件读取
"""
from pathlib import Path
from loguru import logger


def get_html_from_file(file_path: str) -> str:
    """
    从本地文件读取HTML源代码

    Args:
        file_path: HTML文件的绝对路径或相对路径

    Returns:
        HTML源代码字符串
    """
    try:
        logger.info(f"正在读取本地HTML文件: {file_path}")

        # 将路径转换为Path对象
        html_file = Path(file_path)

        # 检查文件是否存在
        if not html_file.exists():
            raise FileNotFoundError(f"HTML文件不存在: {file_path}")

        # 检查是否是文件
        if not html_file.is_file():
            raise ValueError(f"路径不是一个文件: {file_path}")

        # 读取HTML内容
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        logger.success(f"成功读取HTML文件，长度: {len(html_content)} 字符")
        return html_content

    except Exception as e:
        error_msg = f"读取HTML文件失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

