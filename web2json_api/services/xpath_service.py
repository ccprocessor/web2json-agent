"""
XPath生成服务

支持多样本迭代学习，提高XPath准确率
"""
from typing import List, Dict, Optional
from loguru import logger

from web2json.tools.schema_extraction import enrich_schema_with_xpath, merge_multiple_schemas
from web2json_api.models.field import FieldInput, FieldOutput


class XPathService:
    """
    XPath生成服务

    核心功能：
    1. 支持多样本输入（HTML内容）
    2. 对每个样本调用agent生成schema
    3. 合并多个schema，生成最优XPath
    4. 返回前端需要的格式
    """

    @staticmethod
    def collect_html_samples(
        html_contents: Optional[List[str]],
        html_content: Optional[str]
    ) -> List[str]:
        """
        收集所有HTML样本

        Args:
            html_contents: 多个HTML内容
            html_content: 单个HTML内容（兼容）

        Returns:
            HTML样本列表

        Raises:
            ValueError: 没有提供任何输入时
        """
        samples = []

        # 1. 收集多个HTML内容
        if html_contents:
            samples.extend(html_contents)
            logger.info(f"收集到 {len(html_contents)} 个HTML内容")

        # 2. 兼容单个HTML内容
        if html_content:
            samples.append(html_content)
            logger.info("收集到1个HTML内容（单样本模式）")

        if not samples:
            raise ValueError("必须提供至少一个HTML内容")

        logger.info(f"总共收集到 {len(samples)} 个HTML样本")
        return samples

    @staticmethod
    def generate_xpaths_with_iteration(
        html_samples: List[str],
        fields: List[FieldInput],
        iteration_rounds: Optional[int] = None
    ) -> List[FieldOutput]:
        """
        使用多样本迭代生成XPath

        流程：
        1. 对每个样本调用enrich_schema_with_xpath
        2. 合并所有schema
        3. 提取最优XPath

        Args:
            html_samples: HTML样本列表
            fields: 用户定义的字段列表
            iteration_rounds: 迭代轮数（None表示使用所有样本）

        Returns:
            包含XPath的字段列表
        """
        try:
            # 1. 确定迭代轮数
            if iteration_rounds is None:
                iteration_rounds = len(html_samples)
            else:
                iteration_rounds = min(iteration_rounds, len(html_samples))

            logger.info(f"开始为 {len(fields)} 个字段生成XPath（使用 {iteration_rounds} 个样本）")

            # 2. 构建schema模板
            schema_template = {}
            for field in fields:
                schema_template[field.name] = {
                    "type": field.field_type,
                    "description": field.description or "",
                    "value_sample": [],
                    "xpaths": [""]
                }

            logger.info(f"Schema模板字段: {list(schema_template.keys())}")

            # 3. 对每个样本调用agent生成schema
            enriched_schemas = []
            for i, html_content in enumerate(html_samples[:iteration_rounds]):
                logger.info(f"处理第 {i+1}/{iteration_rounds} 个样本...")

                enriched_schema = enrich_schema_with_xpath.invoke({
                    "schema_template": schema_template,
                    "html_content": html_content
                })

                enriched_schemas.append(enriched_schema)
                logger.success(f"第 {i+1} 个样本处理完成")

            # 4. 如果只有一个样本，直接使用
            if len(enriched_schemas) == 1:
                logger.info("单样本模式，直接使用生成的schema")
                final_schema = enriched_schemas[0]
            else:
                # 5. 合并多个schema
                logger.info(f"合并 {len(enriched_schemas)} 个schema...")
                final_schema = merge_multiple_schemas.invoke({
                    "schemas": enriched_schemas
                })
                logger.success("Schema合并完成")

            # 6. 转换回前端格式
            output_fields = []
            for field in fields:
                field_name = field.name
                if field_name in final_schema:
                    enriched_data = final_schema[field_name]

                    # 提取XPath（可能是列表，取第一个）
                    xpaths = enriched_data.get("xpaths", [""])
                    if isinstance(xpaths, list) and xpaths:
                        xpath = xpaths[0]
                    else:
                        xpath = str(xpaths or "")

                    # 提取value_sample（可能是列表或字符串）
                    value_sample_raw = enriched_data.get("value_sample", [])
                    if isinstance(value_sample_raw, list):
                        value_sample = value_sample_raw
                    elif value_sample_raw:
                        value_sample = [str(value_sample_raw)]
                    else:
                        value_sample = []

                    output_fields.append(FieldOutput(
                        name=field_name,
                        description=field.description,
                        field_type=field.field_type,
                        xpath=xpath,
                        value_sample=value_sample
                    ))
                else:
                    # 如果agent没有返回该字段，使用空XPath
                    logger.warning(f"字段 {field_name} 未在返回结果中找到")
                    output_fields.append(FieldOutput(
                        name=field_name,
                        description=field.description,
                        field_type=field.field_type,
                        xpath="",
                        value_sample=[]
                    ))

            logger.success(f"成功为 {len(output_fields)} 个字段生成XPath")
            return output_fields

        except Exception as e:
            logger.error(f"生成XPath失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise Exception(f"XPath生成失败: {str(e)}")

    @staticmethod
    def generate_xpaths(
        html_contents: Optional[List[str]],
        html_content: Optional[str],
        fields: List[FieldInput],
        iteration_rounds: Optional[int] = None
    ) -> List[FieldOutput]:
        """
        生成XPath（统一入口）

        Args:
            html_contents: 多个HTML内容
            html_content: 单个HTML内容（兼容）
            fields: 字段列表
            iteration_rounds: 迭代轮数

        Returns:
            包含XPath的字段列表
        """
        # 1. 收集所有HTML样本
        html_samples = XPathService.collect_html_samples(
            html_contents, html_content
        )

        # 2. 使用迭代方式生成XPath
        return XPathService.generate_xpaths_with_iteration(
            html_samples, fields, iteration_rounds
        )


# 全局实例
xpath_service = XPathService()
