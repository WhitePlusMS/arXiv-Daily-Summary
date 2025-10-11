#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv分类浏览器 - 显示所有可用的ArXiv分类
"""

from streamlit_ui.ui_components.main_dashboard_components import render_footer
from streamlit_ui.ui_components.category_browser_components import (
    render_category_browser_header,
    render_statistics_card,
    render_category_section,
    render_usage_guide
)
from streamlit_ui.services.category_browser_service import CategoryService


def main():
    """主函数 - 组装分类浏览器页面"""
    # 渲染页面头部
    render_category_browser_header()
    
    # 初始化分类服务
    category_service = CategoryService()
    
    # 加载分类数据
    categories = category_service.load_categories_data()
    
    if not categories:
        import streamlit as st
        st.error("无法加载分类数据，请检查数据文件是否存在。")
        return
    
    # 渲染统计卡片
    render_statistics_card(categories)
    
    # 渲染分类区域
    for main_cat in categories:
        render_category_section(main_cat)
    
    # 渲染使用指南
    render_usage_guide()
    
    # 渲染页面底部
    render_footer()


if __name__ == "__main__":
    main()