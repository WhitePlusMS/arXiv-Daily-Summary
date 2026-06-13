"""Loguru 日志配置工具。

集中管理不同入口的日志初始化，避免 FastAPI 与 CLI 各自维护一套重复配置。
"""

import logging
import os
import sys
from pathlib import Path
from typing import Iterable

from loguru import logger


def cleanup_old_logs_by_size(files: Iterable[str], max_size_mb: int = 500):
    """清理旧日志文件，确保总大小不超过指定值。"""
    file_paths = [Path(f) for f in files if Path(f).exists()]
    if not file_paths:
        return

    max_size_bytes = max_size_mb * 1024 * 1024
    file_paths.sort(key=lambda f: f.stat().st_mtime)
    total_size = sum(f.stat().st_size for f in file_paths)

    while total_size > max_size_bytes and len(file_paths) > 1:
        oldest_file = file_paths.pop(0)
        file_size = oldest_file.stat().st_size
        try:
            oldest_file.unlink()
            total_size -= file_size
        except Exception:
            pass


def cleanup_fastapi_logs(logs_dir: Path, max_size_mb: int = 500):
    """启动时清理 FastAPI 轮转日志。"""
    log_files = list(logs_dir.glob("fastapi.log*"))
    if log_files:
        cleanup_old_logs_by_size([str(f) for f in log_files], max_size_mb)


def _add_console_sink(level: str, milliseconds: bool):
    time_format = "YYYY-MM-DD HH:mm:ss.SSS" if milliseconds else "YYYY-MM-DD HH:mm:ss"
    logger.add(
        sys.stdout,
        format=f"<green>{{time:{time_format}}}</green> | <level>{{level: <8}}</level> | <cyan>{{name}}</cyan>:<cyan>{{function}}</cyan>:<cyan>{{line}}</cyan> - <level>{{message}}</level>",
        level=level,
    )


def _intercept_uvicorn_logs():
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level_map = {
                    logging.DEBUG: "DEBUG",
                    logging.INFO: "INFO",
                    logging.WARNING: "WARNING",
                    logging.ERROR: "ERROR",
                    logging.CRITICAL: "CRITICAL",
                }
                level = level_map.get(record.levelno, "INFO")

            logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

    logging.getLogger("uvicorn").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]


def setup_fastapi_logging(project_root: Path, configured: bool = False) -> bool:
    """配置 FastAPI 日志，返回最新 configured 状态。"""
    if configured:
        return True

    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "fastapi.log"

    logger.remove()
    _add_console_sink("DEBUG", milliseconds=True)

    def retention_function(files):
        cleanup_old_logs_by_size(files, max_size_mb=500)

    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention=retention_function,
        encoding="utf-8",
        enqueue=True,
    )

    cleanup_fastapi_logs(logs_dir, max_size_mb=500)
    _intercept_uvicorn_logs()
    return True


def setup_cli_logging(
    log_to_console: bool,
    log_file: str = "logs/arxiv_recommender.log",
    log_level: str = "DEBUG",
    log_max_size_mb: int = 10,
    log_backup_count: int = 5,
):
    """配置 CLI 日志。"""
    logger.remove()

    if log_to_console:
        _add_console_sink(log_level, milliseconds=False)

    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation=log_max_size_mb * 1024 * 1024,
            retention=log_backup_count,
            encoding="utf-8",
        )
