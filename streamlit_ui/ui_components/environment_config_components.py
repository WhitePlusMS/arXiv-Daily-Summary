#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境配置UI组件 - Streamlit界面渲染组件
"""

import streamlit as st
from streamlit_ui.services.environment_config_service import (
    validate_email, 
    validate_url, 
    track_config_change
)


def render_custom_css():
    """渲染自定义CSS样式"""
    st.markdown("""
    <style>
    .config-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #007bff;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.25rem;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 0.25rem;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.75rem;
        border-radius: 0.25rem;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar_navigation():
    """渲染侧边栏导航"""
    st.sidebar.title("配置导航")
    sections = [
        "🔑 API配置",
        "📚 ArXiv配置", 
        "🤖 LLM配置",
        "📁 文件路径配置",
        "📧 邮件配置",
        "🕐 时区格式配置",
        "📝 日志配置"
    ]
    
    selected_section = st.sidebar.selectbox("选择配置分组", sections)
    st.sidebar.markdown("---")
    st.sidebar.subheader("操作")
    
    return selected_section


def render_api_config(config_manager):
    """渲染API配置"""
    st.subheader("🔑 通义千问API配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        api_key = st.text_input(
            "API密钥",
            value=st.session_state.config_changes.get('DASHSCOPE_API_KEY', ''),
            type="password",
            help="您的通义千问API密钥",
            key="api_key_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('DASHSCOPE_API_KEY', api_key)
        
        base_url = st.text_input(
            "API基础URL",
            value=st.session_state.config_changes.get('DASHSCOPE_BASE_URL', ''),
            help="通义千问API的基础URL"
        )
        if validate_url(base_url):
            st.session_state.config_changes['DASHSCOPE_BASE_URL'] = base_url
        else:
            st.error("请输入有效的URL格式")
    
    with col2:
        model_options = [
            "qwen3-235b-a22b-instruct-2507",
            "qwen3-30b-a3b-instruct-2507",
            "qwen-turbo",
            "qwen-plus",
            "qwen-max"
        ]
        
        current_model = st.session_state.config_changes.get('QWEN_MODEL', '')
        # 如果当前模型不在选项中，使用第一个选项
        if current_model not in model_options and model_options:
            current_model = model_options[0]
        
        model = st.selectbox(
            "正文分析与报告模型",
            options=model_options,
            index=model_options.index(current_model) if current_model in model_options else 0,
            help="选择要使用的通义千问模型"
        )
        st.session_state.config_changes['QWEN_MODEL'] = model
        
        # 轻量模型提供商选择（仅保留 DashScope/通义千问）
        provider_options = ["dashscope"]
        current_provider = st.session_state.config_changes.get('LIGHT_MODEL_PROVIDER', '')
        # 如果当前提供商不在选项中，使用第一个选项
        if current_provider not in provider_options and provider_options:
            current_provider = provider_options[0]
            
        light_provider = st.selectbox(
            "分类匹配模型提供方",
            options=provider_options,
            index=provider_options.index(current_provider) if current_provider in provider_options else 0,
            help="选择分类匹配模型的提供方：仅支持 DashScope（通义千问）"
        )
        st.session_state.config_changes['LIGHT_MODEL_PROVIDER'] = light_provider
        
        # 根据提供商显示不同的模型选择
        if light_provider == "dashscope":
            current_light_model = st.session_state.config_changes.get('QWEN_MODEL_LIGHT', '')
            # 如果当前轻量模型不在选项中，使用第二个选项（如果存在）
            if current_light_model not in model_options and len(model_options) > 1:
                current_light_model = model_options[1]
            elif current_light_model not in model_options and model_options:
                current_light_model = model_options[0]
                
            light_model = st.selectbox(
                "分类匹配模型",
                options=model_options,
                index=model_options.index(current_light_model) if current_light_model in model_options else (1 if len(model_options) > 1 else 0),
                help="选择用于分类匹配的通义千问模型"
            )
            st.session_state.config_changes['QWEN_MODEL_LIGHT'] = light_model
        # 已移除本地引擎（Ollama）配置分支


def render_arxiv_config(config_manager):
    """渲染ArXiv配置"""
    st.subheader("📚 ArXiv获取器配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        base_url = st.text_input(
            "ArXiv API基础URL",
            value=st.session_state.config_changes.get('ARXIV_BASE_URL', ''),
            help="ArXiv API的基础URL"
        )
        st.session_state.config_changes['ARXIV_BASE_URL'] = base_url
        
        retries = st.number_input(
            "重试次数",
            min_value=1,
            max_value=10,
            value=int(st.session_state.config_changes.get('ARXIV_RETRIES', 1)),
            help="请求失败时的重试次数",
            key="arxiv_retries_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('ARXIV_RETRIES', str(retries))
        
        delay = st.number_input(
            "请求延迟（秒）",
            min_value=1,
            max_value=60,
            value=int(st.session_state.config_changes.get('ARXIV_DELAY', 1)),
            help="请求间隔延迟时间",
            key="arxiv_delay_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('ARXIV_DELAY', str(delay))
    
    with col2:
        max_entries = st.number_input(
            "最大条目数",
            min_value=1,
            max_value=1000,
            value=int(st.session_state.config_changes.get('MAX_ENTRIES', 50)),
            help="每次查询的最大论文数量",
            key="arxiv_max_entries_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('MAX_ENTRIES', str(max_entries))
        
        brief_count = st.number_input(
            "简要分析论文数",
            min_value=1,
            max_value=50,
            value=int(st.session_state.config_changes.get('NUM_BRIEF_PAPERS', 7)),
            help="进行简要分析的论文数量",
            key="brief_analysis_count_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('NUM_BRIEF_PAPERS', str(brief_count))
        
        detailed_count = st.number_input(
            "详细分析论文数",
            min_value=1,
            max_value=10,
            value=int(st.session_state.config_changes.get('NUM_DETAILED_PAPERS', 3)),
            help="进行详细分析的论文数量",
            key="detailed_analysis_count_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('NUM_DETAILED_PAPERS', str(detailed_count))


def render_llm_config(config_manager):
    """渲染LLM配置"""
    st.subheader("🤖 LLM参数配置")
    
    # 通义千问参数配置
    st.markdown("#### 通义千问参数")
    col1, col2 = st.columns(2)
    
    with col1:
        qwen_temp = st.slider(
            "正文分析与报告模型温度",
            min_value=0.0,
            max_value=2.0,
            value=float(st.session_state.config_changes.get('QWEN_MODEL_TEMPERATURE', 0.0)),
            step=0.1,
            help="控制生成文本的随机性",
            key="qwen_temp_slider"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('QWEN_MODEL_TEMPERATURE', str(qwen_temp))
        
        qwen_top_p = st.slider(
            "正文分析与报告模型 Top-p",
            min_value=0.0,
            max_value=1.0,
            value=float(st.session_state.config_changes.get('QWEN_MODEL_TOP_P', 0.0)),
            step=0.05,
            help="控制生成文本的多样性",
            key="qwen_top_p_slider"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('QWEN_MODEL_TOP_P', str(qwen_top_p))
        
        qwen_max_tokens = st.number_input(
            "正文分析与报告模型最大令牌数",
            min_value=100,
            max_value=8000,
            value=int(st.session_state.config_changes.get('QWEN_MODEL_MAX_TOKENS', 100)),
            help="生成文本的最大长度",
            key="qwen_max_tokens_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('QWEN_MODEL_MAX_TOKENS', str(qwen_max_tokens))
    
    with col2:
        qwen_light_temp = st.slider(
            "分类匹配模型温度",
            min_value=0.0,
            max_value=2.0,
            value=float(st.session_state.config_changes.get('QWEN_MODEL_LIGHT_TEMPERATURE', 0.0)),
            step=0.1,
            help="分类匹配模型的温度参数",
            key="qwen_light_temp_slider"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('QWEN_MODEL_LIGHT_TEMPERATURE', str(qwen_light_temp))
        
        qwen_light_top_p = st.slider(
            "分类匹配模型 Top-p",
            min_value=0.0,
            max_value=1.0,
            value=float(st.session_state.config_changes.get('QWEN_MODEL_LIGHT_TOP_P', 0.0)),
            step=0.05,
            help="分类匹配模型的 Top-p 参数",
            key="qwen_light_top_p_slider"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('QWEN_MODEL_LIGHT_TOP_P', str(qwen_light_top_p))
        
        qwen_light_max_tokens = st.number_input(
            "分类匹配模型最大令牌数",
            min_value=50,
            max_value=2000,
            value=int(st.session_state.config_changes.get('QWEN_MODEL_LIGHT_MAX_TOKENS', 50)),
            help="分类匹配模型生成文本的最大长度",
            key="qwen_light_max_tokens_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('QWEN_MODEL_LIGHT_MAX_TOKENS', str(qwen_light_max_tokens))
    
    # 已移除 OLLAMA 参数配置
    
    # 通用配置
    st.markdown("#### 通用配置")
    max_workers = st.number_input(
        "最大工作线程数",
        min_value=1,
        max_value=20,
        value=int(st.session_state.config_changes.get('MAX_WORKERS', 1)),
        help="并发处理的最大线程数",
        key="max_workers_input"
    )
    # 使用辅助函数跟踪配置更改
    track_config_change('MAX_WORKERS', str(max_workers))


def render_file_config(config_manager):
    """渲染文件路径配置"""
    st.subheader("📁 文件路径配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        user_categories_file = st.text_input(
            "研究兴趣描述文件",
            value=st.session_state.config_changes.get('USER_CATEGORIES_FILE', '../../data/users/user_categories.json'),
            help="研究兴趣描述文件路径"
        )
        st.session_state.config_changes['USER_CATEGORIES_FILE'] = user_categories_file
        
        save_directory = st.text_input(
            "保存目录",
            value=st.session_state.config_changes.get('SAVE_DIRECTORY', './arxiv_history'),
            help="报告保存目录路径"
        )
        st.session_state.config_changes['SAVE_DIRECTORY'] = save_directory
    
    with col2:
        save_markdown = st.checkbox(
            "保存为Markdown格式",
            value=st.session_state.config_changes.get('SAVE_MARKDOWN', 'true').lower() == 'true',
            help="是否保存为Markdown格式"
        )
        st.session_state.config_changes['SAVE_MARKDOWN'] = str(save_markdown).lower()


def render_email_config(config_manager):
    """渲染邮件配置"""
    st.subheader("📧 邮件配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        smtp_server = st.text_input(
            "SMTP服务器",
            value=st.session_state.config_changes.get('SMTP_SERVER', 'smtp.gmail.com'),
            help="邮件服务器地址"
        )
        st.session_state.config_changes['SMTP_SERVER'] = smtp_server
        
        smtp_port = st.number_input(
            "SMTP端口",
            min_value=1,
            max_value=65535,
            value=int(st.session_state.config_changes.get('SMTP_PORT', 587)),
            help="邮件服务器端口",
            key="smtp_port_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('SMTP_PORT', str(smtp_port))
        
        sender_email = st.text_input(
            "发件人邮箱",
            value=st.session_state.config_changes.get('SENDER_EMAIL', ''),
            help="发送邮件的邮箱地址"
        )
        if sender_email and validate_email(sender_email):
            st.session_state.config_changes['SENDER_EMAIL'] = sender_email
        elif sender_email:
            st.error("请输入有效的邮箱格式")
    
    with col2:
        email_password = st.text_input(
            "邮箱密码/应用密码",
            value=st.session_state.config_changes.get('EMAIL_PASSWORD', ''),
            type="password",
            help="邮箱密码或应用专用密码"
        )
        st.session_state.config_changes['EMAIL_PASSWORD'] = email_password
        
        receiver_email = st.text_input(
            "收件人邮箱",
            value=st.session_state.config_changes.get('RECEIVER_EMAIL', ''),
            help="接收报告的邮箱地址"
        )
        if receiver_email and validate_email(receiver_email):
            st.session_state.config_changes['RECEIVER_EMAIL'] = receiver_email
        elif receiver_email:
            st.error("请输入有效的邮箱格式")
        
        send_email = st.checkbox(
            "启用邮件发送",
            value=st.session_state.config_changes.get('SEND_EMAIL', 'false').lower() == 'true',
            help="是否启用邮件发送功能"
        )
        st.session_state.config_changes['SEND_EMAIL'] = str(send_email).lower()


def render_timezone_config(config_manager):
    """渲染时区格式配置"""
    st.subheader("🕐 时区格式配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        timezone_options = [
            "Asia/Shanghai",
            "US/Eastern", 
            "US/Pacific",
            "Europe/London",
            "Europe/Paris",
            "UTC"
        ]
        
        current_tz = st.session_state.config_changes.get('TIMEZONE', 'Asia/Shanghai')
        timezone = st.selectbox(
            "时区设置",
            options=timezone_options,
            index=timezone_options.index(current_tz) if current_tz in timezone_options else 0,
            help="选择系统使用的时区"
        )
        st.session_state.config_changes['TIMEZONE'] = timezone
        
        date_format = st.text_input(
            "日期格式",
            value=st.session_state.config_changes.get('DATE_FORMAT', '%Y-%m-%d'),
            help="日期显示格式，如：%Y-%m-%d"
        )
        st.session_state.config_changes['DATE_FORMAT'] = date_format
    
    with col2:
        time_format = st.text_input(
            "时间格式",
            value=st.session_state.config_changes.get('TIME_FORMAT', '%H:%M:%S'),
            help="时间显示格式，如：%H:%M:%S"
        )
        st.session_state.config_changes['TIME_FORMAT'] = time_format
        
        enable_mcp_time = st.checkbox(
            "启用MCP时间服务",
            value=st.session_state.config_changes.get('ENABLE_MCP_TIME_SERVICE', 'false').lower() == 'true',
            help="是否启用MCP时间服务"
        )
        st.session_state.config_changes['ENABLE_MCP_TIME_SERVICE'] = str(enable_mcp_time).lower()


def render_log_config(config_manager):
    """渲染日志配置"""
    st.subheader("📝 日志配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        log_level_options = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        current_level = st.session_state.config_changes.get('LOG_LEVEL', 'INFO')
        log_level = st.selectbox(
            "日志级别",
            options=log_level_options,
            index=log_level_options.index(current_level) if current_level in log_level_options else 1,
            help="设置日志记录级别"
        )
        st.session_state.config_changes['LOG_LEVEL'] = log_level
        
        log_file = st.text_input(
            "日志文件路径",
            value=st.session_state.config_changes.get('LOG_FILE', './logs/arxiv_recommender.log'),
            help="日志文件保存路径"
        )
        st.session_state.config_changes['LOG_FILE'] = log_file
    
    with col2:
        log_max_size = st.number_input(
            "最大日志文件大小(MB)",
            min_value=1,
            max_value=1000,
            value=int(st.session_state.config_changes.get('LOG_MAX_SIZE', 10)),
            help="单个日志文件的最大大小",
            key="log_max_size_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('LOG_MAX_SIZE', str(log_max_size))
        
        log_backup_count = st.number_input(
            "日志备份数量",
            min_value=1,
            max_value=50,
            value=int(st.session_state.config_changes.get('LOG_BACKUP_COUNT', 5)),
            help="保留的日志备份文件数量",
            key="log_backup_count_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('LOG_BACKUP_COUNT', str(log_backup_count))
        
        log_to_console = st.checkbox(
            "启用控制台日志",
            value=st.session_state.config_changes.get('LOG_TO_CONSOLE', 'true').lower() == 'true',
            help="是否在控制台输出日志"
        )
        st.session_state.config_changes['LOG_TO_CONSOLE'] = str(log_to_console).lower()
        
        debug_mode = st.checkbox(
            "启用调试模式",
            value=st.session_state.config_changes.get('DEBUG_MODE', 'false').lower() == 'true',
            help="启用调试模式将使用模拟数据"
        )
        st.session_state.config_changes['DEBUG_MODE'] = str(debug_mode).lower()


def render_footer():
    """渲染页面底部"""
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
        "ArXiv 每日论文推荐系统"
        " | 版本 V 0.1"
        "</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
        "联系作者：WhitePlusMS"
        "</div>",
        unsafe_allow_html=True
    )