#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv推荐系统 - 环境配置页面
重构后的版本：只包含UI组装逻辑
"""

import streamlit as st

# 导入组件和服务
from ui_components.environment_config_components import (
    render_custom_css,
    render_sidebar_navigation,
    render_api_config,
    render_arxiv_config,
    render_llm_config,
    render_file_config,
    render_email_config,
    render_timezone_config,
    render_log_config,
    render_footer
)
from services.env_config_service import (
    EnvConfigManager,
    initialize_config_state,
    check_config_changes,
    handle_save_config,
    handle_reload_config,
    handle_restore_default
)

def main():
    """主函数 - UI组装"""
    
    # 设置页面配置
    st.set_page_config(
        page_title="ArXiv推荐系统 - 环境配置",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 渲染自定义CSS样式
    render_custom_css()
    
    # 页面标题
    st.title("⚙️ ArXiv推荐系统 - 环境配置")
    
    # 初始化配置管理器
    config_manager = EnvConfigManager()
    
    # 初始化配置状态
    initialize_config_state(config_manager)
    
    # 检查配置更改状态
    check_config_changes(config_manager)
    
    st.markdown("---")
    
    # 渲染侧边栏导航
    selected_section = render_sidebar_navigation()
    
    # 配置区域
    config_container = st.container()
    
    with config_container:
        if selected_section == "🔑 API配置":
            render_api_config(config_manager)
        elif selected_section == "📚 ArXiv配置":
            render_arxiv_config(config_manager)
        elif selected_section == "🤖 LLM配置":
            render_llm_config(config_manager)
        elif selected_section == "📁 文件路径配置":
            render_file_config(config_manager)
        elif selected_section == "📧 邮件配置":
            render_email_config(config_manager)
        elif selected_section == "🕐 时区格式配置":
            render_timezone_config(config_manager)
        elif selected_section == "📝 日志配置":
            render_log_config(config_manager)
    
    # 底部操作按钮
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            handle_save_config(config_manager)
    
    with col2:
        if st.button("🔄 重新加载", use_container_width=True):
            handle_reload_config(config_manager)
    
    with col3:
        if st.button("📋 恢复默认", use_container_width=True):
            handle_restore_default(config_manager)
    
    # 渲染页面底部
    render_footer()


if __name__ == "__main__":
    main()
