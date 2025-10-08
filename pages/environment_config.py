import streamlit as st
import os
import sys
from typing import Dict, Any
import re
from pathlib import Path

# 页面配置
st.set_page_config(
    page_title="ArXiv推荐系统 - 环境配置",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
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

class EnvConfigManager:
    """环境配置管理器"""
    
    def __init__(self):
        # 获取项目根目录的绝对路径
        # 动态计算项目根目录
        project_root = Path(__file__).parent.parent
        # 将项目根目录添加到sys.path
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        self.env_file = project_root / ".env"
        self.env_example_file = project_root / ".env.example"
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """加载当前配置"""
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip()
    
    def save_config(self, new_config: Dict[str, Any]) -> bool:
        """保存配置到.env文件"""
        try:
            # 确保父目录存在
            self.env_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取原文件保留注释和格式
            lines = []
            if self.env_file.exists():
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # 更新配置值
            updated_lines = []
            updated_keys = set()
            
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    if key in new_config:
                        updated_lines.append(f"{key}={new_config[key]}\n")
                        updated_keys.add(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # 添加新的配置项
            for key, value in new_config.items():
                if key not in updated_keys:
                    updated_lines.append(f"{key}={value}\n")
            
            # 写入文件
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            # 验证写入是否成功
            if not self.env_file.exists():
                raise FileNotFoundError(f"配置文件写入失败: {self.env_file}")
            
            # 重新加载配置以验证
            self.load_config()
            
            # 强制重新加载环境变量到当前进程
            from dotenv import load_dotenv
            load_dotenv(self.env_file, override=True)
            
            # 清除Streamlit缓存以确保其他页面重新加载
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()
            if hasattr(st, 'cache_resource'):
                st.cache_resource.clear()
            
            return True
        except Exception as e:
            st.error(f"保存配置失败: {str(e)}")
            st.error(f"错误类型: {type(e).__name__}")
            st.error(f"文件路径: {self.env_file}")
            return False
    
    def load_example_config(self) -> Dict[str, str]:
        """加载示例配置"""
        example_config = {}
        if self.env_example_file.exists():
            with open(self.env_example_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        example_config[key.strip()] = value.strip()
        return example_config

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url: str) -> bool:
    """验证URL格式"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None

def track_config_change(key: str, value: str) -> None:
    """跟踪配置更改并触发实时更新"""
    # 立即更新配置状态
    st.session_state.config_changes[key] = value
    
    # 创建跟踪键名
    track_key = f'last_{key.lower()}'
    
    # 强制触发状态更新检查
    if track_key not in st.session_state:
        st.session_state[track_key] = value
    elif st.session_state[track_key] != value:
        st.session_state[track_key] = value
        # 触发页面重新渲染以立即显示更改状态
        st.rerun()

def main():
    """主函数"""
    st.title("⚙️ ArXiv推荐系统 - 环境配置")
    
    # 初始化配置管理器
    config_manager = EnvConfigManager()
    
    # 实时状态监控 - 优化配置更改检测逻辑
    if 'config_changes' in st.session_state and config_manager.config:
        # 检查是否有未保存的更改 - 更严格的比较逻辑
        has_changes = False
        changed_keys = []
        
        # 遍历所有可能的配置项，包括session_state中的新增项
        all_keys = set(st.session_state.config_changes.keys()) | set(config_manager.config.keys())
        
        for key in all_keys:
            file_value = str(config_manager.config.get(key, '')).strip()
            session_value = str(st.session_state.config_changes.get(key, '')).strip()
            
            # 更严格的比较：确保类型一致性和值的准确比较
            if file_value != session_value:
                has_changes = True
                changed_keys.append(key)
        
        # 实时显示状态 - 立即响应任何更改
        if changed_keys:
            st.warning(f"⚠️ 有 {len(changed_keys)} 项配置未保存到文件")
            with st.expander(f"📋 查看所有 {len(changed_keys)} 项更改详情", expanded=False):
                for key in changed_keys:
                    file_val = config_manager.config.get(key, '')
                    session_val = st.session_state.config_changes.get(key, '')
                    
                    # 显示完整值，但限制显示长度以保持界面整洁
                    file_display = file_val[:30] + "..." if len(str(file_val)) > 30 else str(file_val)
                    session_display = session_val[:30] + "..." if len(str(session_val)) > 30 else str(session_val)
                    
                    st.write(f"  - **{key}**: 文件=`{file_display}` → 界面=`{session_display}`")
        else:
            st.success("✅ 所有配置已同步，无未保存更改")
            # 添加占位符区域，保持界面布局一致性
            with st.expander("📋 配置状态详情", expanded=False):
                st.info("🎉 当前所有配置项都已保存到 .env 文件中，界面与文件完全同步。")
                st.write("💡 **提示**: 修改任何配置项后，此区域将显示具体的更改详情。")
    
    st.markdown("---")
    

    
    # 侧边栏导航
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
    
    # 操作按钮
    st.sidebar.markdown("---")
    st.sidebar.subheader("操作")
    
    # 存储配置的会话状态 - 确保每次都同步最新的.env内容
    if 'config_changes' not in st.session_state or st.session_state.get('force_reload', False):
        config_manager.load_config()  # 重新加载最新配置
        st.session_state.config_changes = config_manager.config.copy()
        st.session_state.force_reload = False
        
        # 初始化所有配置项的上次值跟踪
        for key in config_manager.config:
            st.session_state[f'last_{key.lower()}'] = config_manager.config[key]
    

    
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
            # 显示保存进度
            with st.spinner("正在保存配置到.env文件..."):
                # 立即保存配置到.env文件
                if config_manager.save_config(st.session_state.config_changes):
                    # 重新加载环境变量确保生效
                    config_manager.load_config()
                    st.session_state.config_changes = config_manager.config.copy()
                    
                    st.rerun()
                else:
                    st.error("❌ 配置保存失败！请检查文件权限或路径是否正确。")
    
    with col2:
        if st.button("🔄 重新加载", use_container_width=True):
            # 显示确认对话框
            if st.session_state.get('confirm_reload', False):
                st.warning("⚠️ 确认要重新加载配置吗？这将丢失所有未保存的更改。")
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("✅ 确认重新加载", type="primary", key="confirm_reload_btn"):
                        # 显示重新加载进度
                        with st.spinner("正在从.env文件重新加载配置..."):
                            # 完全丢弃用户修改，从.env文件重新加载
                            config_manager.load_config()
                            st.session_state.config_changes = config_manager.config.copy()
                            
                            # 显示详细的重新加载结果
                            st.success("✅ 配置重新加载成功！")
                            st.info(f"📂 已从 .env 文件重新加载 {len(config_manager.config)} 项配置")
                            st.info("🔄 所有未保存的界面更改已丢弃，恢复到文件中的配置")
                            
                            # 清除所有相关的session状态
                            st.session_state.force_reload = True
                            st.session_state.confirm_reload = False
                            st.rerun()
                with col_cancel:
                    if st.button("❌ 取消", key="cancel_reload_btn"):
                        st.session_state.confirm_reload = False
                        st.rerun()
            else:
                st.session_state.confirm_reload = True
                st.rerun()
    
    with col3:
        if st.button("📋 恢复默认", use_container_width=True):
            # 显示确认对话框
            if st.session_state.get('confirm_restore', False):
                st.warning("⚠️ 确认要恢复默认配置吗？这将丢失所有当前更改并使用.env.example中的默认值。")
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("✅ 确认恢复默认", type="primary", key="confirm_restore_btn"):
                        # 显示恢复默认配置进度
                        with st.spinner("正在恢复默认配置..."):
                            example_config = config_manager.load_example_config()
                            if example_config:
                                # 直接将默认配置写入.env文件
                                if config_manager.save_config(example_config):
                                    # 重新加载配置确保生效
                                    config_manager.load_config()
                                    st.session_state.config_changes = config_manager.config.copy()
                                    
                                    # 显示详细的恢复结果
                                    st.success("✅ 默认配置恢复成功！")
                                    st.info(f"📋 已从 .env.example 加载 {len(example_config)} 项默认配置")
                                    st.info(f"💾 默认配置已写入 .env 文件并重新加载")
                                    st.info("🔄 所有配置已重置为默认值")
                                    
                                    st.session_state.confirm_restore = False
                                    st.rerun()
                                else:
                                    st.error("❌ 恢复默认配置失败！请检查文件权限。")
                                    st.session_state.confirm_restore = False
                            else:
                                st.error("❌ 无法加载默认配置！请确保该文件存在于项目根目录。")
                                st.session_state.confirm_restore = False
                with col_cancel:
                    if st.button("❌ 取消", key="cancel_restore_btn"):
                        st.session_state.confirm_restore = False
                        st.rerun()
            else:
                st.session_state.confirm_restore = True
                st.rerun()
    # 页脚
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
            value=st.session_state.config_changes.get('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
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
        
        current_model = st.session_state.config_changes.get('QWEN_MODEL', model_options[0])
        model = st.selectbox(
            "主模型（生成报告/详细分析）",
            options=model_options,
            index=model_options.index(current_model) if current_model in model_options else 0,
            help="选择要使用的通义千问模型"
        )
        st.session_state.config_changes['QWEN_MODEL'] = model
        
        # 轻量模型提供商选择
        provider_options = ["qwen", "ollama"]
        current_provider = st.session_state.config_changes.get('LIGHT_MODEL_PROVIDER', 'qwen')
        light_provider = st.selectbox(
            "轻量模型提供商",
            options=provider_options,
            index=provider_options.index(current_provider) if current_provider in provider_options else 0,
            help="选择轻量模型的提供商：通义千问或OLLAMA本地模型"
        )
        st.session_state.config_changes['LIGHT_MODEL_PROVIDER'] = light_provider
        
        # 根据提供商显示不同的模型选择
        if light_provider == "qwen":
            current_light_model = st.session_state.config_changes.get('QWEN_MODEL_LIGHT', model_options[1])
            light_model = st.selectbox(
                "轻量模型（分类匹配）",
                options=model_options,
                index=model_options.index(current_light_model) if current_light_model in model_options else 1,
                help="选择轻量级通义千问模型"
            )
            st.session_state.config_changes['QWEN_MODEL_LIGHT'] = light_model
        else:  # ollama
            ollama_model = st.text_input(
                "OLLAMA轻量模型名称",
                value=st.session_state.config_changes.get('OLLAMA_MODEL_LIGHT', 'llama3.2:3b'),
                help="输入OLLAMA本地模型名称，如：llama3.2:3b, qwen2.5:7b等"
            )
            st.session_state.config_changes['OLLAMA_MODEL_LIGHT'] = ollama_model
            
            ollama_url = st.text_input(
                "OLLAMA服务器地址",
                value=st.session_state.config_changes.get('OLLAMA_BASE_URL', 'http://localhost:11434/v1'),
                help="OLLAMA服务器的API地址"
            )
            st.session_state.config_changes['OLLAMA_BASE_URL'] = ollama_url

def render_arxiv_config(config_manager):
    """渲染ArXiv配置"""
    st.subheader("📚 ArXiv获取器配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        base_url = st.text_input(
            "ArXiv API基础URL",
            value=st.session_state.config_changes.get('ARXIV_BASE_URL', 'http://export.arxiv.org/api/query'),
            help="ArXiv API的基础URL"
        )
        st.session_state.config_changes['ARXIV_BASE_URL'] = base_url
        
        retries = st.number_input(
            "重试次数",
            min_value=1,
            max_value=10,
            value=int(st.session_state.config_changes.get('ARXIV_RETRIES', 3)),
            help="请求失败时的重试次数",
            key="arxiv_retries_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('ARXIV_RETRIES', str(retries))
        
        delay = st.number_input(
            "请求延迟（秒）",
            min_value=1,
            max_value=60,
            value=int(st.session_state.config_changes.get('ARXIV_DELAY', 5)),
            help="请求间隔延迟时间",
            key="arxiv_delay_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('ARXIV_DELAY', str(delay))
    
    with col2:
        categories = st.text_input(
            "论文分类",
            value=st.session_state.config_changes.get('ARXIV_CATEGORIES', 'cs.CL'),
            help="用逗号分隔的ArXiv分类，如：cs.CV,cs.LG,cs.AI",
            key="arxiv_categories_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('ARXIV_CATEGORIES', categories)
        
        max_entries = st.number_input(
            "每个分类最大条目数",
            min_value=1,
            max_value=50,
            value=int(st.session_state.config_changes.get('MAX_ENTRIES', 3)),
            help="每个分类最多获取的论文数量",
            key="max_entries_input"  # 添加唯一key确保状态跟踪
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('MAX_ENTRIES', str(max_entries))
        
        brief_papers = st.number_input(
            "简要分析论文数",
            min_value=1,
            max_value=15,
            value=int(st.session_state.config_changes.get('NUM_BRIEF_PAPERS', 7)),
            help="需要简要分析的论文数量（总推荐数 = 详细分析数 + 简要分析数）",
            key="brief_papers_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('NUM_BRIEF_PAPERS', str(brief_papers))
        
        detailed_papers = st.number_input(
            "详细分析论文数",
            min_value=1,
            max_value=10,
            value=int(st.session_state.config_changes.get('NUM_DETAILED_PAPERS', 3)),
            help="需要详细分析的论文数量",
            key="detailed_papers_input"
        )
        # 使用辅助函数跟踪配置更改
        track_config_change('NUM_DETAILED_PAPERS', str(detailed_papers))

def render_llm_config(config_manager):
    """渲染LLM配置"""
    st.subheader("🤖 LLM配置")
    
    # 主模型配置
    st.markdown("### 🚀 主模型参数配置")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        qwen_temperature = st.slider(
            "主模型温度参数",
            min_value=0.0,
            max_value=2.0,
            value=float(st.session_state.config_changes.get('QWEN_MODEL_TEMPERATURE', 0.7)),
            step=0.1,
            help="控制主模型生成文本的随机性，值越高越随机",
            key="qwen_temperature_slider"
        )
        track_config_change('QWEN_MODEL_TEMPERATURE', str(qwen_temperature))
    
    with col2:
        qwen_top_p = st.slider(
            "主模型Top-P参数",
            min_value=0.0,
            max_value=1.0,
            value=float(st.session_state.config_changes.get('QWEN_MODEL_TOP_P', 0.9)),
            step=0.05,
            help="控制主模型词汇选择的多样性，值越小越保守",
            key="qwen_top_p_slider"
        )
        track_config_change('QWEN_MODEL_TOP_P', str(qwen_top_p))
    
    with col3:
        qwen_max_tokens = st.number_input(
            "主模型最大Token数",
            min_value=500,
            max_value=8000,
            value=int(st.session_state.config_changes.get('QWEN_MODEL_MAX_TOKENS', 4000)),
            step=100,
            help="主模型单次生成的最大token数量",
            key="qwen_max_tokens_input"
        )
        track_config_change('QWEN_MODEL_MAX_TOKENS', str(qwen_max_tokens))
    
    # 轻量模型配置
    st.markdown("### ⚡ 轻量模型参数配置")
    
    # 获取当前选择的轻量模型提供商
    current_light_provider = st.session_state.config_changes.get('LIGHT_MODEL_PROVIDER', 'qwen')
    
    if current_light_provider == "qwen":
        st.markdown("**通义千问轻量模型参数**")
        col4, col5, col6 = st.columns(3)
        
        with col4:
            qwen_light_temperature = st.slider(
                "轻量模型温度参数",
                min_value=0.0,
                max_value=2.0,
                value=float(st.session_state.config_changes.get('QWEN_MODEL_LIGHT_TEMPERATURE', 0.5)),
                step=0.1,
                help="控制轻量模型生成文本的随机性，值越高越随机",
                key="qwen_light_temperature_slider"
            )
            track_config_change('QWEN_MODEL_LIGHT_TEMPERATURE', str(qwen_light_temperature))
        
        with col5:
            qwen_light_top_p = st.slider(
                "轻量模型Top-P参数",
                min_value=0.0,
                max_value=1.0,
                value=float(st.session_state.config_changes.get('QWEN_MODEL_LIGHT_TOP_P', 0.8)),
                step=0.05,
                help="控制轻量模型词汇选择的多样性，值越小越保守",
                key="qwen_light_top_p_slider"
            )
            track_config_change('QWEN_MODEL_LIGHT_TOP_P', str(qwen_light_top_p))
        
        with col6:
            qwen_light_max_tokens = st.number_input(
                "轻量模型最大Token数",
                min_value=500,
                max_value=4000,
                value=int(st.session_state.config_changes.get('QWEN_MODEL_LIGHT_MAX_TOKENS', 2000)),
                step=100,
                help="轻量模型单次生成的最大token数量",
                key="qwen_light_max_tokens_input"
            )
            track_config_change('QWEN_MODEL_LIGHT_MAX_TOKENS', str(qwen_light_max_tokens))
    
    else:  # ollama
        st.markdown("**OLLAMA本地模型参数**")
        col4, col5, col6 = st.columns(3)
        
        with col4:
            ollama_light_temperature = st.slider(
                "OLLAMA温度参数",
                min_value=0.0,
                max_value=2.0,
                value=float(st.session_state.config_changes.get('OLLAMA_MODEL_LIGHT_TEMPERATURE', 0.7)),
                step=0.1,
                help="控制OLLAMA模型生成文本的随机性，值越高越随机",
                key="ollama_light_temperature_slider"
            )
            track_config_change('OLLAMA_MODEL_LIGHT_TEMPERATURE', str(ollama_light_temperature))
        
        with col5:
            ollama_light_top_p = st.slider(
                "OLLAMA Top-P参数",
                min_value=0.0,
                max_value=1.0,
                value=float(st.session_state.config_changes.get('OLLAMA_MODEL_LIGHT_TOP_P', 0.9)),
                step=0.05,
                help="控制OLLAMA模型词汇选择的多样性，值越小越保守",
                key="ollama_light_top_p_slider"
            )
            track_config_change('OLLAMA_MODEL_LIGHT_TOP_P', str(ollama_light_top_p))
        
        with col6:
            ollama_light_max_tokens = st.number_input(
                "OLLAMA最大Token数",
                min_value=500,
                max_value=8000,
                value=int(st.session_state.config_changes.get('OLLAMA_MODEL_LIGHT_MAX_TOKENS', 2000)),
                step=100,
                help="OLLAMA模型单次生成的最大token数量",
                key="ollama_light_max_tokens_input"
            )
            track_config_change('OLLAMA_MODEL_LIGHT_MAX_TOKENS', str(ollama_light_max_tokens))
    
    # 通用配置
    st.markdown("### ⚙️ 通用配置")
    
    max_workers = st.number_input(
        "最大并发工作线程数",
        min_value=1,
        max_value=20,
        value=int(st.session_state.config_changes.get('MAX_WORKERS', 10)),
        help="并发处理的最大线程数",
        key="max_workers_input"
    )
    track_config_change('MAX_WORKERS', str(max_workers))

def render_file_config(config_manager):
    """渲染文件路径配置"""
    st.subheader("📁 文件路径配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        user_categories_file = st.text_input(
            "用户分类文件路径",
            value=st.session_state.config_changes.get('USER_CATEGORIES_FILE', 'data/users/user_categories.json'),
            help="用户研究兴趣分类文件的路径"
        )
        st.session_state.config_changes['USER_CATEGORIES_FILE'] = user_categories_file
        
        save_directory = st.text_input(
            "保存目录",
            value=st.session_state.config_changes.get('SAVE_DIRECTORY', './arxiv_history'),
            help="推荐结果保存的目录"
        )
        st.session_state.config_changes['SAVE_DIRECTORY'] = save_directory
    
    with col2:
        save_markdown = st.checkbox(
            "保存为Markdown格式",
            value=st.session_state.config_changes.get('SAVE_MARKDOWN', 'true').lower() == 'true',
            help="是否将结果保存为Markdown格式"
        )
        st.session_state.config_changes['SAVE_MARKDOWN'] = str(save_markdown).lower()

def render_email_config(config_manager):
    """渲染邮件配置"""
    st.subheader("📧 邮件发送配置")
    
    send_email = st.checkbox(
        "启用邮件发送",
        value=st.session_state.config_changes.get('SEND_EMAIL', 'false').lower() == 'true',
        help="是否启用邮件发送功能"
    )
    st.session_state.config_changes['SEND_EMAIL'] = str(send_email).lower()
    
    if send_email:
        col1, col2 = st.columns(2)
        
        with col1:
            sender_email = st.text_input(
                "发送者邮箱",
                value=st.session_state.config_changes.get('SENDER_EMAIL', ''),
                help="发送邮件的邮箱地址"
            )
            if sender_email and validate_email(sender_email):
                st.session_state.config_changes['SENDER_EMAIL'] = sender_email
            elif sender_email:
                st.error("请输入有效的邮箱地址")
            
            receiver_email = st.text_input(
                "接收者邮箱",
                value=st.session_state.config_changes.get('RECEIVER_EMAIL', ''),
                help="接收邮件的邮箱地址"
            )
            if receiver_email and validate_email(receiver_email):
                st.session_state.config_changes['RECEIVER_EMAIL'] = receiver_email
            elif receiver_email:
                st.error("请输入有效的邮箱地址")
            
            email_password = st.text_input(
                "邮箱密码",
                value=st.session_state.config_changes.get('EMAIL_PASSWORD', ''),
                type="password",
                help="邮箱密码或应用专用密码"
            )
            st.session_state.config_changes['EMAIL_PASSWORD'] = email_password
        
        with col2:
            smtp_server = st.text_input(
                "SMTP服务器",
                value=st.session_state.config_changes.get('SMTP_SERVER', 'smtp.qq.com'),
                help="SMTP服务器地址"
            )
            st.session_state.config_changes['SMTP_SERVER'] = smtp_server
            
            smtp_port = st.number_input(
                "SMTP端口",
                min_value=1,
                max_value=65535,
                value=int(st.session_state.config_changes.get('SMTP_PORT', 587)),
                help="SMTP服务器端口"
            )
            st.session_state.config_changes['SMTP_PORT'] = str(smtp_port)
            
            use_ssl = st.checkbox(
                "使用SSL",
                value=st.session_state.config_changes.get('USE_SSL', 'false').lower() == 'true',
                help="是否使用SSL加密"
            )
            st.session_state.config_changes['USE_SSL'] = str(use_ssl).lower()
            
            use_tls = st.checkbox(
                "使用TLS",
                value=st.session_state.config_changes.get('USE_TLS', 'true').lower() == 'true',
                help="是否使用TLS加密"
            )
            st.session_state.config_changes['USE_TLS'] = str(use_tls).lower()
            
            subject_prefix = st.text_input(
                "邮件主题前缀",
                value=st.session_state.config_changes.get('SUBJECT_PREFIX', '每日arXiv'),
                help="邮件主题的前缀"
            )
            st.session_state.config_changes['SUBJECT_PREFIX'] = subject_prefix

def render_timezone_config(config_manager):
    """渲染时区格式配置"""
    st.subheader("🕐 时区和格式配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        timezone_options = [
            "Asia/Shanghai",
            "UTC",
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo"
        ]
        
        current_timezone = st.session_state.config_changes.get('TIMEZONE', 'Asia/Shanghai')
        timezone = st.selectbox(
            "时区设置",
            options=timezone_options,
            index=timezone_options.index(current_timezone) if current_timezone in timezone_options else 0,
            help="选择时区"
        )
        st.session_state.config_changes['TIMEZONE'] = timezone
    
    with col2:
        date_format = st.text_input(
            "日期格式",
            value=st.session_state.config_changes.get('DATE_FORMAT', '%Y-%m-%d'),
            help="日期显示格式"
        )
        st.session_state.config_changes['DATE_FORMAT'] = date_format
        
        time_format = st.text_input(
            "时间格式",
            value=st.session_state.config_changes.get('TIME_FORMAT', '%H:%M:%S'),
            help="时间显示格式"
        )
        st.session_state.config_changes['TIME_FORMAT'] = time_format


def render_log_config(config_manager):
    """渲染日志配置"""
    st.subheader("📝 日志配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        current_level = st.session_state.config_changes.get('LOG_LEVEL', 'INFO')
        log_level = st.selectbox(
            "日志级别",
            options=log_levels,
            index=log_levels.index(current_level) if current_level in log_levels else 1,
            help="设置日志记录级别"
        )
        st.session_state.config_changes['LOG_LEVEL'] = log_level
        
        log_file = st.text_input(
            "日志文件路径",
            value=st.session_state.config_changes.get('LOG_FILE', 'logs/arxiv_recommender.log'),
            help="日志文件保存路径"
        )
        st.session_state.config_changes['LOG_FILE'] = log_file
        
        log_to_console = st.checkbox(
            "启用控制台日志",
            value=st.session_state.config_changes.get('LOG_TO_CONSOLE', 'true').lower() == 'true',
            help="是否在控制台显示日志"
        )
        st.session_state.config_changes['LOG_TO_CONSOLE'] = str(log_to_console).lower()
    
    with col2:
        log_max_size = st.number_input(
            "日志文件最大大小（MB）",
            min_value=1,
            max_value=100,
            value=int(st.session_state.config_changes.get('LOG_MAX_SIZE', 10)),
            help="单个日志文件的最大大小"
        )
        st.session_state.config_changes['LOG_MAX_SIZE'] = str(log_max_size)
        
        log_backup_count = st.number_input(
            "保留日志文件数量",
            min_value=1,
            max_value=20,
            value=int(st.session_state.config_changes.get('LOG_BACKUP_COUNT', 5)),
            help="保留的历史日志文件数量"
        )
        st.session_state.config_changes['LOG_BACKUP_COUNT'] = str(log_backup_count)


if __name__ == "__main__":
    main()
