"""
网页截图工具
使用 DrissionPage 捕获网页截图
"""
from DrissionPage import ChromiumPage, ChromiumOptions
import os
from datetime import datetime
from pathlib import Path
from loguru import logger
from config.settings import settings
from langchain_core.tools import tool


@tool
def capture_webpage_screenshot(
    url: str,
    save_path: str = None,
    full_page: bool = True,
    width: int = 1920,
    height: int = 1080
) -> str:
    """
    捕获网页截图

    Args:
        url: 要截图的网页URL
        save_path: 截图保存路径，如果为None则自动生成文件名
        full_page: 是否截取整个页面，默认True
        width: 浏览器窗口宽度，默认1920
        height: 浏览器窗口高度，默认1080

    Returns:
        截图保存的绝对路径
    """
    try:
        logger.info(f"正在截图网页: {url}")

        # 配置浏览器选项
        co = ChromiumOptions()
        co.headless(settings.headless)
        co.set_argument('--window-size', f'{width},{height}')

        # 创建页面对象
        page = ChromiumPage(addr_or_opts=co)

        # 设置窗口大小
        page.set.window.size(width, height)

        # 访问网页
        page.get(url)

        # 等待页面加载完成
        page.wait(3)

        # 生成默认保存路径
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain = url.split("//")[-1].split("/")[0].replace(".", "_")
            save_path = f"screenshots/screenshot_{domain}_{timestamp}.png"

        # 确保保存目录存在
        save_dir = os.path.dirname(save_path)
        if save_dir:
            Path(save_dir).mkdir(parents=True, exist_ok=True)

        # 截图
        if full_page:
            page.get_screenshot(path=save_path, full_page=True)
        else:
            page.get_screenshot(path=save_path)

        # 关闭浏览器
        page.quit()

        # 获取绝对路径
        abs_path = os.path.abspath(save_path)

        logger.success(f"截图成功保存到: {abs_path}")
        return abs_path

    except Exception as e:
        error_msg = f"网页截图失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

