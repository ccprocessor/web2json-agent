"""
HTML 精简工具
提取自 html_alg_lib，只保留核心的 HTML 精简功能
"""
from lxml import html
from collections import deque
from typing import List, Set
from loguru import logger
from langchain_core.tools import tool


# ============================================
# 核心工具函数
# ============================================

def html_to_element(html_str: str) -> html.HtmlElement:
    """将 HTML 字符串转换为 lxml 元素"""
    parser = html.HTMLParser(
        collect_ids=False,
        encoding='utf-8',
        remove_comments=True,
        remove_pis=True
    )
    # 处理编码声明
    if isinstance(html_str, str) and (
        '<?xml' in html_str or '<meta charset' in html_str or 'encoding=' in html_str
    ):
        html_str = html_str.encode('utf-8')

    root = html.fromstring(html_str, parser=parser)
    return root


def element_to_html(root: html.HtmlElement) -> str:
    """将 lxml 元素转换为 HTML 字符串"""
    html_str = html.tostring(root, encoding='utf-8').decode()
    return html_str


def remove_reversely(element_list: List[html.HtmlElement]):
    """反向删除元素列表（避免迭代器问题）"""
    for element in reversed(element_list):
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)


# ============================================
# HTML 精简处理函数
# ============================================

def remove_tags_by_types(root: html.HtmlElement, tag_type_list: List[str]) -> html.HtmlElement:
    """
    删除指定类型的标签

    Args:
        root: HTML 根元素
        tag_type_list: 要删除的标签类型列表

    Returns:
        处理后的 HTML 根元素
    """
    if not tag_type_list:
        return root
    xpath = '|'.join([f'.//{tag}' for tag in tag_type_list])
    remove_targets = root.xpath(xpath)
    remove_reversely(remove_targets)
    return root


def is_display_none(element: html.HtmlElement) -> bool:
    """检查元素是否设置了 display:none"""
    style = element.get('style', '').replace(' ', '').lower()
    return 'display:none' in style


def remove_invisible_tags(root: html.HtmlElement) -> html.HtmlElement:
    """
    删除不可见的标签（display:none）

    Args:
        root: HTML 根元素

    Returns:
        处理后的 HTML 根元素
    """
    remove_targets = [element for element in root.iter() if is_display_none(element)]
    remove_reversely(remove_targets)
    return root


def remove_empty_tags(
    root: html.HtmlElement,
    predefined_non_empty_tags: Set[str] = {'img', 'br', 'hr', 'input'}
) -> html.HtmlElement:
    """
    递归删除空标签

    Args:
        root: HTML 根元素
        predefined_non_empty_tags: 预定义的非空标签集合（即使没有内容也不删除）

    Returns:
        处理后的 HTML 根元素
    """
    # 使用队列处理叶子节点
    leaf_elements = deque([node for node in root.iter() if len(node) == 0])

    while leaf_elements:
        leaf_element = leaf_elements.pop()
        parent = leaf_element.getparent()

        # 如果父节点为 None，说明是根节点，跳过
        if parent is None:
            continue

        # 如果是预定义的非空标签，跳过
        if leaf_element.tag in predefined_non_empty_tags:
            continue

        # 如果有文本内容，跳过
        if leaf_element.text and leaf_element.text.strip():
            continue

        # 删除空标签
        parent.remove(leaf_element)

        # 如果父节点变成了叶子节点，加入队列
        if len(parent) == 0:
            leaf_elements.append(parent)

    return root


def clean_attributes(
    root: html.HtmlElement,
    keep_attrs: List[str] = None
) -> html.HtmlElement:
    """
    清理元素的属性，只保留指定的属性

    Args:
        root: HTML 根元素
        keep_attrs: 要保留的属性列表，None 表示删除所有属性

    Returns:
        处理后的 HTML 根元素
    """
    keep_attrs_set = set(keep_attrs) if keep_attrs else set()

    for elem in root.iter():
        # 获取所有属性的副本（避免迭代时修改）
        attrs_to_remove = [
            attr for attr in elem.attrib.keys()
            if attr not in keep_attrs_set
        ]
        for attr in attrs_to_remove:
            elem.attrib.pop(attr)

    return root


# ============================================
# 主要精简函数
# ============================================

def simplify_html_minimal(
    html_str: str,
    remove_tags: List[str] = None,
    remove_invisible: bool = True,
    remove_empty: bool = True,
    clean_attrs: bool = True,
    keep_attrs: List[str] = None
) -> str:
    """
    HTML 精简（最小化实现）

    Args:
        html_str: 原始 HTML 字符串
        remove_tags: 要删除的标签列表，None 使用默认列表
        remove_invisible: 是否删除不可见元素
        remove_empty: 是否删除空标签
        clean_attrs: 是否清理属性
        keep_attrs: 要保留的属性列表（仅在 clean_attrs=True 时有效）

    Returns:
        精简后的 HTML 字符串
    """
    # 默认要删除的标签列表
    if remove_tags is None:
        remove_tags = [
            # 头部和元数据
            'base', 'head', 'link', 'meta', 'style', 'title',
            # 脚本和嵌入
            'script', 'noscript', 'iframe', 'embed', 'object',
            # 导航和布局
            'nav', 'aside', 'footer', 'header',
            # 表单元素（通常不需要）
            'button', 'datalist', 'fieldset', 'input', 'label',
            'legend', 'meter', 'optgroup', 'option', 'output',
            'progress', 'select', 'textarea', 'form',
            # 其他
            'canvas', 'dialog', 'source', 'track',
        ]

    try:
        # 1. 解析 HTML
        root = html_to_element(html_str)

        # 2. 删除指定的标签
        if remove_tags:
            root = remove_tags_by_types(root, remove_tags)

        # 3. 删除不可见元素
        if remove_invisible:
            root = remove_invisible_tags(root)

        # 4. 删除空标签
        if remove_empty:
            root = remove_empty_tags(root)

        # 5. 清理属性
        if clean_attrs:
            root = clean_attributes(root, keep_attrs)

        # 6. 转换回 HTML 字符串
        result = element_to_html(root)

        return result

    except Exception as e:
        logger.error(f"HTML 精简失败: {str(e)}")
        raise


