"""
简化的字段定义模型
"""
from typing import Optional, Literal, List
from pydantic import BaseModel, Field


class FieldInput(BaseModel):
    """
    用户输入的字段定义（前端 -> 后端）
    """
    name: str = Field(..., description="字段名（必填）")
    description: Optional[str] = Field(None, description="字段描述（可选，提高抽取准确率）")
    field_type: Literal["string", "int", "float", "bool", "array"] = Field(
        "string",
        description="字段类型"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "price",
                "description": "Product price",
                "field_type": "string"
            }
        }


class FieldOutput(BaseModel):
    """
    返回给前端的字段（包含生成的XPath）
    """
    name: str
    description: Optional[str] = None
    field_type: str = "string"
    xpath: str = Field(..., description="生成的XPath表达式")
    value_sample: List[str] = Field(default_factory=list, description="示例值")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "price",
                "description": "Product price",
                "field_type": "string",
                "xpath": "//span[@class='price']/text()",
                "value_sample": ["$99.99"]
            }
        }
