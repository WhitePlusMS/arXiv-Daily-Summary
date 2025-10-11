#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础服务类 - 提供通用的服务响应模型和日志功能
"""

from loguru import logger
from typing import Any, Dict, Optional
from pydantic import BaseModel
from datetime import datetime


class ServiceResponse(BaseModel):
    """标准服务响应模型"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.now()


class BaseService:
    """基础服务类"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        # 统一使用 Loguru，不在此处添加独立的处理器
        self.logger = logger
    
    def log_info(self, message: str, **kwargs):
        """记录信息日志"""
        extra_info = f" - {kwargs}" if kwargs else ""
        self.logger.info(f"[{self.service_name}] {message}{extra_info}")
    
    def log_error(self, message: str, error: Exception = None):
        """记录错误日志"""
        if error:
            self.logger.error(f"[{self.service_name}] {message}: {str(error)}")
        else:
            self.logger.error(f"[{self.service_name}] {message}")
    
    def success_response(self, data: Any = None, message: str = None) -> ServiceResponse:
        """创建成功响应"""
        return ServiceResponse(success=True, data=data, message=message)
    
    def error_response(self, error: str, data: Any = None) -> ServiceResponse:
        """创建错误响应"""
        return ServiceResponse(success=False, error=error, data=data)