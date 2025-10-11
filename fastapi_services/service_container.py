#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务容器 - 依赖注入容器，管理所有服务实例
"""

from functools import lru_cache
from .main_dashboard_service import ArxivRecommenderService
from .category_matcher_service import CategoryMatcherService
from .environment_config_service import EnvConfigService


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

    @lru_cache(maxsize=1)
    def get_category_matcher_service(self) -> CategoryMatcherService:
        """获取分类匹配器服务实例"""
        if 'category_matcher_service' not in self._services:
            self._services['category_matcher_service'] = CategoryMatcherService()
        return self._services['category_matcher_service']

    @lru_cache(maxsize=1)
    def get_env_config_service(self) -> EnvConfigService:
        """获取环境配置服务实例"""
        if 'env_config_service' not in self._services:
            self._services['env_config_service'] = EnvConfigService()
        return self._services['env_config_service']


# 全局服务容器实例
service_container = ServiceContainer()


# FastAPI依赖注入函数
def get_arxiv_service() -> ArxivRecommenderService:
    """FastAPI依赖注入：获取ArXiv推荐服务"""
    return service_container.get_arxiv_service()

def get_category_matcher_service() -> CategoryMatcherService:
    """FastAPI依赖注入：获取分类匹配器服务"""
    return service_container.get_category_matcher_service()

def get_env_config_service() -> EnvConfigService:
    """FastAPI依赖注入：获取环境配置服务"""
    return service_container.get_env_config_service()