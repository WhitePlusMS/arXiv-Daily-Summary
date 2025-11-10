#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv分类匹配器UI组件 - Streamlit界面渲染组件

完全封装 Streamlit 操作，提供纯净的业务逻辑接口
"""

import streamlit as st
import pandas as pd
import datetime as dt
from pathlib import Path


# ==================== 会话状态管理封装 ====================

def initialize_session_state():
    """初始化Streamlit会话状态"""
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    if 'is_matching' not in st.session_state:
        st.session_state.is_matching = False
    if 'latest_results' not in st.session_state:
        st.session_state.latest_results = None
    if 'latest_matcher' not in st.session_state:
        st.session_state.latest_matcher = None


def get_session_state(key, default=None):
    """获取会话状态值"""
    return getattr(st.session_state, key, default)


def set_session_state(key, value):
    """设置会话状态值"""
    setattr(st.session_state, key, value)


def get_latest_results():
    """获取最新匹配结果"""
    return get_session_state('latest_results')


def set_latest_results(results):
    """设置最新匹配结果"""
    set_session_state('latest_results', results)


def get_latest_matcher():
    """获取最新匹配器"""
    return get_session_state('latest_matcher')


def set_latest_matcher(matcher):
    """设置最新匹配器"""
    set_session_state('latest_matcher', matcher)


def get_matching_status():
    """获取匹配状态"""
    return get_session_state('is_matching', False)


def set_matching_status(status):
    """设置匹配状态"""
    set_session_state('is_matching', status)


# ==================== 消息显示封装 ====================

def show_info(message):
    """显示信息消息"""
    st.info(message)


def show_error(message):
    """显示错误消息"""
    st.error(message)


def show_success(message):
    """显示成功消息"""
    st.success(message)


def show_warning(message):
    """显示警告消息"""
    st.warning(message)


# ==================== 进度控制封装 ====================

class ProgressContext:
    """进度上下文管理器"""
    def __init__(self, message):
        self.message = message
        self.spinner = None
    
    def __enter__(self):
        self.spinner = st.spinner(self.message)
        return self.spinner.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.spinner.__exit__(exc_type, exc_val, exc_tb)


def create_progress_context(message):
    """创建进度上下文"""
    return ProgressContext(message)


def render_page_config():
    """渲染页面配置"""
    st.set_page_config(
        page_title="ArXiv分类匹配器",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def render_custom_css():
    """渲染自定义CSS样式"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .result-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .metric-card {
        background-color: #e8f4fd;
        padding: 0.5rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.25rem 0;
    }
    .compact-metric-card {
        background-color: #e8f4fd;
        padding: 0.3rem 0.5rem;
        border-radius: 0.3rem;
        text-align: center;
        margin: 0.2rem 0;
        display: inline-block;
        width: 100%;
    }
    .compact-metric-card h4 {
        margin: 0;
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .compact-metric-card p {
        margin: 0;
        font-size: 0.8rem;
        color: #666;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .optimize-button {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .optimize-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """渲染页面头部"""
    st.markdown('<h1 class="main-header">📚 ArXiv分类匹配器</h1>', unsafe_allow_html=True)
    st.markdown("---")


def render_sidebar_config(service):
    """渲染侧边栏配置"""
    with st.sidebar:
        st.header("⚙️ 配置选项")
        
        # 展示 DashScope 配置状态
        config = service.get_provider_config()
        if config['configured']:
            st.success("✅ DashScope API密钥已配置")
        else:
            st.error("❌ 请配置DashScope API密钥")
        
        # 匹配参数
        top_n = st.slider("返回结果数量", min_value=1, max_value=10, value=5)
        
        # 刷新按钮
        if st.button("🔄 刷新数据"):
            service.clear_caches()
            st.rerun()
        
        st.markdown("---")
        
        # 实时统计
        st.header("📊 实时统计")
        existing_data = service.load_existing_data()
        stats = service.get_statistics(existing_data)
        if stats:
            st.metric("总记录数", stats['total_records'])
            st.metric("用户数量", stats['unique_users'])
        else:
            st.info("暂无数据记录")
    
    return top_n


def render_research_input_section(service):
    """渲染研究信息输入区域"""
    st.markdown('<h2 class="sub-header">📝 输入研究信息</h2>', unsafe_allow_html=True)
        
    # 用户输入区域
    username = st.text_input(
        "用户名",
        placeholder="请输入您的用户名",
        help="用于标识和保存您的匹配结果",
        disabled=st.session_state.is_matching  # 匹配时禁用输入
    )
    
    # 如果正在匹配，显示警告信息
    if st.session_state.is_matching:
        st.warning("⚠️ 正在进行分类匹配，请等待完成后再修改输入内容")
    
    user_input = st.text_area(
        "研究内容描述",
        value=st.session_state.user_input,
        height=200,
        placeholder="请详细描述您的研究方向和兴趣领域...\n\n例如：\n# 个人研究兴趣\n我正在从事RAG领域的研究。具体来说，我对以下领域感兴趣：\n1. RAG（检索增强生成）\n2. LLM（大语言模型）\n3. 多模态大语言模型",
        help="支持Markdown格式，请尽可能详细地描述您的研究方向",
        key="research_description",
        disabled=st.session_state.is_matching  # 匹配时禁用输入
    )
    
    # 更新session state（仅在非匹配状态下）
    if not st.session_state.is_matching:
        st.session_state.user_input = user_input
    
    return username, user_input


def render_ai_optimize_section(service, user_input):
    """渲染AI优化描述区域"""
    # 优化按钮
    col1, col2 = st.columns([3, 1])
    with col2:
        optimize_clicked = st.button(
            "✨ AI优化描述",
            help="使用AI来扩展和完善您的研究描述",
            use_container_width=True,
            disabled=st.session_state.is_matching  # 匹配时禁用按钮
        )
    
    # 处理优化请求
    if optimize_clicked:
        if not user_input.strip():
            st.error("❌ 请先输入研究内容描述")
        else:
            with st.spinner("🤖 AI正在优化您的研究描述，请稍候..."):
                try:
                    optimized_description = service.optimize_research_description(user_input)
                    
                    # 更新session state和重新运行
                    st.session_state.user_input = optimized_description
                    st.success("✅ 研究描述已优化完成！")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 优化过程中出现错误: {e}")


def render_matching_form():
    """渲染匹配表单"""
    # 匹配表单
    with st.form("matching_form"):
        st.markdown("### 🚀 开始匹配")
        
        # 显示按钮状态
        button_text = "开始匹配分类" if not st.session_state.is_matching else "正在匹配中..."
        button_disabled = st.session_state.is_matching
        
        submitted = st.form_submit_button(
            button_text,
            type="primary",
            use_container_width=True,
            disabled=button_disabled  # 匹配时禁用按钮
        )
    
    return submitted


def render_matching_success():
    """渲染匹配成功消息"""
    st.markdown(
        '<div class="success-message">✅ 匹配完成！结果已保存到数据库。<br>📊 全部115个分类的详细评分已保存到 ../../data/users/detailed_scores/ 目录。</div>',
        unsafe_allow_html=True
    )


def render_results_section(results, service):
    """渲染结果展示区域"""
    if 'latest_results' in st.session_state:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">🎯 匹配结果</h2>', unsafe_allow_html=True)
        
        results = st.session_state.latest_results
        
        # 检查results是否为None或空
        if results is None or len(results) == 0:
            st.info("暂无匹配结果")
            return
        
        # 结果表格
        st.subheader("📈 详细结果")
        results_df = pd.DataFrame([
            {
                "排名": i+1,
                "分类ID": result[0],
                "分类名称": result[1],
                "匹配评分": result[2]
            }
            for i, result in enumerate(results)
        ])
        
        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True
        )
        
        # 可视化图表
        chart_data = service.create_results_chart_data(results)
        if chart_data is not None:
            st.subheader("📊 匹配评分可视化")
            st.bar_chart(chart_data.set_index('分类ID')['匹配评分'])


def render_token_usage_section(service):
    """渲染Token使用统计区域"""
    if 'latest_results' in st.session_state:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">💰 使用统计</h2>', unsafe_allow_html=True)
        matcher = st.session_state.latest_matcher
        token_data = service.get_token_usage_data(matcher)
        
        if token_data:
            # 使用三列布局，但更紧凑
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(
                    f'<div class="compact-metric-card"><h4>{token_data["total_input_tokens"]:,}</h4><p>输入Token</p></div>',
                    unsafe_allow_html=True
                )
            
            with col2:
                st.markdown(
                    f'<div class="compact-metric-card"><h4>{token_data["total_output_tokens"]:,}</h4><p>输出Token</p></div>',
                    unsafe_allow_html=True
                )
            
            with col3:
                st.markdown(
                    f'<div class="compact-metric-card"><h4>{token_data["total_tokens"]:,}</h4><p>总Token</p></div>',
                    unsafe_allow_html=True
                )


def render_detailed_scores_section(service):
    """渲染详细评分文件管理区域"""
    st.markdown("### 📊 详细评分文件")
    
    score_files = service.get_detailed_score_files()
    
    if score_files:
        st.info(f"📁 找到 {len(score_files)} 个详细评分文件")
        
        # 显示最近的5个文件
        for i, file_path in enumerate(score_files[:5]):
            file_info = service.get_file_info(file_path)
            
            with st.expander(f"📄 {file_info['name']} ({file_info['size']} bytes, {file_info['time']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    try:
                        file_content = service.read_file_content(file_path)
                        st.download_button(
                            label="📥 下载JSON文件",
                            data=file_content,
                            file_name=file_info['name'],
                            mime="application/json",
                            key=f"download_btn_{i}"
                        )
                    except Exception as e:
                        st.error(f"读取文件失败: {e}")
                
                with col2:
                    if st.button(f"🗑️ 删除", key=f"delete_score_{i}"):
                        success, message = service.delete_score_file(file_path)
                        if success:
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(message)
        
        if len(score_files) > 5:
            st.info(f"还有 {len(score_files) - 5} 个文件未显示...")
    else:
        st.info("📂 暂无详细评分文件")


def render_user_data_management_section(service):
    """渲染用户数据管理区域"""
    st.markdown("---")
    st.markdown('<h2 class="sub-header">👥 用户数据管理</h2>', unsafe_allow_html=True)
    
    # 详细评分文件管理
    render_detailed_scores_section(service)
    
    st.markdown("---")
    
    existing_data = service.load_existing_data()
    if existing_data:
        # 搜索和操作栏
        search_term = st.text_input(
            "🔍 搜索用户或内容",
            placeholder="输入用户名或研究内容关键词..."
        )
        
        # 过滤数据
        filtered_data = service.filter_data(existing_data, search_term)
        
        # 批量操作和导出功能
        render_batch_operations_section(service, existing_data, filtered_data)
        
        st.info(f"显示 {len(filtered_data)} / {len(existing_data)} 条记录")
        
        # 用户记录展示
        render_user_records_section(service, existing_data, filtered_data)
    else:
        st.info("📝 暂无数据记录，请先进行分类匹配。")


def render_batch_operations_section(service, existing_data, filtered_data):
    """渲染批量操作区域"""
    st.markdown("### 📋 批量操作")
    
    # 初始化批量选择状态
    if 'selected_items' not in st.session_state:
        st.session_state.selected_items = set()
    
    # 全选/取消全选
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("✅ 全选", use_container_width=True):
            st.session_state.selected_items = set(range(len(filtered_data)))
            st.rerun()
    
    with col2:
        if st.button("❌ 取消全选", use_container_width=True):
            st.session_state.selected_items = set()
            st.rerun()
    
    with col3:
        if st.button("🗑️ 批量删除", use_container_width=True, type="secondary"):
            if st.session_state.selected_items:
                st.session_state.show_batch_delete_confirm = True
                st.rerun()
            else:
                st.warning("请先选择要删除的记录")
    
    with col4:
        if st.button("📥 导出JSON", use_container_width=True):
            export_data = [filtered_data[i] for i in range(len(filtered_data))]
            json_str = service.export_data_to_json(export_data)
            st.download_button(
                label="💾 下载JSON文件",
                data=json_str,
                file_name=f"user_categories_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # 批量删除确认对话框
    if st.session_state.get('show_batch_delete_confirm', False):
        st.warning(f"⚠️ 确认要删除选中的 {len(st.session_state.selected_items)} 条记录吗？此操作不可撤销！")
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("✅ 确认删除", type="primary", key="confirm_batch_delete"):
                # 执行批量删除
                deleted_count = service.batch_delete_records(existing_data, st.session_state.selected_items)
                
                # 清除状态
                st.session_state.selected_items = set()
                st.session_state.show_batch_delete_confirm = False
                service.clear_caches()
                st.success(f"✅ 已成功删除 {deleted_count} 条记录")
                st.rerun()
        
        with col_cancel:
            if st.button("❌ 取消", key="cancel_batch_delete"):
                st.session_state.show_batch_delete_confirm = False
                st.rerun()


def render_user_records_section(service, existing_data, filtered_data):
    """渲染用户记录展示区域"""
    st.markdown("### 📄 用户记录")
    
    for i, item in enumerate(filtered_data):
        # 获取原始索引
        original_index = existing_data.index(item)
        
        with st.expander(f"记录 {i+1}: {item.get('username', 'Unknown')}", expanded=False):
            # 批量选择复选框
            is_selected = st.checkbox(
                f"选择记录 {i+1}",
                value=i in st.session_state.selected_items,
                key=f"select_{i}"
            )
            
            if is_selected:
                st.session_state.selected_items.add(i)
            else:
                st.session_state.selected_items.discard(i)
            
            # 编辑模式切换
            edit_key = f"edit_mode_{i}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False
            
            # 操作按钮
            render_record_action_buttons(service, existing_data, original_index, i, item)
            
            # 显示/编辑内容
            render_record_content(item, i, edit_key)


def render_record_action_buttons(service, existing_data, original_index, i, item):
    """渲染记录操作按钮"""
    edit_key = f"edit_mode_{i}"
    
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if st.button("✏️ 编辑" if not st.session_state[edit_key] else "💾 保存", 
                   key=f"edit_btn_{i}", use_container_width=True):
            if st.session_state[edit_key]:
                # 保存编辑
                new_username = st.session_state.get(f"edit_username_{i}", item.get('username', ''))
                new_category_id = st.session_state.get(f"edit_category_{i}", item.get('category_id', ''))
                new_user_input = st.session_state.get(f"edit_input_{i}", item.get('user_input', ''))
                
                # 更新数据
                success = service.update_record(existing_data, original_index, new_username, new_category_id, new_user_input)
                if success:
                    st.session_state[edit_key] = False
                    service.clear_caches()
                    st.success("✅ 保存成功")
                    st.rerun()
            else:
                # 进入编辑模式
                st.session_state[edit_key] = True
                st.rerun()
    
    with btn_col2:
        if st.session_state[edit_key]:
            if st.button("❌ 取消", key=f"cancel_btn_{i}", use_container_width=True):
                st.session_state[edit_key] = False
                st.rerun()
        else:
            if st.button("🗑️ 删除", key=f"delete_btn_{i}", use_container_width=True):
                st.session_state[f"show_delete_confirm_{i}"] = True
                st.rerun()
    
    # 删除确认对话框
    if st.session_state.get(f"show_delete_confirm_{i}", False):
        st.warning("⚠️ 确认要删除这条记录吗？此操作不可撤销！")
        del_col1, del_col2 = st.columns(2)
        with del_col1:
            if st.button("✅ 确认删除", key=f"confirm_del_{i}", type="primary"):
                success = service.delete_single_record(existing_data, original_index)
                if success:
                    st.session_state[f"show_delete_confirm_{i}"] = False
                    service.clear_caches()
                    st.success("✅ 删除成功")
                    st.rerun()
        
        with del_col2:
            if st.button("❌ 取消删除", key=f"cancel_del_{i}"):
                st.session_state[f"show_delete_confirm_{i}"] = False
                st.rerun()


def render_record_content(item, i, edit_key):
    """渲染记录内容"""
    # 显示/编辑内容
    if st.session_state[edit_key]:
        # 编辑模式
        st.markdown("**编辑用户信息:**")
        
        edited_username = st.text_input(
            "用户名",
            value=item.get('username', ''),
            key=f"edit_username_{i}"
        )
        
        edited_category_id = st.text_input(
            "分类ID",
            value=item.get('category_id', ''),
            key=f"edit_category_{i}",
            help="多个分类用逗号分隔"
        )
        
        edited_user_input = st.text_area(
            "研究内容",
            value=item.get('user_input', ''),
            height=200,
            key=f"edit_input_{i}"
        )
    else:
        # 显示模式
        st.markdown("**用户信息:**")
        st.write(f"**用户名:** {item.get('username', 'N/A')}")
        
        st.write("**匹配分类:**")
        categories = item.get('category_id', '').split(',')
        category_display = ", ".join([cat.strip() for cat in categories if cat.strip()])
        st.code(category_display)
        
        st.write("**研究内容:**")
        st.text_area(
            "研究内容",
            value=item.get('user_input', ''),
            height=150,
            disabled=True,
            key=f"display_content_{i}",
            label_visibility="collapsed"
        )


def render_footer():
    """渲染页脚信息"""
    st.markdown(
        """
        <div style="text-align: center; color: #666; padding: 1rem;">
            <p>🔬 ArXiv分类匹配器 | 基于大语言模型的智能分类推荐系统</p>
            <p>💡 支持多用户、实时匹配、结果可视化</p>
        </div>
        """
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