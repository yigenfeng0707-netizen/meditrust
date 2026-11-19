"""结构化日志（P3 运维闭环）：JSON 格式 + 请求 ID 上下文，零新依赖。

解决的问题：此前仅 uvicorn 默认文本日志——无请求 ID、无 JSON、无文件轮转，
生产排障只能靠时间戳猜。现在：
- 生产（LOG_FORMAT=json，默认）：每条日志一行 JSON，字段
  ts/level/logger/msg/request_id + 业务 extra 字段，直接对接 ELK/Loki；
- 开发（LOG_FORMAT=text）：保持可读彩色文本；
- 请求 ID：http 中间件为每个请求生成/透传 X-Request-ID（contextvars，
  多 worker/异步安全），响应头回写，所有日志与错误响应自动携带；
- 日志文件：LOG_FILE 配置时按大小轮转（10MB × 5），配合 docker json-file
  双层防护（容器层由 compose 配置，此为裸机/Dockerfile 未挂载场景）。

用法：main.py 启动时调用 setup_logging()，业务代码无需改动
（全站已统一 logging.getLogger(__name__)）。
"""

import logging
import logging.handlers
import os
import sys
import time
import uuid
from contextvars import ContextVar

from app.config import settings

# 请求 ID 上下文（异步安全）：中间件 set，formatter/formatter 业务代码 get
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

_LOG_FORMATS = ("json", "text")


class JsonFormatter(logging.Formatter):
    """单行 JSON 日志：标准字段 + record.__dict 中的扩展字段。"""

    _RESERVED = frozenset({
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime", "taskName",
    })

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
                  + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                try:
                    log[key] = value if isinstance(
                        value, (str, int, float, bool, type(None))) else str(value)
                except Exception:  # noqa: BLE001 —— 日志序列化失败不能拖垮业务
                    log[key] = "<unserializable>"
        if record.exc_info:
            log["exc"] = self.formatException(record.exc_info)
        return _json_dumps(log)


def _json_dumps(obj: dict) -> str:
    """极简 JSON 序列化（标准库，不引入 orjson 依赖）。"""


class TextFormatter(logging.Formatter):
    """文本模式：把请求 ID 注入 record（供 %(request_id)s 引用）。"""

    def format(self, record: logging.LogRecord) -> str:
        record.request_id = request_id_ctx.get()
        return super().format(record)


def _json_dumps(obj: dict) -> str:
    """极简 JSON 序列化（标准库，不引入 orjson 依赖）。"""
    parts = []
    for key, value in obj.items():
        if value is None:
            rendered = "null"
        elif isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, (int, float)):
            rendered = str(value)
        else:
            escaped = (
                str(value)
                .replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t")
            )
            rendered = f'"{escaped}"'
        parts.append(f'"{key}":{rendered}')
    return "{" + ",".join(parts) + "}"


def get_request_id() -> str:
    """业务代码获取当前请求 ID（写日志/错误响应）。"""
    return request_id_ctx.get()


def set_request_id(value: str | None = None) -> str:
    """中间件设置请求 ID（未提供时生成）；返回生效后的值。"""
    rid = value or uuid.uuid4().hex[:16]
    request_id_ctx.set(rid)
    return rid


def setup_logging() -> None:
    """应用启动时调用：按 LOG_FORMAT/LOG_LEVEL/LOG_FILE 配置根日志。"""
    fmt = (os.getenv("LOG_FORMAT") or "json").lower()
    if fmt not in _LOG_FORMATS:
        fmt = "json"
    level_name = (os.getenv("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    log_file = os.getenv("LOG_FILE")
    if log_file:
        # 10MB × 5 轮转（裸机/未挂载容器卷场景；容器层由 compose json-file 兜底）
        handlers.append(
            logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
            )
        )

    formatter: logging.Formatter
    if fmt == "json":
        formatter = JsonFormatter()
    else:
        formatter = TextFormatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | rid=%(request_id)s | %(message)s"
        )

    root = logging.getLogger()
    root.setLevel(level)
    # 清理既有 handler（uvicorn 可能已注入），避免重复输出
    for h in list(root.handlers):
        root.removeHandler(h)
    for h in handlers:
        h.setFormatter(formatter)
        h.setLevel(level)
        root.addHandler(h)

    # uvicorn/access 日志并入根配置
    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(noisy)
        lg.handlers = []
        lg.propagate = True

    logging.getLogger(__name__).info(
        "日志初始化", extra={"log_format": fmt, "log_level": level_name,
                              "demo_mode": settings.DEMO_MODE,
                              "log_file": log_file or "-"}
    )
