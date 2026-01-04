"""
XPath生成相关模型
"""
from typing import List, Optional
from pydantic import BaseModel, Field

from .field import FieldInput, FieldOutput


class XPathGenerateRequest(BaseModel):
    """
    XPath生成请求

    支持多样本输入（提高XPath准确率）：
    1. 多个HTML内容 (html_contents)
    2. 多个URL (urls)
    3. 单个HTML内容 (html_content) - 兼容旧版
    4. 单个URL (url) - 兼容旧版

    以及需要抽取的字段列表
    """
    # 多样本输入（推荐）
    html_contents: Optional[List[str]] = Field(None, description="多个HTML内容（推荐：2-5个样本）")
    urls: Optional[List[str]] = Field(None, description="多个网页URL（推荐：2-5个样本）")

    # 单样本输入（向后兼容）
    html_content: Optional[str] = Field(None, description="单个HTML内容（兼容旧版）")
    url: Optional[str] = Field(None, description="单个网页URL（兼容旧版）")

    fields: List[FieldInput] = Field(..., description="需要抽取的字段列表")
    iteration_rounds: Optional[int] = Field(None, description="迭代轮数（默认使用所有样本）")

    class Config:
        json_schema_extra = {
            "example": {
                "html_contents": [
                    "<html><body><h1>Title 1</h1><span class='price'>$99.99</span></body></html>",
                    "<html><body><h1>Title 2</h1><span class='price'>$89.99</span></body></html>"
                ],
                "urls": None,
                "fields": [
                    {"name": "title", "description": "Page title", "field_type": "string"},
                    {"name": "price", "description": "Product price", "field_type": "string"}
                ],
                "iteration_rounds": 2
            }
        }


class XPathGenerateResponse(BaseModel):
    """
    XPath生成响应

    返回每个字段对应的XPath表达式
    """
    success: bool = Field(..., description="是否成功")
    fields: List[FieldOutput] = Field(..., description="包含生成XPath的字段列表")
    error: Optional[str] = Field(None, description="错误信息")
    message: Optional[str] = Field(None, description="提示信息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "fields": [
                    {
                        "name": "title",
                        "description": "Page title",
                        "field_type": "string",
                        "xpath": "//h1/text()",
                        "value_sample": ["Title"]
                    },
                    {
                        "name": "price",
                        "description": "Product price",
                        "field_type": "string",
                        "xpath": "//span[@class='price']/text()",
                        "value_sample": ["$99.99"]
                    }
                ],
                "error": None,
                "message": "Successfully generated XPath for 2 fields"
            }
        }