# ============================================
# 主函数（可直接调用）
# ============================================

def simplify_html(
    html_str: str,
    keep_attrs: List[str] = None,
    aggressive: bool = True,
    mode: str = 'default'
) -> str:
    """
    精简 HTML，删除无用标签和属性，使其更易于处理和分析

    Args:
        html_str: 原始 HTML 字符串
        keep_attrs: 要保留的属性列表，例如 ['class', 'id', 'href']。None 表示删除所有属性
        aggressive: 是否使用激进模式（删除更多标签和清理所有属性）
        mode: 精简模式
            - 'default': 根据aggressive参数决定
            - 'xpath': 为xpath提取优化，保留结构属性和内容标签

    Returns:
        精简后的 HTML 字符串

    Examples:
        >>> html = '<html><head><script>...</script></head><body><div>content</div></body></html>'
        >>> simplified = simplify_html(html)
        >>> # 结果: '<html><body><div>content</div></body></html>'

        >>> # 保留特定属性
        >>> simplified = simplify_html(html, keep_attrs=['class', 'id'])

        >>> # 为xpath提取优化
        >>> simplified = simplify_html(html, mode='xpath')
    """
    try:
        logger.info(f"开始精简 HTML，长度: {len(html_str)} 字符")

        # xpath模式：为xpath提取优化
        if mode == 'xpath':
            # 删除明确无用的标签，但保留可能有内容的标签
            remove_tags_list = [
                # 头部和元数据
                'base', 'head', 'link', 'meta', 'style', 'title',
                # 脚本和嵌入
                'script', 'noscript', 'iframe', 'embed', 'object',
                # 表单元素（通常不需要）
                'button', 'datalist', 'fieldset', 'input', 'label',
                'legend', 'meter', 'optgroup', 'option', 'output',
                'progress', 'select', 'textarea', 'form',
                # 其他
                'canvas', 'dialog', 'source', 'track',
            ]
            # 保留class, id等定位属性
            keep_attrs_list = keep_attrs if keep_attrs is not None else ['class', 'id', 'href', 'src', 'data-id']

            result = simplify_html_minimal(
                html_str=html_str,
                remove_tags=remove_tags_list,
                remove_invisible=True,
                remove_empty=True,
                clean_attrs=True,
                keep_attrs=keep_attrs_list
            )
        # 根据aggressive参数选择模式
        elif aggressive:
            # 激进模式：删除所有无用内容
            result = simplify_html_minimal(
                html_str=html_str,
                remove_tags=None,  # 使用默认删除列表
                remove_invisible=True,
                remove_empty=True,
                clean_attrs=True,
                keep_attrs=keep_attrs  # 只保留指定的属性
            )
        else:
            # 保守模式：只删除明显无用的内容
            result = simplify_html_minimal(
                html_str=html_str,
                remove_tags=['script', 'style', 'head', 'noscript'],
                remove_invisible=True,
                remove_empty=True,
                clean_attrs=False,  # 不清理属性
                keep_attrs=None
            )

        return result

    except Exception as e:
        error_msg = f"HTML 精简失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


# ============================================
# LangChain Tool 封装
# ============================================

@tool
def simplify_html_tool(
    html_str: str,
    keep_attrs: List[str] = None,
    aggressive: bool = True,
    mode: str = 'default'
) -> str:
    """
    精简 HTML，删除无用标签和属性，使其更易于处理和分析

    这是 LangChain tool 版本，可以在 Agent 中使用

    Args:
        html_str: 原始 HTML 字符串
        keep_attrs: 要保留的属性列表，例如 ['class', 'id', 'href']。None 表示删除所有属性
        aggressive: 是否使用激进模式（删除更多标签和清理所有属性）
        mode: 精简模式 ('default', 'xpath')

    Returns:
        精简后的 HTML 字符串
    """
    return simplify_html(html_str, keep_attrs, aggressive, mode)


# ============================================
# 便捷函数（非 tool）
# ============================================

def simplify_html_for_llm(html_str: str) -> str:
    """
    为 LLM 处理优化的 HTML 精简
    删除所有属性，只保留结构和文本内容

    Args:
        html_str: 原始 HTML 字符串

    Returns:
        精简后的 HTML 字符串
    """
    return simplify_html_minimal(
        html_str=html_str,
        remove_tags=None,
        remove_invisible=True,
        remove_empty=True,
        clean_attrs=True,
        keep_attrs=[]  # 不保留任何属性
    )


def simplify_html_keep_structure(html_str: str) -> str:
    """
    保留结构信息的 HTML 精简
    保留 class 和 id 属性，用于定位元素

    Args:
        html_str: 原始 HTML 字符串

    Returns:
        精简后的 HTML 字符串
    """
    return simplify_html_minimal(
        html_str=html_str,
        remove_tags=None,
        remove_invisible=True,
        remove_empty=True,
        clean_attrs=True,
        keep_attrs=['class', 'id']
    )
