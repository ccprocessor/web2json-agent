"""
完整解析器生成API路由

提供以下端点：
1. POST /generate - 创建解析器生成任务
2. WS /progress/{task_id} - WebSocket进度流
3. POST /cancel/{task_id} - 取消任务
4. GET /download/{task_id} - 下载结果（ZIP或parser.py）
5. GET /status/{task_id} - 查询任务状态
6. GET /results/{task_id} - 获取所有解析结果数据（JSON格式）
"""
from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import FileResponse, Response, JSONResponse
from typing import Literal
import logging
import json
from pathlib import Path

from web2json_api.models.parser import (
    ParserGenerateRequest,
    ParserGenerateResponse,
    TaskStatus,
    CancelResponse
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# 导入全局TaskManager实例
from web2json_api.services.task_manager import task_manager


@router.post("/generate", response_model=ParserGenerateResponse)
async def generate_parser(
    request: ParserGenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    创建完整解析器生成任务

    **工作流程：**
    1. 验证输入（至少一个HTML源，schema_mode=predefined时必须有fields）
    2. 创建任务并返回task_id
    3. 在后台启动解析器生成流程
    4. 返回WebSocket URL供前端连接并接收进度

    **Schema模式：**
    - `auto`: AI自动分析HTML并发现所有字段
    - `predefined`: 用户指定要提取的字段名

    **返回：**
    - task_id: 用于查询状态和下载结果
    - websocket_url: 连接此URL接收实时进度更新
    """
    # 验证输入
    if request.schema_mode == "predefined" and not request.fields:
        raise HTTPException(
            status_code=400,
            detail="Fields are required when schema_mode is 'predefined'"
        )

    # 检查至少有一个HTML源
    has_input = any([
        request.html_contents,
        request.urls,
        request.html_content,
        request.url
    ])
    if not has_input:
        raise HTTPException(
            status_code=400,
            detail="At least one HTML source is required (html_contents, urls, html_content, or url)"
        )

    # 创建任务
    task_id = task_manager.create_task(request)

    # 在后台启动任务
    background_tasks.add_task(task_manager.run_task, task_id)

    # 构建WebSocket URL
    websocket_url = f"ws://localhost:8000/api/parser/progress/{task_id}"

    logger.info(f"Task created and started: {task_id}")

    return ParserGenerateResponse(
        success=True,
        task_id=task_id,
        message="Parser generation task created successfully",
        websocket_url=websocket_url
    )


@router.websocket("/progress/{task_id}")
async def progress_stream(websocket: WebSocket, task_id: str):
    """
    WebSocket端点 - 实时进度流

    **消息类型：**
    - `progress`: 进度更新（百分比、阶段、ETA）
    - `log`: 日志消息（info/success/warning/error）
    - `result`: 最终结果数据
    - `error`: 错误消息
    - `complete`: 任务完成通知

    **连接流程：**
    1. 前端连接ws://host/api/parser/progress/{task_id}
    2. 后端验证task_id并接受连接
    3. 后端持续发送ProgressMessage
    4. 任务完成或出错时发送final message并关闭连接

    **重连支持：**
    - 支持多个客户端同时连接同一task_id
    - 断线重连后会收到缓冲的最近消息
    """
    logger.info(f"WebSocket connection request for task: {task_id}")

    # 验证任务存在
    task_status = task_manager.get_status(task_id)
    if not task_status:
        await websocket.close(code=1008, reason="Task not found")
        return

    # 接受连接
    await websocket.accept()
    logger.info(f"WebSocket connected for task: {task_id}")

    # 添加到连接列表
    await task_manager.add_websocket(task_id, websocket)

    try:
        # 保持连接直到客户端断开或任务完成
        while True:
            # 接收客户端消息（用于心跳或控制）
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task: {task_id}")
    finally:
        await task_manager.remove_websocket(task_id, websocket)


@router.post("/cancel/{task_id}", response_model=CancelResponse)
async def cancel_task(task_id: str):
    """
    取消正在运行的任务

    **行为：**
    - 设置任务的取消标志
    - 任务在下一个检查点处停止
    - 清理部分生成的文件
    - 通过WebSocket发送cancelled消息

    **注意：**
    - 只能取消pending或running状态的任务
    - 已完成/失败的任务无法取消
    """
    logger.info(f"POST /api/parser/cancel/{task_id}")

    success = task_manager.cancel_task(task_id)

    if not success:
        # 检查任务是否存在
        task_status = task_manager.get_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel task in '{task_status.status}' status"
            )

    return CancelResponse(
        success=True,
        message="Task cancellation initiated"
    )


@router.get("/download/{task_id}")
async def download_results(
    task_id: str,
    type: Literal["zip", "parser"] = Query("zip", description="下载类型：zip=所有结果，parser=仅parser.py")
):
    """
    下载生成的结果

    **下载类型：**
    - `zip`: 下载包含所有结果的ZIP文件
      - parser.py（解析器代码）
      - schema.json（字段定义）
      - results/（所有解析的JSON文件）
      - README.md（使用说明）

    - `parser`: 仅下载parser.py文件

    **返回：**
    - Content-Type: application/zip 或 text/x-python
    - Content-Disposition: attachment
    """
    logger.info(f"GET /api/parser/download/{task_id}?type={type}")

    # 验证任务存在且已完成
    task_status = task_manager.get_status(task_id)
    if not task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_status.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot download results for task in '{task_status.status}' status. Wait for completion."
        )

    task = task_manager.tasks.get(task_id)
    if not task or not task.output_dir:
        raise HTTPException(status_code=404, detail="Task output not found")

    output_dir = task.output_dir

    # 根据类型返回不同文件
    if type == "parser":
        # 返回parser.py文件
        from web2json_api.services.zip_packager import ZipPackager
        parser_file = ZipPackager.get_parser_file(output_dir)

        if not parser_file or not parser_file.exists():
            raise HTTPException(status_code=404, detail="Parser file not found")

        return FileResponse(
            path=str(parser_file),
            filename="parser.py",
            media_type="text/x-python",
            headers={"Content-Disposition": "attachment; filename=parser.py"}
        )

    elif type == "zip":
        # 返回ZIP文件
        from web2json_api.services.zip_packager import ZipPackager

        zip_file = output_dir / "parser_results.zip"

        # 如果ZIP不存在，先创建
        if not zip_file.exists():
            logger.info(f"ZIP file not found, creating it now for task {task_id}")
            zip_file = ZipPackager.create_zip(output_dir)

        if not zip_file or not zip_file.exists():
            raise HTTPException(status_code=404, detail="ZIP file not found")

        return FileResponse(
            path=str(zip_file),
            filename=f"parser_results_{task_id[:8]}.zip",
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=parser_results_{task_id[:8]}.zip"}
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid download type")


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    查询任务状态

    **状态类型：**
    - `pending`: 任务已创建，等待执行
    - `running`: 任务正在执行
    - `completed`: 任务成功完成
    - `failed`: 任务执行失败
    - `cancelled`: 任务被用户取消

    **返回字段：**
    - progress: 0-100的百分比
    - phase: 当前执行阶段
    - result: 仅completed状态时包含
    - error: 仅failed状态时包含
    """
    logger.info(f"GET /api/parser/status/{task_id}")

    task_status = task_manager.get_status(task_id)

    if not task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    return task_status


@router.get("/results/{task_id}")
async def get_task_results(task_id: str):
    """
    获取所有解析结果数据（JSON格式）

    **功能：**
    - 读取result/目录下的所有JSON文件
    - 返回所有解析结果的数组

    **返回：**
    - List[Dict]: 所有解析结果的JSON数组

    **注意：**
    - 只有completed状态的任务才能获取结果
    - 如果文件太多，可能需要较长时间加载
    """
    logger.info(f"GET /api/parser/results/{task_id}")

    # 验证任务存在且已完成
    task_status = task_manager.get_status(task_id)
    if not task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_status.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot get results for task in '{task_status.status}' status. Wait for completion."
        )

    task = task_manager.tasks.get(task_id)
    if not task or not task.output_dir:
        raise HTTPException(status_code=404, detail="Task output not found")

    output_dir = task.output_dir
    result_dir = output_dir / "result"

    if not result_dir.exists():
        raise HTTPException(status_code=404, detail="Result directory not found")

    # 读取所有JSON文件
    all_results = []
    json_files = sorted(result_dir.glob("*.json"))

    logger.info(f"Loading {len(json_files)} result files from {result_dir}")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_results.append(data)
        except Exception as e:
            logger.error(f"Failed to load {json_file}: {e}")
            # 跳过无法加载的文件
            continue

    logger.info(f"Successfully loaded {len(all_results)} results")

    return JSONResponse(content={
        "success": True,
        "count": len(all_results),
        "results": all_results
    })
