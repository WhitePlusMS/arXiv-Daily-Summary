"""ArXiv分类匹配器 - Streamlit Web界面

基于category_matcher.py功能创建的用户友好界面，支持：
- 用户输入研究内容
- 实时匹配计算
- 结果可视化展示
- JSON数据管理
"""

import streamlit as st
import json
import os
import sys
from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.task2_category_matching.task2_category_matcher import CategoryMatcher, MultiUserDataManager

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'), override=True)

# 页面配置
st.set_page_config(
    page_title="ArXiv分类匹配器",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
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
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_existing_data():
    """加载现有的JSON数据"""
    # 获取项目根目录的绝对路径
    project_root = Path(__file__).parent.parent
    json_file = project_root / "data" / "users" / "user_categories.json"
    
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"加载JSON文件失败: {e}")
            return []
    return []

def save_user_data(data):
    """保存用户数据到JSON文件"""
    # 获取项目根目录的绝对路径
    project_root = Path(__file__).parent.parent
    json_file = project_root / "data" / "users" / "user_categories.json"
    
    try:
        # 确保目录存在
        json_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存数据
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        st.error(f"保存JSON文件失败: {e}")
        return False

@st.cache_resource
def initialize_matcher():
    """初始化分类匹配器（缓存以提高性能）"""
    # 强制重新加载环境变量
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'), override=True)
    
    model = os.getenv("QWEN_MODEL_LIGHT", "qwen-plus")
    base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        st.error("❌ 请配置API密钥")
        st.info("请前往 **环境配置** 页面设置 DASHSCOPE_API_KEY")
        return None
    
    try:
        matcher = CategoryMatcher(model, base_url, api_key)
        return matcher
    except Exception as e:
        st.error(f"❌ 初始化匹配器失败: {e}")
        st.stop()

def create_results_chart(results: List[Tuple[str, str, int]]):
    """创建结果可视化图表"""
    if not results:
        return None
    
    # 准备数据用于Streamlit内置图表
    chart_data = pd.DataFrame({
        '分类ID': [r[0] for r in results],
        '分类名称': [r[1][:20] + '...' if len(r[1]) > 20 else r[1] for r in results],
        '匹配评分': [r[2] for r in results]
    })
    
    return chart_data

def display_token_usage(matcher):
    """显示Token使用统计"""
    if hasattr(matcher, 'total_tokens') and matcher.total_tokens > 0:
        # 使用三列布局，但更紧凑
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(
                f'<div class="compact-metric-card"><h4>{matcher.total_input_tokens:,}</h4><p>输入Token</p></div>',
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f'<div class="compact-metric-card"><h4>{matcher.total_output_tokens:,}</h4><p>输出Token</p></div>',
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f'<div class="compact-metric-card"><h4>{matcher.total_tokens:,}</h4><p>总Token</p></div>',
                unsafe_allow_html=True
            )

