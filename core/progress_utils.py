#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度管理工具模块

提供通用的进度更新功能，避免在各个模块中重复定义。
"""

from typing import Optional
from loguru import logger


def update_task_progress(
    task_id: Optional[str],
    step: Optional[str] = None,
    percentage: Optional[int] = None,
    log_message: Optional[str] = None,
    log_level: str = "info"
) -> None:
    """更新任务进度
    
    如果提供了有效的 task_id，则更新进度管理器中的任务状态。
    如果 task_id 为 None 或进度管理器不可用，则静默跳过。
    
    Args:
        task_id: 任务ID，如果为None则跳过更新
        step: 当前步骤描述
        percentage: 进度百分比 (0-100)
        log_message: 日志消息
        log_level: 日志级别 (info, warning, error等)
    
    Example:
        >>> update_task_progress(
        ...     task_id="task_123",
        ...     step="正在处理数据...",
        ...     percentage=50,
        ...     log_message="已处理50%"
        ... )
    """
    if not task_id:
        return
    
    try:
        from fastapi_services.progress_manager import get_progress_manager
        progress_manager = get_progress_manager()
        progress_manager.update_progress(
            task_id,
            step=step,
            percentage=percentage,
            log_message=log_message,
            log_level=log_level
        )
    except Exception as e:
        logger.warning(f"进度更新失败: {e}")


class ProgressTracker:
    """进度跟踪器基类
    
    为需要进度跟踪的类提供标准的进度更新接口。
    使用此类的子类需要有 `task_id` 属性。
    
    Example:
        >>> class MyService(ProgressTracker):
        ...     def __init__(self, task_id=None):
        ...         self.task_id = task_id
        ...     
        ...     def process(self):
        ...         self._update_progress(step="开始处理", percentage=10)
        ...         # 处理逻辑...
        ...         self._update_progress(step="完成", percentage=100)
    """
    
    task_id: Optional[str] = None
    
    def _update_progress(
        self,
        step: Optional[str] = None,
        percentage: Optional[int] = None,
        log_message: Optional[str] = None,
        log_level: str = "info"
    ) -> None:
        """更新进度（实例方法）
        
        Args:
            step: 当前步骤描述
            percentage: 进度百分比 (0-100)
            log_message: 日志消息
            log_level: 日志级别
        """
        update_task_progress(
            self.task_id,
            step=step,
            percentage=percentage,
            log_message=log_message,
            log_level=log_level
        )

