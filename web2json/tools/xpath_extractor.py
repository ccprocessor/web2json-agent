"""
XPath提取器
从生成的parser代码中提取xpath表达式，生成字段-xpath映射
"""
import ast
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from loguru import logger

from web2json.utils.llm_client import LLMClient
from web2json.prompts.xpath_extraction import XPathExtractionPrompts


class XPathExtractor:
    """从parser代码中提取xpath表达式"""

    def extract_from_parser(self, parser_path: str) -> Dict[str, List[str]]:
        """
        从parser代码中提取xpath表达式

        Args:
            parser_path: parser文件路径

        Returns:
            字段到xpath列表的映射
            格式: {
                "field_name": ["xpath1", "xpath2", ...],
                ...
            }
        """
        parser_file = Path(parser_path)
        if not parser_file.exists():
            logger.error(f"Parser文件不存在: {parser_path}")
            return {}

        # 读取parser代码
        try:
            with open(parser_file, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            logger.error(f"读取parser文件失败: {e}")
            return {}

        # 解析AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.error(f"解析parser代码失败: {e}")
            return {}

        # 提取xpath
        field_xpaths = self._extract_xpaths_from_ast(tree)

        logger.info(f"从parser中提取了 {len(field_xpaths)} 个字段的xpath")
        return field_xpaths

    def _extract_xpaths_from_ast(self, tree: ast.AST) -> Dict[str, List[str]]:
        """
        从AST中提取xpath表达式

        分析逻辑：
        1. 找到WebPageParser类
        2. 找到所有_extract_xxx方法
        3. 在方法中查找tree.xpath()调用
        4. 提取xpath字符串
        """
        field_xpaths = {}

        # 遍历所有类定义
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'WebPageParser':
                # 遍历类中的所有方法
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # 提取字段名（从_extract_xxx提取xxx）
                        method_name = item.name
                        if method_name.startswith('_extract_'):
                            field_name = method_name[len('_extract_'):]

                            # 提取该方法中的所有xpath
                            xpaths = self._extract_xpaths_from_method(item)
                            if xpaths:
                                field_xpaths[field_name] = xpaths

        return field_xpaths

    def _extract_xpaths_from_method(self, method_node: ast.FunctionDef) -> List[str]:
        """
        从方法AST节点中提取所有xpath表达式

        查找模式：
        - tree.xpath("...")
        - tree.xpath('...')
        """
        xpaths = []

        for node in ast.walk(method_node):
            # 查找方法调用：tree.xpath(...)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # 检查是否是xpath方法
                    if node.func.attr == 'xpath':
                        # 检查是否是tree对象调用
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id == 'tree':
                                # 提取xpath字符串参数
                                if node.args and len(node.args) > 0:
                                    arg = node.args[0]
                                    if isinstance(arg, ast.Constant):
                                        xpath = arg.value
                                        if isinstance(xpath, str):
                                            xpaths.append(xpath)
                                    elif isinstance(arg, ast.Str):  # Python 3.7兼容
                                        xpaths.append(arg.s)

        return xpaths

    def save_xpaths_to_json(self, field_xpaths: Dict[str, List[str]], output_path: str):
        """
        保存xpath映射到JSON文件

        Args:
            field_xpaths: 字段到xpath列表的映射
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(field_xpaths, f, ensure_ascii=False, indent=2)
            logger.success(f"XPath映射已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存xpath映射失败: {e}")

    def extract_and_save(self, parser_path: str, output_path: str) -> bool:
        """
        提取xpath并保存到JSON文件

        Args:
            parser_path: parser文件路径
            output_path: 输出JSON文件路径

        Returns:
            是否成功
        """
        logger.info(f"开始从parser中提取xpath: {parser_path}")

        # 提取xpath
        field_xpaths = self.extract_from_parser(parser_path)

        if not field_xpaths:
            logger.warning("未能提取到任何xpath")
            return False

        # 保存到JSON
        self.save_xpaths_to_json(field_xpaths, output_path)

        # 打印摘要
        logger.info("\n" + "="*50)
        logger.info("XPath提取摘要:")
        logger.info("="*50)
        for field, xpaths in field_xpaths.items():
            logger.info(f"  {field}: {len(xpaths)} 个xpath")
            for i, xpath in enumerate(xpaths, 1):
                logger.info(f"    {i}. {xpath}")
        logger.info("="*50 + "\n")

        return True

    def extract_from_parser_with_llm(self, parser_path: str) -> Dict[str, str]:
        """
        使用LLM从parser代码中提取最优xpath表达式

        Args:
            parser_path: parser文件路径

        Returns:
            字段到最优xpath的映射
            格式: {
                "field_name": "xpath_expression",
                ...
            }
        """
        parser_file = Path(parser_path)
        if not parser_file.exists():
            logger.error(f"Parser文件不存在: {parser_path}")
            return {}

        # 读取parser代码
        try:
            with open(parser_file, 'r', encoding='utf-8') as f:
                parser_code = f.read()
        except Exception as e:
            logger.error(f"读取parser文件失败: {e}")
            return {}

        # 创建LLM客户端
        llm = LLMClient.for_scenario("default")

        # 构建prompt
        prompt = XPathExtractionPrompts.get_xpath_extraction_prompt(parser_code)

        # 调用LLM
        try:
            logger.info("调用LLM提取最优XPath表达式...")
            messages = [{"role": "user", "content": prompt}]
            response = llm.chat_completion(messages)

            # 解析JSON响应
            # 尝试提取JSON部分（可能有```json标记）
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            # 解析JSON
            field_xpaths = json.loads(response)

            logger.success(f"成功提取 {len(field_xpaths)} 个字段的最优XPath")
            return field_xpaths

        except json.JSONDecodeError as e:
            logger.error(f"解析LLM响应失败: {e}")
            logger.debug(f"LLM响应: {response}")
            return {}
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return {}

    def extract_and_save_with_llm(self, parser_path: str, output_path: str) -> bool:
        """
        使用LLM提取最优xpath并保存到JSON文件

        Args:
            parser_path: parser文件路径
            output_path: 输出JSON文件路径

        Returns:
            是否成功
        """
        logger.info(f"开始使用LLM从parser中提取最优XPath: {parser_path}")

        # 提取xpath
        field_xpaths = self.extract_from_parser_with_llm(parser_path)

        if not field_xpaths:
            logger.warning("未能提取到任何xpath")
            return False

        # 保存到JSON
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(field_xpaths, f, ensure_ascii=False, indent=2)
            logger.success(f"最优XPath映射已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存xpath映射失败: {e}")
            return False

        # 打印摘要
        logger.info("\n" + "="*50)
        logger.info("最优XPath提取摘要:")
        logger.info("="*50)
        for field, xpath in field_xpaths.items():
            logger.info(f"  {field}: {xpath}")
        logger.info("="*50 + "\n")

        return True


def extract_xpaths_from_parser(parser_path: str, output_path: str = None) -> Dict[str, List[str]]:
    """
    便捷函数：从parser代码中提取xpath

    Args:
        parser_path: parser文件路径
        output_path: 可选，输出JSON文件路径

    Returns:
        字段到xpath列表的映射
    """
    extractor = XPathExtractor()

    if output_path:
        extractor.extract_and_save(parser_path, output_path)

    return extractor.extract_from_parser(parser_path)
