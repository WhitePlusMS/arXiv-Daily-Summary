#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务容器 - 依赖注入容器，管理所有服务实例
"""

from functools import lru_cache
from .arxiv_service import ArxivRecommenderService


class ServiceContainer:
    """服务容器 - 管理所有服务的单例实例"""
    
    _instance = None
    _services = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceContainer, cls).__new__(cls)
        return cls._instance
    
    @lru_cache(maxsize=1)
    def get_arxiv_service(self) -> ArxivRecommenderService:
        """获取ArXiv推荐服务实例"""
        if 'arxiv_service' not in self._services:
            self._services['arxiv_service'] = ArxivRecommenderService()
        return self._services['arxiv_service']


# 全局服务容器实例
service_container = ServiceContainer()


# FastAPI依赖注入函数
def get_arxiv_service() -> ArxivRecommenderService:
    """FastAPI依赖注入：获取ArXiv推荐服务"""
    return service_container.get_arxiv_service()