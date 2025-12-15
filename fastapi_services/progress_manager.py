#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度管理器 - 用于跟踪长时间运行任务的进度
使用单例模式，支持任务创建、更新、查询和自动清理
"""

import uuid
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from threading import Lock
from loguru import logger


class ProgressManager:
    """单例模式的进度管理器"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化进度管理器"""
        if self._initialized:
            return
            
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_lock = Lock()
        self.ttl_minutes = 30  # 任务存活时间：30分钟
        self.max_logs = 100  # 每个任务最多保留100条日志
        self._initialized = True
        logger.info("进度管理器初始化完成")
    
    def create_task(self, initial_step: str = "初始化中...") -> str:
        """创建新任务
        
        Args:
            initial_step: 初始步骤描述
            
        Returns:
            str: 任务ID (UUID)
        """
        task_id = str(uuid.uuid4())
        
        with self.task_lock:
            self.tasks[task_id] = {
                "task_id": task_id,
                "status": "running",
                "step": initial_step,
                "percentage": 0,
                "logs": [],
                "error": None,
                "result": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        
        logger.debug(f"创建任务: {task_id}")
        return task_id
    
    def update_progress(
        self,
        task_id: str,
        step: Optional[str] = None,
        percentage: Optional[int] = None,
        log_message: Optional[str] = None,
        log_level: str = "info"
    ) -> bool:
        """更新任务进度
        
        Args:
            task_id: 任务ID
            step: 当前步骤描述（可选）
            percentage: 进度百分比 0-100（可选）
            log_message: 日志消息（可选）
            log_level: 日志级别 (info/warning/error)
            
        Returns:
            bool: 更新是否成功
        """
        with self.task_lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False
            
            task = self.tasks[task_id]
            
            # 更新步骤
            if step is not None:
                task["step"] = step
            
            # 更新百分比（限制在0-100范围内）
            if percentage is not None:
                task["percentage"] = max(0, min(100, percentage))
            
            # 添加日志
            if log_message is not None:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "level": log_level,
                    "message": log_message
                }
                task["logs"].append(log_entry)
                
                # 限制日志数量
                if len(task["logs"]) > self.max_logs:
                    task["logs"] = task["logs"][-self.max_logs:]
            
            # 更新时间戳
            task["updated_at"] = datetime.now()
            
        return True
    
    def complete_task(self, task_id: str, message: str = "完成", result: Any = None) -> bool:
        """标记任务为完成
        
        Args:
            task_id: 任务ID
            message: 完成消息
            result: 任务结果数据（可选）
            
        Returns:
            bool: 更新是否成功
        """
        with self.task_lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False
            
            task = self.tasks[task_id]
            task["status"] = "completed"
            task["percentage"] = 100
            task["step"] = message
            if result is not None:
                task["result"] = result
            
            # 添加日志
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": "success",
                "message": message
            }
            task["logs"].append(log_entry)
            
            task["updated_at"] = datetime.now()
            
        logger.info(f"任务完成: {task_id}")
        return True
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """标记任务为失败
        
        Args:
            task_id: 任务ID
            error_message: 错误消息
            
        Returns:
            bool: 操作是否成功
        """
        with self.task_lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False
            
            task = self.tasks[task_id]
            task["status"] = "failed"
            task["error"] = error_message
            task["updated_at"] = datetime.now()
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": "error",
                "message": error_message
            }
            task["logs"].append(log_entry)
        
        logger.debug(f"任务失败: {task_id}")
        return True
    
    def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务进度
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict]: 任务进度数据，如果任务不存在则返回None
        """
        with self.task_lock:
            if task_id not in self.tasks:
                return None
            
            # 返回任务数据的副本（不包含内部时间戳）
            task = self.tasks[task_id].copy()
            task.pop("created_at", None)
            task.pop("updated_at", None)
            return task
    
    def cleanup_expired_tasks(self) -> int:
        """清理过期任务
        
        Returns:
            int: 清理的任务数量
        """
        now = datetime.now()
        expired_ids = []
        
        with self.task_lock:
            for task_id, task in self.tasks.items():
                # 检查是否过期（超过TTL时间）
                if now - task["updated_at"] > timedelta(minutes=self.ttl_minutes):
                    expired_ids.append(task_id)
            
            # 删除过期任务
            for task_id in expired_ids:
                del self.tasks[task_id]
        
        if expired_ids:
            logger.info(f"清理过期任务: {len(expired_ids)} 个")
        
        return len(expired_ids)
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 删除是否成功
        """
        with self.task_lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                logger.debug(f"删除任务: {task_id}")
                return True
            return False
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务（用于调试）
        
        Returns:
            List[Dict]: 所有任务列表
        """
        with self.task_lock:
            return [
                {
                    "task_id": task["task_id"],
                    "status": task["status"],
                    "step": task["step"],
                    "percentage": task["percentage"],
                    "result": task.get("result"),
                    "created_at": task["created_at"].isoformat(),
                    "updated_at": task["updated_at"].isoformat()
                }
                for task in self.tasks.values()
            ]


# 全局单例实例
_progress_manager = ProgressManager()


def get_progress_manager() -> ProgressManager:
    """获取进度管理器单例实例
    
    Returns:
        ProgressManager: 进度管理器实例
    """
    return _progress_manager

