"""
网页截图工具
使用 DrissionPage 捕获本地HTML文件截图
"""
from DrissionPage import ChromiumPage, ChromiumOptions
import os
from datetime import datetime
from pathlib import Path
from loguru import logger
from config.settings import settings
from langchain_core.tools import tool
from typing import Optional

# 全局浏览器实例（用于复用）
_browser_instance: Optional[ChromiumPage] = None


def _get_or_create_browser(width: int = 1920, height: int = 1080) -> ChromiumPage:
    """
    获取或创建浏览器实例（复用模式）

    Args:
        width: 浏览器窗口宽度
        height: 浏览器窗口高度

    Returns:
        浏览器页面对象
    """
    global _browser_instance

    if _browser_instance is None:
        logger.debug("创建新的浏览器实例（将复用）")
        co = ChromiumOptions()
        co.headless(settings.headless)
        co.set_argument('--window-size', f'{width},{height}')

        # 性能优化参数
        co.set_argument('--disable-dev-shm-usage')  # 解决资源限制
        co.set_argument('--no-sandbox')  # 提升启动速度
        co.set_argument('--disable-gpu')  # 禁用GPU加速（截图不需要）
        co.set_argument('--disable-software-rasterizer')

        # 可选：禁用图片加载（如果布局不依赖图片）
        # co.set_argument('--blink-settings=imagesEnabled=false')

        _browser_instance = ChromiumPage(addr_or_opts=co)
        _browser_instance.set.window.size(width, height)

    return _browser_instance


def close_browser():
    """关闭全局浏览器实例"""
    global _browser_instance
    if _browser_instance is not None:
        logger.debug("关闭浏览器实例")
        _browser_instance.quit()
        _browser_instance = None


@tool
def capture_html_file_screenshot(
    html_file_path: str,
    save_path: str = None,
    full_page: bool = True,
    width: int = 1920,
    height: int = 1080,
    reuse_browser: bool = True
) -> str:
    """
    渲染本地HTML文件并截图（优化版，支持浏览器复用）

    Args:
        html_file_path: HTML文件的绝对路径或相对路径
        save_path: 截图保存路径，如果为None则自动生成文件名
        full_page: 是否截取整个页面，默认True
        width: 浏览器窗口宽度，默认1920
        height: 浏览器窗口高度，默认1080
        reuse_browser: 是否复用浏览器实例（默认True，大幅提升性能）

    Returns:
        截图保存的绝对路径
    """
    page = None
    should_close = False

    try:
        logger.debug(f"截图: {Path(html_file_path).name}")

        # 检查HTML文件是否存在
        html_path = Path(html_file_path)
        if not html_path.exists():
            raise FileNotFoundError(f"HTML文件不存在: {html_file_path}")

        # 获取或创建浏览器实例
        if reuse_browser:
            page = _get_or_create_browser(width, height)
        else:
            # 独立模式：创建临时浏览器
            co = ChromiumOptions()
            co.headless(settings.headless)
            co.set_argument('--window-size', f'{width},{height}')
            page = ChromiumPage(addr_or_opts=co)
            page.set.window.size(width, height)
            should_close = True

        # 加载本地HTML文件（使用file://协议）
        file_url = html_path.absolute().as_uri()
        logger.debug(f"  加载: {file_url}")
        page.get(file_url)

        # 智能等待：等待DOM加载完成（最多2秒）
        try:
            page.wait.doc_loaded(timeout=2)
        except:
            # 如果超时，继续执行（可能是简单页面）
            pass

        # 生成默认保存路径
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = html_path.stem
            save_path = f"screenshots/screenshot_{filename}_{timestamp}.png"

        # 确保保存目录存在
        save_dir = os.path.dirname(save_path)
        if save_dir:
            Path(save_dir).mkdir(parents=True, exist_ok=True)

        # 截图
        if full_page:
            page.get_screenshot(path=save_path, full_page=True)
        else:
            page.get_screenshot(path=save_path)

        # 如果是独立模式，关闭浏览器
        if should_close:
            page.quit()

        # 获取绝对路径
        abs_path = os.path.abspath(save_path)

        logger.debug(f"  ✓ 截图完成: {Path(abs_path).name}")
        return abs_path

    except Exception as e:
        # 发生错误时，如果是独立模式则关闭浏览器
        if should_close and page is not None:
            try:
                page.quit()
            except:
                pass

        error_msg = f"HTML文件截图失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

