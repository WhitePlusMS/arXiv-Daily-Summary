#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv 论文推荐系统 - 主仪表板页面
重构后的版本：只包含UI组装逻辑
"""

# 导入组件和服务
from streamlit_ui.ui_components.main_dashboard_components import (
    render_header,
    render_user_config_section,
    render_research_interests_section,
    render_recommendation_section,
    render_history_section,
    render_footer
)
from streamlit_ui.services.main_dashboard_service import ArxivRecommenderService


def main():
    """主函数 - UI组装"""
    
    # 渲染页面头部（包含页面配置和时间显示）
    render_header()
    
    # 初始化服务
    ArxivRecommenderService.initialize_service()
    
    # 获取服务实例
    service = ArxivRecommenderService.get_service()
    
    # 渲染用户配置选择区域
    selected_profile_name, selected_profile = render_user_config_section(service.get_user_profiles(), service)
    
    # 渲染研究兴趣输入区域
    render_research_interests_section(service)
    
    # 渲染推荐系统执行区域
    render_recommendation_section(service, selected_profile_name)
    
    # 渲染历史报告管理区域
    render_history_section(service)
    
    # 渲染页面底部
    render_footer()


if __name__ == "__main__":
    main()