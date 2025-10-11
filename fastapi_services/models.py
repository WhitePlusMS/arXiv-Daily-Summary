#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型 - Pydantic模型定义
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class UserProfile(BaseModel):
    """用户配置模型"""
    username: str
    user_input: str
    category_id: str


class RecommendationRequest(BaseModel):
    """推荐请求模型"""
    profile_name: str
    debug_mode: bool = False


class RecommendationResult(BaseModel):
    """推荐结果模型"""
    success: bool
    report: Optional[str] = None
    summary_content: Optional[str] = None
    detailed_analysis: Optional[str] = None
    brief_analysis: Optional[str] = None
    html_content: Optional[str] = None
    html_filepath: Optional[str] = None
    filename: Optional[str] = None
    target_date: Optional[str] = None
    debug_mode: Optional[bool] = False
    error: Optional[str] = None
    warning: Optional[str] = None
    show_weekend_tip: Optional[bool] = False
    traceback: Optional[str] = None


class ResearchInterestsRequest(BaseModel):
    """研究兴趣更新请求模型"""
    interests: List[str]


class InitializeRequest(BaseModel):
    """初始化请求模型"""
    profile_name: str


# 分类匹配器相关请求模型
class OptimizeRequest(BaseModel):
    """优化研究描述请求"""
    user_input: str


class MatchRequest(BaseModel):
    """执行分类匹配请求"""
    username: str
    user_input: str
    top_n: int = 5


class UpdateRecordRequest(BaseModel):
    """更新记录请求"""
    index: int
    username: str
    category_id: str
    user_input: str


class BatchDeleteRequest(BaseModel):
    """批量删除记录请求"""
    indices: List[int]