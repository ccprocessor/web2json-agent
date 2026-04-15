"""
LLM 调用重试：网关故障、超时、限流等瞬时错误时使用指数退避重试。
"""
from __future__ import annotations

import random
import time
from typing import Any, Callable, TypeVar

from loguru import logger

from web2json.config.settings import settings

T = TypeVar("T")

# 与 LLMClient 类似：进程内累计，便于 pipeline 汇总
_retry_events: int = 0


def reset_retry_stats() -> None:
    """新一批 pipeline 运行前清零。"""
    global _retry_events
    _retry_events = 0


def get_retry_stats() -> dict[str, int]:
    """本次进程内 LLM 可重试失败后实际执行重试的次数（每次退避前计 1）。"""
    return {"llm_retry_events": _retry_events}


def is_retryable_api_error(exc: BaseException) -> bool:
    """是否为可重试的瞬时 API 故障（非业务/鉴权错误）。"""
    try:
        from openai import (
            APIConnectionError,
            APITimeoutError,
            InternalServerError,
            RateLimitError,
        )
        from openai import APIStatusError

        if isinstance(exc, (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)):
            return True
        if isinstance(exc, APIStatusError):
            resp = getattr(exc, "response", None)
            code = getattr(resp, "status_code", None) if resp is not None else None
            if code is not None and code in (408, 429, 500, 502, 503, 504):
                return True
    except ImportError:
        pass

    try:
        import httpx

        if isinstance(
            exc,
            (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.ConnectTimeout,
                httpx.PoolTimeout,
            ),
        ):
            return True
        if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
            if exc.response.status_code in (408, 429, 500, 502, 503, 504):
                return True
    except ImportError:
        pass

    # 兜底：部分异常被 LangChain 包装或仅有字符串信息
    msg = str(exc).lower()
    hints = (
        "502",
        "503",
        "504",
        "timeout",
        "timed out",
        "connection",
        "temporarily unavailable",
        "bad gateway",
        "gateway timeout",
        "rate limit",
        "overloaded",
    )
    if any(h in msg for h in hints):
        return True

    return False


def invoke_with_retry(
    operation_label: str,
    invoke_fn: Callable[[], T],
) -> T:
    """
    执行无参调用（通常为 model.invoke），在可重试错误时退避重试。

    Args:
        operation_label: 日志用简短说明
        invoke_fn: 实际调用，如 lambda: model.invoke(messages)

    Returns:
        invoke_fn 的返回值
    """
    global _retry_events
    max_attempts = max(1, settings.llm_api_retry_max_attempts)

    for attempt in range(1, max_attempts + 1):
        try:
            return invoke_fn()
        except Exception as e:
            if attempt >= max_attempts or not is_retryable_api_error(e):
                raise
            delay = min(
                settings.llm_api_retry_max_seconds,
                settings.llm_api_retry_base_seconds * (2 ** (attempt - 1)),
            )
            jitter = random.uniform(0, max(delay * 0.1, 0.05))
            sleep_s = min(delay + jitter, settings.llm_api_retry_max_seconds)
            _retry_events += 1
            logger.warning(
                f"[{operation_label}] LLM 调用失败 ({attempt}/{max_attempts}): {e!s} — "
                f"{sleep_s:.1f}s 后重试 (累计重试 #{_retry_events})"
            )
            time.sleep(sleep_s)


def chat_openai_invoke_kwargs() -> dict[str, Any]:
    """构造 ChatOpenAI 的公共参数：关闭 SDK 内置重试，由 invoke_with_retry 统一退避。"""
    out: dict[str, Any] = {"max_retries": 0}
    if settings.llm_request_timeout is not None:
        out["timeout"] = settings.llm_request_timeout
    return out
