"""
获取网页源码工具
支持从本地HTML文件读取和使用 Playwright 从URL获取
"""
from pathlib import Path
from loguru import logger
from config.settings import settings
from langchain_core.tools import tool
from tools.playwright_browser import create_browser


@tool
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


@tool
def get_webpage_source(
    url: str,
    wait_time: int = 3,
    anti_bot: bool = True,
    max_retries: int = 3
) -> str:
    """
    获取网页的HTML源代码，支持绕过 Cloudflare 人机验证

    Args:
        url: 要获取源码的网页URL
        wait_time: 页面加载等待时间（秒），默认3秒
        anti_bot: 是否启用反机器人检测（推荐开启以绕过 Cloudflare），默认True
        max_retries: 最大重试次数，默认3次

    Returns:
        网页的HTML源代码字符串
    """
    browser = None
    try:
        logger.info(f"正在获取网页源码: {url}")

        # 创建浏览器实例
        browser = create_browser(
            headless=settings.headless,
            timeout=settings.timeout
        )

        # 获取网页内容
        html_source, final_url = browser.get_page_content(
            url=url,
            wait_time=wait_time,
            anti_bot=anti_bot,
            max_retries=max_retries
        )

        if final_url != url:
            logger.info(f"页面发生重定向: {url} -> {final_url}")

        logger.success(f"成功获取网页源码，长度: {len(html_source)} 字符")
        return html_source

    except Exception as e:
        error_msg = f"获取网页源码失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        # 确保浏览器被关闭
        if browser:
            try:
                browser.close()
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

