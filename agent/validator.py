"""
Agent 验证器
负责验证生成的解析代码是否正确
"""
import sys
import os
import json
import importlib.util
from typing import Dict, List
from loguru import logger
from tools import get_webpage_source
from langchain_openai import ChatOpenAI
from config.settings import settings


class AgentValidator:
    """Agent验证器，负责验证和优化生成的代码"""

    def __init__(self):
        # 使用 LangChain 1.0 的 ChatOpenAI
        self.llm = ChatOpenAI(
            model=settings.agent_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            temperature=settings.agent_temperature
        )
    
    def validate_parser_with_groundtruth(self, parser_path: str, rounds: List[Dict], output_dir: str = "output") -> Dict:
        """
        基于 groundtruth 验证解析器

        使用图片识别的 JSON Schema 作为 groundtruth，对比解析器生成的 JSON 与 groundtruth 的准确率

        Args:
            parser_path: 解析器代码路径
            rounds: 执行轮次列表（包含每一轮的 groundtruth_schema 和 html）
            output_dir: 输出目录

        Returns:
            验证结果
        """
        logger.info(f"基于 groundtruth 验证解析器: {parser_path}")

        results = {
            'parser_path': parser_path,
            'tests': [],
            'success_rate': 0.0,
            'passed': False,
            'issues': [],
            'accuracy_details': {}
        }

        # 加载解析器
        try:
            parser_class = self._load_parser(parser_path)
        except Exception as e:
            logger.error(f"加载解析器失败: {str(e)}")
            results['issues'].append(f"加载失败: {str(e)}")
            return results

        # 对每一轮进行验证
        total_accuracy = 0
        valid_rounds = 0

        for round_result in rounds:
            if not round_result.get('success'):
                continue

            round_num = round_result['round']
            html = round_result['html']
            groundtruth_schema = round_result.get('groundtruth_schema', {})

            if not groundtruth_schema:
                logger.warning(f"第 {round_num} 轮没有 groundtruth_schema，跳过")
                continue

            logger.info(f"  验证第 {round_num} 轮...")

            test_result = self._compare_with_groundtruth(
                parser_class,
                html,
                groundtruth_schema,
                round_num
            )

            results['tests'].append(test_result)
            results['accuracy_details'][f'round_{round_num}'] = {
                'accuracy': test_result['accuracy'],
                'matched_fields': test_result['matched_fields'],
                'missing_fields': test_result['missing_fields'],
                'extra_fields': test_result['extra_fields']
            }

            total_accuracy += test_result['accuracy']
            valid_rounds += 1

        # 计算平均成功率
        if valid_rounds > 0:
            results['success_rate'] = total_accuracy / valid_rounds

        results['passed'] = results['success_rate'] >= settings.success_threshold

        if results['passed']:
            logger.success(f"验证通过! 平均准确率: {results['success_rate']:.1%}")
        else:
            logger.warning(f"验证未通过. 平均准确率: {results['success_rate']:.1%}, 阈值: {settings.success_threshold:.1%}")

        return results

    def _compare_with_groundtruth(self, parser, html: str, groundtruth_schema: Dict, round_num: int) -> Dict:
        """
        对比解析结果与 groundtruth

        Args:
            parser: 解析器实例
            html: HTML 内容
            groundtruth_schema: 从图片识别得到的 groundtruth JSON Schema
            round_num: 轮次号

        Returns:
            对比结果
        """
        result = {
            'round': round_num,
            'accuracy': 0.0,
            'matched_fields': [],
            'missing_fields': [],
            'extra_fields': [],
            'error': None,
            'details': ''
        }

        try:
            # 使用解析器解析 HTML
            predicted_data = parser.parse(html)

            if not predicted_data or not isinstance(predicted_data, dict):
                result['error'] = "解析结果为空或格式错误"
                result['details'] = f"返回类型: {type(predicted_data)}"
                logger.warning(f"  ✗ 第 {round_num} 轮解析失败: {result['error']}")
                return result

            # 提取 groundtruth 中的字段名
            groundtruth_fields = set(groundtruth_schema.keys())
            # 提取预测数据中的字段名
            predicted_fields = set(predicted_data.keys())

            # 计算匹配、缺失和额外的字段
            matched = groundtruth_fields & predicted_fields
            missing = groundtruth_fields - predicted_fields
            extra = predicted_fields - groundtruth_fields

            result['matched_fields'] = list(matched)
            result['missing_fields'] = list(missing)
            result['extra_fields'] = list(extra)

            # 计算准确率（匹配字段数 / groundtruth 字段数）
            if groundtruth_fields:
                result['accuracy'] = len(matched) / len(groundtruth_fields)
            else:
                result['accuracy'] = 0.0

            # 详细信息
            details = [
                f"预测字段数: {len(predicted_fields)}",
                f"Groundtruth 字段数: {len(groundtruth_fields)}",
                f"匹配字段: {len(matched)} {list(matched)[:3]}{'...' if len(matched) > 3 else ''}",
                f"缺失字段: {len(missing)} {list(missing)[:3]}{'...' if len(missing) > 3 else ''}",
                f"额外字段: {len(extra)} {list(extra)[:3]}{'...' if len(extra) > 3 else ''}",
            ]
            result['details'] = " | ".join(details)

            logger.success(f"  ✓ 第 {round_num} 轮准确率: {result['accuracy']:.1%} - {result['details']}")

        except Exception as e:
            import traceback
            result['error'] = str(e)
            result['details'] = traceback.format_exc()
            logger.error(f"  ✗ 第 {round_num} 轮验证失败: {str(e)}")

        return result

    def validate_parser(self, parser_path: str, test_urls: List[str]) -> Dict:
        """
        验证解析器
        
        Args:
            parser_path: 解析器代码路径
            test_urls: 测试URL列表
        
        Returns:
            验证结果
        """
        logger.info(f"验证解析器: {parser_path}")
        
        results = {
            'parser_path': parser_path,
            'tests': [],  # 使用'tests'而不是'test_results'以保持一致性
            'test_results': [],  # 保留向后兼容
            'success_rate': 0.0,
            'passed': False,
            'issues': [],
        }

        # 加载解析器
        try:
            parser_class = self._load_parser(parser_path)
        except Exception as e:
            logger.error(f"加载解析器失败: {str(e)}")
            results['issues'].append(f"加载失败: {str(e)}")
            return results

        # 测试每个URL
        success_count = 0
        for url in test_urls:
            test_result = self._test_url(parser_class, url)
            results['tests'].append(test_result)
            results['test_results'].append(test_result)  # 向后兼容
            if test_result['success']:
                success_count += 1

        # 计算成功率
        results['success_rate'] = success_count / len(test_urls) if test_urls else 0
        results['passed'] = results['success_rate'] >= settings.success_threshold
        
        if results['passed']:
            logger.success(f"验证通过! 成功率: {results['success_rate']:.1%}")
        else:
            logger.warning(f"验证未通过. 成功率: {results['success_rate']:.1%}, 阈值: {settings.success_threshold:.1%}")
        
        return results
    
    def _load_parser(self, parser_path: str):
        """动态加载解析器类"""
        spec = importlib.util.spec_from_file_location("parser_module", parser_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["parser_module"] = module
        spec.loader.exec_module(module)
        
        # 获取WebPageParser类
        if hasattr(module, 'WebPageParser'):
            return module.WebPageParser()
        else:
            raise Exception("解析器中未找到WebPageParser类")
    
    def _test_url(self, parser, url: str) -> Dict:
        """测试单个URL"""
        result = {
            'url': url,
            'success': False,
            'data': None,
            'error': None,
            'details': '',  # 添加详细信息字段
        }

        try:
            logger.info(f"  测试URL: {url}")

            # 获取HTML - 使用 .invoke() 调用工具
            html = get_webpage_source.invoke({"url": url})

            # 解析
            data = parser.parse(html)

            # 检查结果
            if data and isinstance(data, dict) and len(data) > 0:
                result['success'] = True
                result['data'] = data
                result['details'] = f"成功提取 {len(data)} 个字段: {', '.join(data.keys())}"
                logger.success(f"  ✓ 解析成功，提取 {len(data)} 个字段")
            else:
                result['error'] = "解析结果为空或格式错误"
                result['details'] = f"返回类型: {type(data)}, 内容: {str(data)[:100]}"
                logger.warning(f"  ✗ {result['error']}")

        except Exception as e:
            import traceback
            result['error'] = str(e)
            result['details'] = traceback.format_exc()
            logger.error(f"  ✗ 解析失败: {str(e)}")

        return result
    
    def diagnose_issues(self, validation_result: Dict) -> List[str]:
        """
        诊断验证中发现的问题
        
        Args:
            validation_result: 验证结果
        
        Returns:
            问题诊断列表
        """
        issues = []
        
        # 分析失败的测试
        failed_tests = [t for t in validation_result.get('tests', []) if t.get('error')]

        if not failed_tests:
            return issues
        
        # 统计错误类型
        error_types = {}
        for test in failed_tests:
            error = test.get('error', 'Unknown error')
            error_types[error] = error_types.get(error, 0) + 1
        
        # 生成诊断
        for error, count in error_types.items():
            issues.append(f"{count} 个轮次出现错误: {error}")

        return issues
    
    def suggest_improvements(self, validation_result: Dict, parser_code: str) -> str:
        """
        基于验证结果建议改进方案
        
        Args:
            validation_result: 验证结果
            parser_code: 当前解析器代码
        
        Returns:
            改进建议
        """
        issues = self.diagnose_issues(validation_result)
        
        if not issues:
            return "代码运行良好，无需改进"
        
        # 使用LLM分析问题并给出建议
        prompt = f"""
解析器验证发现以下问题：
{chr(10).join([f"- {issue}" for issue in issues])}

当前解析器代码片段：
```python
{parser_code[:1000]}...
```

请分析可能的原因并给出改进建议。
"""

        messages = [
            {"role": "system", "content": "你是一个专业的代码审查和优化助手。"},
            {"role": "user", "content": prompt}
        ]
        response = self.llm.invoke(messages)

        return response.content

