"""
解析器服务 - 包装ParserAgent并添加进度追踪

职责：
1. 调用ParserAgent.generate_parser()执行真实的解析器生成
2. 在关键点注入进度回调
3. 发送实时日志和进度更新
"""
import time
import asyncio
from pathlib import Path
from typing import Dict, Optional, List
import logging

from web2json.agent.orchestrator import ParserAgent
from web2json_api.models.parser import ParserGenerateRequest

logger = logging.getLogger(__name__)


class ParserService:
    """
    解析器服务

    将ParserAgent的执行过程包装为异步任务，并注入进度回调
    """

    def __init__(self, task_manager):
        """
        初始化解析器服务

        Args:
            task_manager: TaskManager实例，用于发送进度更新
        """
        self.task_manager = task_manager

    async def generate_parser_with_progress(
        self,
        task_id: str,
        request: ParserGenerateRequest
    ) -> Dict:
        """
        执行解析器生成并发送进度

        Args:
            task_id: 任务ID
            request: 解析器生成请求

        Returns:
            Dict: 生成结果
        """
        task = self.task_manager.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        start_time = time.time()
        progress_task = None

        try:
            # 准备输出目录
            output_dir = task.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)

            # 收集HTML文件
            html_files = await self._prepare_html_files(task_id, request, output_dir)

            if not html_files:
                raise ValueError("No HTML files to process")

            # 阶段1: 规划 (5%)
            await self._update_progress(task_id, "planning", "Creating execution plan", 5, 0)
            await asyncio.sleep(0.5)

            # 创建ParserAgent
            agent = ParserAgent(
                output_dir=str(output_dir),
                schema_mode=request.schema_mode,
                schema_template=self._build_schema_template(request) if request.schema_mode == "predefined" else None
            )

            # 阶段2-4: 执行解析器生成
            await self._update_progress(task_id, "schema_iteration", "Starting parser generation", 10, 0)

            # 获取当前事件循环（在主异步线程中）
            loop = asyncio.get_running_loop()

            # 在同步线程中执行ParserAgent（因为它是同步的）
            result = await asyncio.to_thread(
                self._run_parser_agent,
                agent,
                html_files,
                request,
                task_id,
                loop  # 传递事件循环给子线程
            )

            # 阶段5: 完成 (100%)
            elapsed = time.time() - start_time
            await self._update_progress(task_id, "completed", "Parser generation completed", 100, 0)
            await self.task_manager.broadcast_log(
                task_id,
                "success",
                f"Parser generation completed in {elapsed:.1f} seconds"
            )

            return result

        except Exception as e:
            logger.error(f"Parser generation failed for task {task_id}: {e}", exc_info=True)

            # 确保错误消息能传递到前端
            error_message = str(e)

            # 特殊处理API额度不足的错误
            if "insufficient_user_quota" in error_message or "用户额度不足" in error_message:
                error_message = "API额度不足，请充值后重试。剩余额度已用尽。"
                await self.task_manager.broadcast_log(task_id, "error", error_message)
            elif "403" in error_message or "PermissionDenied" in error_message:
                error_message = f"API访问被拒绝: {error_message}"
                await self.task_manager.broadcast_log(task_id, "error", error_message)
            else:
                await self.task_manager.broadcast_log(task_id, "error", f"执行失败: {error_message}")

            # 设置任务状态为失败
            task.status = "failed"
            task.error = error_message

            raise

    def _run_parser_agent(
        self,
        agent: ParserAgent,
        html_files: List[str],
        request: ParserGenerateRequest,
        task_id: str,
        loop  # 从主线程传入的事件循环
    ) -> Dict:
        """
        在同步线程中运行ParserAgent

        Args:
            agent: ParserAgent实例
            html_files: HTML文件路径列表
            request: 请求参数
            task_id: 任务ID

        Returns:
            Dict: 生成结果
        """
        try:
            logger.info(f"开始执行ParserAgent，处理 {len(html_files)} 个HTML文件")

            # 定义进度回调函数（同步调用）
            def progress_callback(phase: str, step: str, percentage: int):
                """进度回调 - 在同步线程中调用"""
                try:
                    # 使用传入的事件循环（从主线程获取）
                    future = asyncio.run_coroutine_threadsafe(
                        self.task_manager.broadcast_progress(
                            task_id,
                            phase=phase,
                            step=step,
                            percentage=percentage,
                            eta_seconds=0
                        ),
                        loop
                    )
                    # 等待完成（带超时）
                    future.result(timeout=1.0)
                except Exception as e:
                    logger.warning(f"进度回调失败: {e}")

            # 更新 agent 的回调函数
            agent.progress_callback = progress_callback
            agent.executor.progress_callback = progress_callback

            # 调用ParserAgent的generate_parser方法
            result = agent.generate_parser(
                html_files=html_files,
                domain=request.domain or "web_parser",
                iteration_rounds=request.iteration_rounds or 3,
                schema_mode=request.schema_mode,
                schema_template=self._build_schema_template(request) if request.schema_mode == "predefined" else None
            )

            # 检查执行结果
            if not result.get("success", False):
                error_msg = result.get("error", "ParserAgent执行失败，未返回成功状态")
                logger.error(f"ParserAgent返回失败: {error_msg}")
                raise RuntimeError(error_msg)

            # 将结果转换为前端需要的格式
            return {
                "success": True,
                "parser_path": result.get("parser_path", ""),
                "schema_path": result.get("config_path", ""),
                "results_dir": result.get("results_dir", ""),
                "parsed_files": self._get_parsed_files_info(result.get("results_dir", ""))
            }

        except Exception as e:
            logger.error(f"ParserAgent execution failed: {e}", exc_info=True)

            # 提取更友好的错误信息
            error_str = str(e)
            if "insufficient_user_quota" in error_str or "用户额度不足" in error_str:
                raise RuntimeError("API额度不足，请充值后重试") from e
            elif "PermissionDenied" in error_str or "403" in error_str:
                raise RuntimeError("API访问权限被拒绝，请检查API密钥") from e
            elif "执行失败" in error_str:
                # 已经是友好的错误消息，直接抛出
                raise
            else:
                # 其他错误，包装一下
                raise RuntimeError(f"解析器生成失败: {error_str}") from e

    async def _prepare_html_files(
        self,
        task_id: str,
        request: ParserGenerateRequest,
        output_dir: Path
    ) -> List[str]:
        """
        准备HTML文件

        将用户提供的HTML内容转换为文件路径

        Args:
            task_id: 任务ID
            request: 请求参数
            output_dir: 输出目录

        Returns:
            List[str]: HTML文件路径列表
        """
        html_files = []
        html_dir = output_dir / "html_original"
        html_dir.mkdir(parents=True, exist_ok=True)

        # 收集所有HTML内容
        html_contents = []

        if request.html_contents:
            html_contents.extend(request.html_contents)
        if request.html_content:
            html_contents.append(request.html_content)

        # 保存HTML内容到文件
        for i, html_content in enumerate(html_contents):
            file_path = html_dir / f"sample_{i:04d}.html"
            file_path.write_text(html_content, encoding='utf-8')
            html_files.append(str(file_path))
            await self.task_manager.broadcast_log(
                task_id,
                "info",
                f"Saved HTML sample {i+1}/{len(html_contents)}"
            )

        return html_files

    def _build_schema_template(self, request: ParserGenerateRequest) -> Optional[Dict]:
        """
        构建schema模板（predefined模式）

        Args:
            request: 请求参数

        Returns:
            Dict: schema模板
        """
        if not request.fields:
            return None

        schema = {}
        for field in request.fields:
            schema[field.name] = {
                "type": field.field_type,
                "description": field.description or "",
            }

        return schema

    def _get_parsed_files_info(self, results_dir: str) -> List[Dict]:
        """
        获取解析结果文件信息

        Args:
            results_dir: 结果目录路径

        Returns:
            List[Dict]: 文件信息列表
        """
        if not results_dir:
            return []

        results_path = Path(results_dir)
        if not results_path.exists():
            return []

        files_info = []
        for json_file in sorted(results_path.glob("*.json")):
            files_info.append({
                "filename": json_file.name,
                "size": json_file.stat().st_size,
                "path": str(json_file)
            })

        return files_info

    async def _update_progress(
        self,
        task_id: str,
        phase: str,
        step: str,
        percentage: int,
        eta_seconds: int
    ):
        """
        更新任务进度

        Args:
            task_id: 任务ID
            phase: 阶段名称
            step: 步骤描述
            percentage: 进度百分比
            eta_seconds: 预计剩余时间
        """
        task = self.task_manager.tasks.get(task_id)
        if task:
            task.progress = percentage
            task.phase = phase

        await self.task_manager.broadcast_progress(
            task_id,
            phase=phase,
            step=step,
            percentage=percentage,
            eta_seconds=eta_seconds
        )
