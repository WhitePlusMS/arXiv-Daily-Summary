#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv 每日论文推荐系统
使用 st.navigation 实现更灵活的多页面应用
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'), override=True)

def main():
    """主应用入口"""
    # 设置页面配置
    st.set_page_config(
        page_title="ArXiv 每日论文推荐系统",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 定义页面
    home_page = st.Page(
        "pages/main_dashboard.py", 
        title="📚 ArXiv 每日论文推荐系统", 
        icon="🏠",
        default=True
    )
    
    classifier_page = st.Page(
        "pages/category_matcher_ui.py", 
        title="🎯 分类匹配器", 
        icon="📊"
    )
    
    config_page = st.Page(
        "pages/environment_config.py", 
        title="⚙️ 环境配置", 
        icon="🔧"
    )
    
    browser_page = st.Page(
        "pages/arxiv_category_browser.py", 
        title="📖 分类浏览器", 
        icon="📋"
    )
    
    # 创建导航
    pg = st.navigation({
        "主要功能": [home_page, classifier_page],
        "系统管理": [config_page, browser_page]
    })
    
    # 运行选中的页面
    pg.run()

if __name__ == "__main__":
    main()