def main():
    """主界面函数"""
    # 页面标题
    st.markdown('<h1 class="main-header">📚 ArXiv分类匹配器</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置选项")
        
        # API配置状态
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if api_key:
            st.success("✅ API密钥已配置")
        else:
            st.error("❌ 请配置API密钥")
        
        # 匹配参数
        top_n = st.slider("返回结果数量", min_value=1, max_value=10, value=5)
        
        # 刷新按钮
        if st.button("🔄 刷新数据"):
            st.cache_data.clear()
            st.cache_resource.clear()
            # 强制重新加载环境变量
            load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'), override=True)
            st.rerun()
        
        st.markdown("---")
        
        # 实时统计
        st.header("📊 实时统计")
        existing_data = load_existing_data()
        if existing_data:
            # 用户统计
            usernames = [item.get('username', 'Unknown') for item in existing_data]
            unique_users = len(set(usernames))
            
            st.metric("总记录数", len(existing_data))
            st.metric("用户数量", unique_users)
        else:
            st.info("暂无数据记录")
    
    # 主界面布局
    st.markdown('<h2 class="sub-header">📝 输入研究信息</h2>', unsafe_allow_html=True)
        
    # 用户输入表单
    with st.form("matching_form"):
        username = st.text_input(
            "用户名",
            placeholder="请输入您的用户名",
            help="用于标识和保存您的匹配结果"
        )
        
        user_input = st.text_area(
            "研究内容描述",
            height=200,
            placeholder="请详细描述您的研究方向和兴趣领域...\n\n例如：\n# 个人研究兴趣\n我正在从事RAG领域的研究。具体来说，我对以下领域感兴趣：\n1. RAG（检索增强生成）\n2. LLM（大语言模型）\n3. 多模态大语言模型",
            help="支持Markdown格式，请尽可能详细地描述您的研究方向"
        )
        
        submitted = st.form_submit_button(
            "🚀 开始匹配",
            type="primary",
            use_container_width=True
        )
        
    # 处理表单提交
    if submitted:
        if not username.strip():
            st.error("❌ 请输入用户名")
        elif not user_input.strip():
            st.error("❌ 请输入研究内容描述")
        else:
            # 初始化匹配器
            with st.spinner("🔧 初始化匹配器..."):
                matcher = initialize_matcher()
            
            # 检查匹配器是否初始化成功
            if matcher is None:
                st.warning("⚠️ 无法初始化匹配器，请检查API配置")
            else:
                # 执行匹配
                with st.spinner("🔍 正在匹配分类，请稍候..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        # 模拟进度更新
                        for i in range(10):
                            progress_bar.progress((i + 1) / 10)
                            status_text.text(f"正在评估分类 {i*10 + 1}-{(i+1)*10}...")
                        
                        # 执行实际匹配
                        results = matcher.match_categories(user_input, top_n=top_n)
                        
                        progress_bar.progress(1.0)
                        status_text.text("✅ 匹配完成！")
                        
                        # 保存结果
                        data_manager = MultiUserDataManager("data/users/user_categories.json")
                        data_manager.add_user_result(username, results, user_input)
                        data_manager.save_to_json()
                        
                        # 显示成功消息
                        st.markdown(
                            '<div class="success-message">✅ 匹配完成！结果已保存到数据库。</div>',
                            unsafe_allow_html=True
                        )
                        
                        # 存储结果到session state
                        st.session_state.latest_results = results
                        st.session_state.latest_matcher = matcher
                        
                        # 清除缓存以刷新数据
                        st.cache_data.clear()
                        
                    except Exception as e:
                        st.error(f"❌ 匹配过程中出现错误: {e}")
                        progress_bar.empty()
                        status_text.empty()
    
    # 结果展示区域
    if 'latest_results' in st.session_state:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">🎯 匹配结果</h2>', unsafe_allow_html=True)
        
        results = st.session_state.latest_results
        matcher = st.session_state.latest_matcher
        
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
        chart_data = create_results_chart(results)
        if chart_data is not None:
            st.subheader("📊 匹配评分可视化")
            st.bar_chart(chart_data.set_index('分类ID')['匹配评分'])
    
    # Token使用统计
    if 'latest_results' in st.session_state:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">💰 使用统计</h2>', unsafe_allow_html=True)
        matcher = st.session_state.latest_matcher
        display_token_usage(matcher)
    
    # 用户数据管理
    st.markdown("---")
    st.markdown('<h2 class="sub-header">👥 用户数据管理</h2>', unsafe_allow_html=True)
    
    existing_data = load_existing_data()
    if existing_data:
        # 搜索和操作栏（单栏布局）
        search_term = st.text_input(
            "🔍 搜索用户或内容",
            placeholder="输入用户名或研究内容关键词..."
        )
        
        # 过滤数据
        filtered_data = existing_data
        if search_term:
            filtered_data = [
                item for item in existing_data
                if search_term.lower() in item.get('username', '').lower() or
                   search_term.lower() in item.get('user_input', '').lower() or
                   search_term.lower() in item.get('category_id', '').lower()
            ]
        
        # 批量操作和导出功能
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
                import json
                from datetime import datetime
                export_data = [filtered_data[i] for i in range(len(filtered_data))]
                json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
                st.download_button(
                    label="💾 下载JSON文件",
                    data=json_str,
                    file_name=f"user_categories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
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
                    indices_to_delete = sorted(st.session_state.selected_items, reverse=True)
                    for idx in indices_to_delete:
                        if 0 <= idx < len(existing_data):
                            existing_data.pop(idx)
                    
                    # 保存到文件
                    save_user_data(existing_data)
                    
                    # 清除状态
                    st.session_state.selected_items = set()
                    st.session_state.show_batch_delete_confirm = False
                    st.cache_data.clear()
                    st.success(f"✅ 已成功删除 {len(indices_to_delete)} 条记录")
                    st.rerun()
            
            with col_cancel:
                if st.button("❌ 取消", key="cancel_batch_delete"):
                    st.session_state.show_batch_delete_confirm = False
                    st.rerun()
        
        st.info(f"显示 {len(filtered_data)} / {len(existing_data)} 条记录")
        
        # 用户记录展示（单栏布局）
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
                edit_key = f"edit_mode_{original_index}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False
                
                # 操作按钮
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                
                with btn_col1:
                    if st.button("✏️ 编辑" if not st.session_state[edit_key] else "💾 保存", 
                               key=f"edit_btn_{original_index}", use_container_width=True):
                        if st.session_state[edit_key]:
                            # 保存编辑
                            new_username = st.session_state.get(f"edit_username_{original_index}", item.get('username', ''))
                            new_category_id = st.session_state.get(f"edit_category_{original_index}", item.get('category_id', ''))
                            new_user_input = st.session_state.get(f"edit_input_{original_index}", item.get('user_input', ''))
                            
                            # 更新数据
                            existing_data[original_index]['username'] = new_username
                            existing_data[original_index]['category_id'] = new_category_id
                            existing_data[original_index]['user_input'] = new_user_input
                            
                            # 保存到文件
                            save_user_data(existing_data)
                            st.session_state[edit_key] = False
                            st.cache_data.clear()
                            st.success("✅ 保存成功")
                            st.rerun()
                        else:
                            # 进入编辑模式
                            st.session_state[edit_key] = True
                            st.rerun()
                
                with btn_col2:
                    if st.button("🗑️ 删除", key=f"delete_btn_{original_index}", use_container_width=True):
                        st.session_state[f"show_delete_confirm_{original_index}"] = True
                        st.rerun()
                
                with btn_col3:
                    if st.button("❌ 取消" if st.session_state[edit_key] else "📋 复制", 
                               key=f"cancel_btn_{original_index}", use_container_width=True):
                        if st.session_state[edit_key]:
                            st.session_state[edit_key] = False
                            st.rerun()
                        else:
                            # 复制功能
                            st.code(f"用户名: {item.get('username', '')}\n分类ID: {item.get('category_id', '')}\n研究内容: {item.get('user_input', '')}")
                
                # 删除确认对话框
                if st.session_state.get(f"show_delete_confirm_{original_index}", False):
                    st.warning("⚠️ 确认要删除这条记录吗？此操作不可撤销！")
                    del_col1, del_col2 = st.columns(2)
                    with del_col1:
                        if st.button("✅ 确认删除", key=f"confirm_del_{original_index}", type="primary"):
                            existing_data.pop(original_index)
                            save_user_data(existing_data)
                            st.session_state[f"show_delete_confirm_{original_index}"] = False
                            st.cache_data.clear()
                            st.success("✅ 删除成功")
                            st.rerun()
                    
                    with del_col2:
                        if st.button("❌ 取消删除", key=f"cancel_del_{original_index}"):
                            st.session_state[f"show_delete_confirm_{original_index}"] = False
                            st.rerun()
                
                # 显示/编辑内容
                if st.session_state[edit_key]:
                    # 编辑模式
                    st.markdown("**编辑用户信息:**")
                    
                    edited_username = st.text_input(
                        "用户名",
                        value=item.get('username', ''),
                        key=f"edit_username_{original_index}"
                    )
                    
                    edited_category_id = st.text_input(
                        "分类ID",
                        value=item.get('category_id', ''),
                        key=f"edit_category_{original_index}",
                        help="多个分类用逗号分隔"
                    )
                    
                    edited_user_input = st.text_area(
                        "研究内容",
                        value=item.get('user_input', ''),
                        height=200,
                        key=f"edit_input_{original_index}"
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
                        key=f"display_content_{original_index}",
                        label_visibility="collapsed"
                    )
    else:
        st.info("📝 暂无数据记录，请先进行分类匹配。")
    # 页脚信息
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

if __name__ == "__main__":
    main()