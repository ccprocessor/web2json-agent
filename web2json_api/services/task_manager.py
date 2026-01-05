"""
任务管理器 - 管理异步解析器生成任务

职责：
1. 任务生命周期管理（创建、运行、取消、清理）
2. WebSocket连接管理
3. 进度消息广播
4. 任务状态查询
"""
import uuid
import asyncio
import time
import shutil
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
from fastapi import WebSocket
import logging

from web2json_api.models.parser import (
    ParserGenerateRequest,
    TaskStatus as TaskStatusModel,
    ProgressMessage
)

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    request: ParserGenerateRequest
    status: str = "pending"  # pending, running, completed, failed, cancelled
    progress: int = 0
    phase: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    cancel_flag: bool = False
    output_dir: Optional[Path] = None
    message_buffer: List[ProgressMessage] = field(default_factory=list)


class TaskManager:
    """
    任务管理器

    Features:
    - 内存存储任务状态（生产环境可替换为Redis）
    - WebSocket连接管理
    - 消息缓冲（最近50条，用于重连）
    - 自动清理过期任务
    """

    def __init__(self, max_concurrent_tasks: int = 10, buffer_size: int = 50):
        """
        初始化任务管理器

        Args:
            max_concurrent_tasks: 最大并发任务数
            buffer_size: 每个任务的消息缓冲大小
        """
        self.tasks: Dict[str, Task] = {}
        self.websocket_connections: Dict[str, List[WebSocket]] = {}
        self.max_concurrent_tasks = max_concurrent_tasks
        self.buffer_size = buffer_size
        self._lock = asyncio.Lock()

        logger.info(f"TaskManager initialized (max_concurrent={max_concurrent_tasks}, buffer_size={buffer_size})")

    def create_task(self, request: ParserGenerateRequest) -> str:
        """
        创建新任务

        Args:
            request: 解析器生成请求

        Returns:
            task_id: 任务唯一标识符（UUID）
        """
        task_id = str(uuid.uuid4())
        output_dir = Path(f"output/temp_{task_id}")

        task = Task(
            task_id=task_id,
            request=request,
            output_dir=output_dir
        )

        self.tasks[task_id] = task
        self.websocket_connections[task_id] = []

        logger.info(f"Task created: {task_id} (schema_mode={request.schema_mode}, domain={request.domain})")
        return task_id

    async def run_task(self, task_id: str):
        """
        在后台执行任务

        Args:
            task_id: 任务ID
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return

        try:
            task.status = "running"
            task.started_at = time.time()
            task.progress = 0

            logger.info(f"Task started: {task_id}")

            # 发送开始日志
            await self.broadcast_log(task_id, "info", "Parser generation task started")

            # 调用ParserService执行实际生成
            from web2json_api.services.parser_service import ParserService
            parser_service = ParserService(self)
            result = await parser_service.generate_parser_with_progress(task_id, task.request)

            task.result = result
            task.status = "completed"
            task.completed_at = time.time()
            task.progress = 100

            logger.info(f"Task completed: {task_id}")

            # 发送完成消息
            await self.broadcast_complete(task_id, task.result)

        except asyncio.CancelledError:
            logger.info(f"Task cancelled: {task_id}")
            task.status = "cancelled"
            task.completed_at = time.time()
            await self.broadcast_log(task_id, "warning", "Task was cancelled by user")

        except Exception as e:
            logger.error(f"Task failed: {task_id} - {str(e)}", exc_info=True)
            task.status = "failed"
            task.error = str(e)
            task.completed_at = time.time()
            await self.broadcast_error(task_id, str(e))

    async def _simulate_task_execution(self, task_id: str):
        """模拟任务执行（用于测试）"""
        task = self.tasks[task_id]

        # 模拟多个阶段
        phases = [
            ("planning", "Planning parser generation", 5),
            ("schema_iteration", "Extracting and merging schemas", 40),
            ("code_generation", "Generating parser code", 40),
            ("batch_parsing", "Parsing all HTML files", 10),
            ("packaging", "Packaging results", 5)
        ]

        for phase_name, phase_desc, duration in phases:
            if task.cancel_flag:
                raise asyncio.CancelledError()

            task.phase = phase_name
            await self.broadcast_progress(
                task_id,
                phase=phase_name,
                step=phase_desc,
                percentage=task.progress,
                eta_seconds=int((100 - task.progress) * 0.6)  # 估算ETA
            )

            # 模拟该阶段的工作
            steps = 3
            for i in range(steps):
                if task.cancel_flag:
                    raise asyncio.CancelledError()

                await asyncio.sleep(duration / steps / 10)  # 加快模拟速度
                task.progress += duration // steps

                await self.broadcast_progress(
                    task_id,
                    phase=phase_name,
                    step=f"{phase_desc} ({i+1}/{steps})",
                    percentage=task.progress,
                    eta_seconds=int((100 - task.progress) * 0.6)
                )

                await self.broadcast_log(task_id, "info", f"Completed step {i+1}/{steps} in {phase_name}")

        # 模拟结果
        task.result = {
            "parser_path": str(task.output_dir / "parsers" / "final_parser.py"),
            "schema_path": str(task.output_dir / "parsers" / "schema.json"),
            "results_dir": str(task.output_dir / "result"),
            "parsed_files": [
                {"filename": "file1.json", "size": 1024},
                {"filename": "file2.json", "size": 2048},
                {"filename": "file3.json", "size": 1536}
            ]
        }

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功设置取消标志
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Cannot cancel task {task_id}: not found")
            return False

        if task.status in ["completed", "failed", "cancelled"]:
            logger.warning(f"Cannot cancel task {task_id}: already {task.status}")
            return False

        task.cancel_flag = True
        logger.info(f"Cancel flag set for task: {task_id}")
        return True

    def get_status(self, task_id: str) -> Optional[TaskStatusModel]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            TaskStatusModel or None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        return TaskStatusModel(
            task_id=task.task_id,
            status=task.status,
            progress=task.progress,
            phase=task.phase,
            started_at=task.started_at,
            completed_at=task.completed_at,
            result=task.result,
            error=task.error
        )

    async def add_websocket(self, task_id: str, websocket: WebSocket):
        """
        添加WebSocket连接

        Args:
            task_id: 任务ID
            websocket: WebSocket连接
        """
        async with self._lock:
            if task_id not in self.websocket_connections:
                self.websocket_connections[task_id] = []

            self.websocket_connections[task_id].append(websocket)
            logger.info(f"WebSocket added for task {task_id} (total: {len(self.websocket_connections[task_id])})")

            # 发送缓冲的消息
            task = self.tasks.get(task_id)
            if task and task.message_buffer:
                logger.info(f"Sending {len(task.message_buffer)} buffered messages to new connection")
                for message in task.message_buffer:
                    try:
                        await websocket.send_json(message.dict())
                    except Exception as e:
                        logger.error(f"Failed to send buffered message: {e}")

    async def remove_websocket(self, task_id: str, websocket: WebSocket):
        """
        移除WebSocket连接

        Args:
            task_id: 任务ID
            websocket: WebSocket连接
        """
        async with self._lock:
            if task_id in self.websocket_connections:
                try:
                    self.websocket_connections[task_id].remove(websocket)
                    logger.info(f"WebSocket removed for task {task_id} (remaining: {len(self.websocket_connections[task_id])})")
                except ValueError:
                    pass

    async def broadcast_progress(
        self,
        task_id: str,
        phase: str,
        step: str,
        percentage: int,
        eta_seconds: int
    ):
        """
        广播进度更新

        Args:
            task_id: 任务ID
            phase: 当前阶段
            step: 当前步骤描述
            percentage: 进度百分比（0-100）
            eta_seconds: 预计剩余时间（秒）
        """
        message = ProgressMessage(
            type="progress",
            timestamp=time.time(),
            phase=phase,
            step=step,
            percentage=percentage,
            eta_seconds=eta_seconds
        )

        await self._broadcast_message(task_id, message)

    async def broadcast_log(
        self,
        task_id: str,
        log_level: str,
        log_message: str
    ):
        """
        广播日志消息

        Args:
            task_id: 任务ID
            log_level: 日志级别（info/success/warning/error）
            log_message: 日志内容
        """
        message = ProgressMessage(
            type="log",
            timestamp=time.time(),
            log_level=log_level,
            log_message=log_message
        )

        await self._broadcast_message(task_id, message)

    async def broadcast_complete(self, task_id: str, result: Dict):
        """
        广播完成消息

        Args:
            task_id: 任务ID
            result: 结果数据
        """
        message = ProgressMessage(
            type="complete",
            timestamp=time.time(),
            result=result
        )

        await self._broadcast_message(task_id, message)

    async def broadcast_error(self, task_id: str, error: str):
        """
        广播错误消息

        Args:
            task_id: 任务ID
            error: 错误信息
        """
        message = ProgressMessage(
            type="error",
            timestamp=time.time(),
            error=error
        )

        await self._broadcast_message(task_id, message)

    async def _broadcast_message(self, task_id: str, message: ProgressMessage):
        """
        内部方法：广播消息到所有连接的WebSocket

        Args:
            task_id: 任务ID
            message: 进度消息
        """
        # 添加到缓冲区
        task = self.tasks.get(task_id)
        if task:
            task.message_buffer.append(message)
            # 限制缓冲区大小
            if len(task.message_buffer) > self.buffer_size:
                task.message_buffer = task.message_buffer[-self.buffer_size:]

        # 广播到所有连接
        connections = self.websocket_connections.get(task_id, [])
        if not connections:
            return

        message_dict = message.dict()
        disconnected = []

        for ws in connections:
            try:
                await ws.send_json(message_dict)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.append(ws)

        # 移除断开的连接
        for ws in disconnected:
            await self.remove_websocket(task_id, ws)

    async def cleanup_task(self, task_id: str, delay_hours: int = 24):
        """
        延迟清理任务文件

        Args:
            task_id: 任务ID
            delay_hours: 延迟清理时间（小时）
        """
        await asyncio.sleep(delay_hours * 3600)

        task = self.tasks.get(task_id)
        if task and task.output_dir and task.output_dir.exists():
            try:
                shutil.rmtree(task.output_dir)
                logger.info(f"Cleaned up task files: {task_id}")
            except Exception as e:
                logger.error(f"Failed to clean up task {task_id}: {e}")

        # 从内存中移除任务
        if task_id in self.tasks:
            del self.tasks[task_id]
        if task_id in self.websocket_connections:
            del self.websocket_connections[task_id]


# 全局任务管理器实例
task_manager = TaskManager()
