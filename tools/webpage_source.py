"""
获取网页源码工具
使用 DrissionPage 获取网页的HTML源代码
"""
from DrissionPage import ChromiumPage, ChromiumOptions
from loguru import logger
from config.settings import settings
from langchain_core.tools import tool


@tool
def get_webpage_source(url: str, wait_time: int = 3) -> str:
    """
    获取网页的HTML源代码

    Args:
        url: 要获取源码的网页URL
        wait_time: 页面加载等待时间（秒），默认3秒

    Returns:
        网页的HTML源代码字符串
    """
    try:
        logger.info(f"正在获取网页源码: {url}")

        # 配置无头模式
        co = ChromiumOptions()
        co.headless(settings.headless)

        # 创建页面对象
        page = ChromiumPage(addr_or_opts=co)

        # 访问网页
        page.get(url)

        # 等待页面加载
        page.wait(wait_time)

        # 获取HTML源码
        html_source = page.html

        # 关闭浏览器
        page.quit()

        logger.success(f"成功获取网页源码，长度: {len(html_source)} 字符")
        return html_source

    except Exception as e:
        error_msg = f"获取网页源码失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

