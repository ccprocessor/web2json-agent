"""
Agent 编排器
整合规划器、执行器和验证器，提供统一的Agent接口
"""
from typing import List, Dict
from pathlib import Path
from loguru import logger
from .planner import AgentPlanner
from .executor import AgentExecutor
from .validator import AgentValidator
from config.settings import settings
from tools import fix_parser_code


class ParserAgent:
    """
    HTML解析器生成Agent
    
    通过给定一组URL，自动生成能够解析这些页面的Python代码
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化Agent
        
        Args:
            output_dir: 输出目录
        """
        self.planner = AgentPlanner()
        self.executor = AgentExecutor(output_dir)
        self.validator = AgentValidator()
        self.output_dir = Path(output_dir)
        
        logger.info("ParserAgent 初始化完成")
    
    def generate_parser(
        self,
        urls: List[str],
        domain: str = None,
        layout_type: str = None,
        validate: bool = True
    ) -> Dict:
        """
        生成解析器

        流程：
        1. 规划：分析URL并制定执行计划
        2. 执行：
           - 阶段1: Schema迭代（前N个URL）- 提取并优化Schema
           - 阶段2: 代码迭代（后M个URL）- 生成并优化解析代码
        3. 验证：基于groundtruth对比验证解析器准确率
        4. 总结：生成执行总结

        Args:
            urls: URL列表
            domain: 域名（可选）
            layout_type: 布局类型（可选）
            validate: 是否验证生成的代码

        Returns:
            生成结果
        """
        logger.info("="*70)
        logger.info("开始生成解析器")
        logger.info("="*70)

        # 第一步：规划
        logger.info("\n[步骤 1/4] 任务规划")
        plan = self.planner.create_plan(urls, domain, layout_type)

        # 第二步：执行（两阶段迭代）
        logger.info("\n[步骤 2/4] 执行计划 - 两阶段迭代")
        execution_result = self.executor.execute_plan(plan)

        if not execution_result['success']:
            logger.error("执行失败，无法生成解析器")
            return {
                'success': False,
                'error': '执行失败',
                'execution_result': execution_result
            }

        # 第三步：验证（基于groundtruth对比）
        validation_result = None
        if validate:
            logger.info("\n[步骤 3/4] 验证解析器 - 基于groundtruth对比")
            parser_path = execution_result['final_parser']['parser_path']

            # 合并两个阶段的轮次数据用于验证
            all_rounds = (
                execution_result['schema_phase']['rounds'] +
                execution_result['code_phase']['rounds']
            )

            # 检查是否有可用的 groundtruth
            has_groundtruth = any(
                r.get('success') and r.get('groundtruth_schema')
                for r in all_rounds
            )

            if not has_groundtruth:
                logger.warning("没有可用的 groundtruth 数据，跳过验证步骤")
                logger.info("提示：当前版本Schema迭代阶段不生成groundtruth，验证功能暂时禁用")
            else:
                # 使用合并后的轮次数据进行 groundtruth 验证
                validation_result = self.validator.validate_parser_with_groundtruth(
                    parser_path,
                    all_rounds
                )

                # 如果验证未通过，尝试迭代优化
                if not validation_result['passed']:
                    logger.warning("初次验证未通过，尝试优化...")
                    validation_result = self._iterate_and_improve(
                        execution_result,
                        validation_result,
                        plan
                    )

        # 第四步：总结
        logger.info("\n[步骤 4/4] 生成总结")
        summary = self._generate_summary(execution_result, validation_result)

        logger.info("="*70)
        logger.success("解析器生成完成!")
        logger.info("="*70)

        return {
            'success': True,
            'plan': plan,
            'execution_result': execution_result,
            'validation_result': validation_result,
            'summary': summary,
            'parser_path': execution_result['final_parser']['parser_path'],
            'config_path': execution_result['final_parser'].get('config_path'),
        }
    
    def _iterate_and_improve(
        self,
        execution_result: Dict,
        validation_result: Dict,
        plan: Dict
    ) -> Dict:
        """
        迭代优化解析器

        策略：
        1. 分析验证失败的原因
        2. 使用LLM修复代码
        3. 重新验证（基于groundtruth对比）
        4. 重复直到达到成功率阈值或最大迭代次数
        """
        max_iterations = plan.get('max_iterations', settings.max_iterations)
        current_validation = validation_result
        current_parser_path = execution_result['final_parser']['parser_path']
        current_code = execution_result['final_parser']['code']

        logger.info(f"开始迭代优化，最大迭代次数: {max_iterations}")

        for iteration in range(1, max_iterations):
            logger.info(f"\n{'='*70}")
            logger.info(f"优化迭代 {iteration}/{max_iterations-1}")
            logger.info(f"当前准确率: {current_validation['success_rate']:.1%}")
            logger.info(f"目标准确率: {settings.success_threshold:.1%}")
            logger.info(f"{'='*70}")

            # 如果已经达到成功率阈值，停止迭代
            if current_validation['passed']:
                logger.success(f"已达到成功率阈值，停止迭代")
                break

            # 收集验证错误
            validation_errors = self._collect_validation_errors(current_validation)

            if not validation_errors:
                logger.warning("没有具体的错误信息，无法继续优化")
                break

            logger.info(f"发现 {len(validation_errors)} 个验证错误")

            # 使用LLM修复代码
            logger.info("调用LLM修复代码...")
            fix_result = fix_parser_code.invoke({
                "original_code": current_code,
                "validation_errors": validation_errors,
                "target_json": execution_result['final_parser'].get('config', {}),
                "html_sample": None  # 可以传入HTML样本
            })

            if not fix_result.get('success'):
                logger.error(f"代码修复失败: {fix_result.get('error')}")
                break

            # 保存修复后的代码
            fixed_code = fix_result['fixed_code']
            logger.info("保存修复后的代码...")

            # 更新解析器文件
            with open(current_parser_path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)

            logger.success(f"代码已更新: {current_parser_path}")

            # 重新验证（基于groundtruth对比）
            logger.info("重新验证修复后的代码...")
            new_validation = self.validator.validate_parser_with_groundtruth(
                current_parser_path,
                execution_result['rounds']
            )

            # 检查是否有改进
            old_rate = current_validation['success_rate']
            new_rate = new_validation['success_rate']

            logger.info(f"准确率变化: {old_rate:.1%} -> {new_rate:.1%}")

            if new_rate > old_rate:
                logger.success(f"✓ 准确率提升了 {(new_rate - old_rate):.1%}")
                current_validation = new_validation
                current_code = fixed_code

                # 更新execution_result中的代码
                execution_result['final_parser']['code'] = fixed_code
            elif new_rate == old_rate:
                logger.warning("准确率没有变化")
                current_validation = new_validation
                current_code = fixed_code
            else:
                logger.error(f"✗ 准确率下降了 {(old_rate - new_rate):.1%}，回滚修改")
                # 回滚代码
                with open(current_parser_path, 'w', encoding='utf-8') as f:
                    f.write(current_code)
                logger.info("已回滚到上一个版本")
                break

        return current_validation

    def _collect_validation_errors(self, validation_result: Dict) -> List[Dict]:
        """收集验证错误信息"""
        errors = []

        for test in validation_result.get('tests', []):
            if not test.get('success'):
                errors.append({
                    'url': test.get('url'),
                    'error': test.get('error', 'Unknown error'),
                    'details': test.get('details', '')
                })

        return errors
    
    def _generate_summary(self, execution_result: Dict, validation_result: Dict = None) -> str:
        """生成执行总结"""
        lines = []
        lines.append("\n" + "="*70)
        lines.append("执行总结")
        lines.append("="*70)

        # Schema迭代阶段结果
        schema_phase = execution_result.get('schema_phase', {})
        schema_rounds = schema_phase.get('rounds', [])
        schema_success_rounds = [r for r in schema_rounds if r.get('success')]
        lines.append(f"\nSchema迭代阶段: {len(schema_success_rounds)}/{len(schema_rounds)} 轮成功")

        if schema_phase.get('final_schema'):
            final_schema_size = len(schema_phase['final_schema'])
            lines.append(f"  最终Schema字段数: {final_schema_size}")

        if schema_phase.get('final_schema_path'):
            lines.append(f"  最终Schema路径: {schema_phase['final_schema_path']}")

        # 代码迭代阶段结果
        code_phase = execution_result.get('code_phase', {})
        code_rounds = code_phase.get('rounds', [])
        code_success_rounds = [r for r in code_rounds if r.get('success')]
        lines.append(f"\n代码迭代阶段: {len(code_success_rounds)}/{len(code_rounds)} 轮成功")

        # 解析器生成结果
        if execution_result.get('final_parser'):
            parser_path = execution_result['final_parser']['parser_path']
            lines.append(f"\n最终解析器路径: {parser_path}")

        # 验证结果
        if validation_result:
            accuracy = validation_result.get('success_rate', 0)
            passed = validation_result.get('passed', False)
            lines.append(f"\n验证结果: {'通过' if passed else '未通过'}")
            lines.append(f"平均准确率: {accuracy:.1%}")

            # 显示每一轮的准确率
            accuracy_details = validation_result.get('accuracy_details', {})
            if accuracy_details:
                lines.append("  各轮准确率：")
                for round_key, details in accuracy_details.items():
                    round_acc = details.get('accuracy', 0)
                    lines.append(f"    {round_key}: {round_acc:.1%}")

        lines.append("="*70)

        summary = "\n".join(lines)
        logger.info(summary)

        return summary

