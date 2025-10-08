#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Components 模块 - 用户界面组件
"""

from .main_dashboard_components import (
    render_header,
    render_user_config_section,
    render_research_interests_section,
    render_recommendation_section,
    render_history_section,
    render_footer
)

__all__ = [
    'render_header',
    'render_user_config_section', 
    'render_research_interests_section',
    'render_recommendation_section',
    'render_history_section',
    'render_footer'
]