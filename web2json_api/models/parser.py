"""
完整解析器生成相关模型
"""
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

from .field import FieldInput


class ParserGenerateRequest(BaseModel):
    """
    完整解析器生成请求

    支持多样本输入：
    1. 多个HTML内容 (html_contents)
    2. 多个URL (urls)
    3. 单个HTML内容 (html_content) - 兼容旧版
    4. 单个URL (url) - 兼容旧版

    Schema 模式：
    - auto: AI自动发现所有字段
    - predefined: 用户指定要提取的字段
    """
    # 多样本输入
    html_contents: Optional[List[str]] = Field(None, description="多个HTML内容")
    urls: Optional[List[str]] = Field(None, description="多个网页URL")

    # 单样本输入（向后兼容）
    html_content: Optional[str] = Field(None, description="单个HTML内容（兼容旧版）")
    url: Optional[str] = Field(None, description="单个网页URL（兼容旧版）")

    # 字段定义（仅predefined模式需要）
    fields: List[FieldInput] = Field(default_factory=list, description="需要抽取的字段列表（predefined模式必填）")

    # 解析器生成选项
    schema_mode: Literal["auto", "predefined"] = Field(
        "auto",
        description="Schema模式：auto=自动发现字段，predefined=用户指定字段"
    )
    domain: Optional[str] = Field("web_parser", description="域名或解析器名称")
    iteration_rounds: Optional[int] = Field(None, description="迭代轮数（Schema学习的样本数，默认3）")

    # 高级选项
    html_simplify_mode: Optional[str] = Field(None, description="HTML简化模式：xpath/aggressive/conservative")

    class Config:
        json_schema_extra = {
            "example": {
                "html_contents": [
                    "<html><body><h1>Title 1</h1><div class='content'>Content 1</div></body></html>",
                    "<html><body><h1>Title 2</h1><div class='content'>Content 2</div></body></html>"
                ],
                "fields": [
                    {"name": "title", "description": "Page title", "field_type": "string"},
                    {"name": "content", "description": "Main content", "field_type": "string"}
                ],
                "schema_mode": "predefined",
                "domain": "example.com",
                "iteration_rounds": 2
            }
        }


class ParserGenerateResponse(BaseModel):
    """
    解析器生成响应（立即返回）

    包含task_id和WebSocket URL用于跟踪进度
    """
    success: bool = Field(..., description="是否成功创建任务")
    task_id: str = Field(..., description="任务ID（UUID）")
    message: str = Field(..., description="提示信息")
    websocket_url: str = Field(..., description="WebSocket连接URL")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Parser generation task created successfully",
                "websocket_url": "ws://localhost:8000/api/parser/progress/550e8400-e29b-41d4-a716-446655440000"
            }
        }


class TaskStatus(BaseModel):
    """
    任务状态查询响应
    """
    task_id: str = Field(..., description="任务ID")
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = Field(
        ...,
        description="任务状态"
    )
    progress: int = Field(0, description="进度百分比（0-100）")
    phase: Optional[str] = Field(None, description="当前阶段")
    started_at: Optional[float] = Field(None, description="开始时间（Unix时间戳）")
    completed_at: Optional[float] = Field(None, description="完成时间（Unix时间戳）")
    result: Optional[Dict[str, Any]] = Field(None, description="结果数据（仅completed状态）")
    error: Optional[str] = Field(None, description="错误信息（仅failed状态）")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "running",
                "progress": 45,
                "phase": "code_generation",
                "started_at": 1704369600.0,
                "completed_at": None,
                "result": None,
                "error": None
            }
        }


class ProgressMessage(BaseModel):
    """
    WebSocket进度消息

    支持多种消息类型：
    - progress: 进度更新
    - log: 日志消息
    - result: 最终结果
    - error: 错误消息
    - complete: 完成通知
    """
    type: Literal["progress", "log", "result", "error", "complete"] = Field(
        ...,
        description="消息类型"
    )
    timestamp: float = Field(..., description="时间戳（Unix时间）")

    # progress类型字段
    phase: Optional[str] = Field(None, description="当前阶段（planning/schema_iteration/code_generation/batch_parsing/packaging）")
    step: Optional[str] = Field(None, description="当前步骤描述")
    percentage: Optional[int] = Field(None, description="进度百分比（0-100）")
    eta_seconds: Optional[int] = Field(None, description="预计剩余时间（秒）")

    # log类型字段
    log_level: Optional[Literal["info", "success", "warning", "error"]] = Field(None, description="日志级别")
    log_message: Optional[str] = Field(None, description="日志消息内容")

    # result/complete类型字段
    result: Optional[Dict[str, Any]] = Field(None, description="最终结果数据")

    # error类型字段
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "type": "progress",
                    "timestamp": 1704369600.0,
                    "phase": "schema_iteration",
                    "step": "Extracting schema from sample 2/3",
                    "percentage": 30,
                    "eta_seconds": 180
                },
                {
                    "type": "log",
                    "timestamp": 1704369601.0,
                    "log_level": "info",
                    "log_message": "Successfully extracted schema from HTML sample"
                },
                {
                    "type": "complete",
                    "timestamp": 1704369700.0,
                    "result": {
                        "parser_path": "/path/to/parser.py",
                        "schema_path": "/path/to/schema.json",
                        "results_dir": "/path/to/results/",
                        "parsed_files": [
                            {"filename": "file1.json", "size": 1024},
                            {"filename": "file2.json", "size": 2048}
                        ]
                    }
                }
            ]
        }


class CancelResponse(BaseModel):
    """
    取消任务响应
    """
    success: bool = Field(..., description="是否成功取消")
    message: str = Field(..., description="提示信息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Task cancelled successfully"
            }
        }
