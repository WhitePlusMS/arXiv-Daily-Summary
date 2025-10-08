#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv 每日论文推荐系统 - Streamlit Web 应用
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import traceback
import json
import webbrowser
import logging
from io import StringIO
import pytz
import streamlit.components.v1 as components
import base64

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'), override=True)

# 导入CLI模块
from core.arxiv_cli import ArxivRecommenderCLI
# 导入核心模块（用于配置显示）
from core.output_manager import OutputManager

class StreamlitArxivRecommender:
    """Streamlit ArXiv 推荐系统应用类"""
    
    def __init__(self):
        self.config = None
        self.research_interests = []
        self.user_profiles = []
        self.cli_app = None  # CLI应用实例
        self.output_manager = None  # 用于配置显示
        self.log_container = None  # 实时日志显示容器
        self.log_messages = []  # 存储日志消息
        
    def load_config(self):
        """加载配置（通过CLI模块）"""
        try:
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            self.config = self.cli_app.get_config()
            st.success("✅ 配置加载成功")
            return True
        except Exception as e:
            st.error(f"❌ 配置加载失败: {str(e)}")
            return False
    
    def load_research_interests(self):
        """加载研究兴趣（通过CLI模块）"""
        try:
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            success = self.cli_app.load_research_interests_from_file()
            if success:
                self.research_interests = self.cli_app.get_research_interests()
            else:
                self.research_interests = []
            return success
        except Exception as e:
            st.error(f"研究兴趣加载失败: {str(e)}")
            return False

    def load_user_profiles(self):
        """加载用户配置（通过CLI模块）"""
        try:
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            success = self.cli_app.load_user_profiles()
            if success:
                self.user_profiles = self.cli_app.get_user_profiles()
            else:
                self.user_profiles = []
            return success
        except Exception as e:
            st.error(f"用户配置加载失败: {str(e)}")
            return False
    
    def initialize_components(self, selected_username=None):
        """初始化系统组件（通过CLI模块）
        
        Args:
            selected_username: 选择的用户名，如果为None或"自定义"则不传入用户名
        """
        try:
            # 初始化CLI应用实例，传入用户名（如果不是自定义的话）
            username = selected_username if selected_username and selected_username != "自定义" else None
            self.cli_app = ArxivRecommenderCLI(username=username)
            
            # 更新CLI应用的研究兴趣
            self.cli_app.update_research_interests(self.research_interests)
            
            # 设置实时日志
            self.cli_app.setup_realtime_logging()
            
            # 初始化输出管理器（用于配置显示）
            template_dir = project_root / 'templates'
            self.output_manager = OutputManager(str(template_dir))
            
            st.success("✅ 系统组件初始化成功")
            return True
        except Exception as e:
            st.error(f"❌ 组件初始化失败: {str(e)}")
            return False
    
    def setup_realtime_logging(self):
        """设置实时日志显示"""
        try:
            # 创建日志容器
            self.log_container = st.empty()
            self.log_messages = []
            
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            # 调用CLI模块的日志设置方法
            log_handler = self.cli_app.setup_realtime_logging()
            
            return log_handler
            
        except Exception as e:
            st.error(f"日志设置失败: {str(e)}")
            return None
    
    def _run_debug_mode(self, specific_date=None):
        """调试模式：通过CLI模块运行"""
        try:
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            # 调用CLI模块的调试模式
            success, result_data, error_msg = self.cli_app.run_debug_mode(specific_date)
            
            if success:
                return {
                    'success': True,
                    'report': result_data['summary'],
                    'summary_content': result_data['summary'],
                    'detailed_analysis': result_data['detailed_analysis'],
                    'brief_analysis': result_data['brief_analysis'],
                    'html_content': None,  # CLI模块生成HTML文件
                    'html_filepath': result_data.get('html_file'),
                    'filename': f"arxiv_recommendation_{result_data['target_date']}_debug.md",
                    'target_date': result_data['target_date'],
                    'debug_mode': True
                }
            else:
                return {
                    'success': False,
                    'error': error_msg,
                    'debug_mode': True
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"调试模式运行失败: {str(e)}",
                'debug_mode': True
            }
    
    def run_recommendation(self, specific_date=None):
        """运行推荐系统（调用CLI核心逻辑）
        
        Args:
            specific_date: 指定日期，格式为YYYY-MM-DD，如果为None则使用智能回溯逻辑
        """
        try:
            # 检查是否启用调试模式
            if self.config.get('debug_mode', False):
                return self._run_debug_mode(specific_date)
            
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            # 调用CLI的完整推荐流程
            success, result_data, error_msg = self.cli_app.run_full_recommendation(specific_date)
            
            if success:
                return {
                    'success': True,
                    'report': result_data['markdown_content'],
                    'summary_content': result_data['summary_content'],
                    'detailed_analysis': result_data['detailed_analysis'],
                    'brief_analysis': result_data['brief_analysis'],
                    'html_content': result_data.get('html_content'),
                    'html_filepath': result_data.get('html_filepath'),
                    'filename': result_data['filename'],
                    'target_date': result_data['target_date']
                }
            else:
                # 检查是否是"未找到论文"的特定情况
                no_papers_found_messages = ["未找到相关论文", "在目标日期范围内未找到相关论文"]
                is_no_papers_error = any(msg in error_msg for msg in no_papers_found_messages)

                if is_no_papers_error:
                    target_date_str = result_data.get('target_date', '最近') if result_data else '最近'
                    
                    # 检查是否为连续两天未找到论文的情况
                    if "在目标日期" in error_msg and "未找到相关论文" in error_msg:
                        return {
                            'success': False,
                            'error': error_msg,
                            'warning': f"在 {target_date_str} 未找到论文",
                            'show_weekend_tip': True
                        }
                    else:
                        return {
                            'success': False,
                            'error': error_msg,
                            'warning': f"在 {target_date_str} 未找到论文"
                        }
                else:
                    return {
                        'success': False,
                        'error': error_msg
                    }
                    
        except Exception as e:
            return {
                'success': False, 
                'error': f"推荐系统运行失败: {str(e)}",
                'traceback': traceback.format_exc()
            }



def get_recent_reports(limit=10):
    """获取最近的报告文件"""
    try:
        cli_app = ArxivRecommenderCLI()
        return cli_app.get_recent_reports(limit)
    except Exception:
        return []

def main():
    """Streamlit 应用主函数"""
    # 设置页面配置
    st.set_page_config(
        page_title="ArXiv 每日论文推荐",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 应用标题和说明
    st.title("📚 ArXiv 每日论文推荐系统")
    
    # 显示当前时区时间和ArXiv时区时间
    local_tz = datetime.now().astimezone().tzinfo
    arxiv_tz = pytz.timezone('US/Eastern')
    
    current_time = datetime.now()
    local_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
    arxiv_time = current_time.astimezone(arxiv_tz)
    arxiv_time_str = arxiv_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # 判断是否为夏令时
    is_dst = arxiv_time.dst().total_seconds() != 0
    tz_abbr = 'EDT' if is_dst else 'EST'
    
    st.caption(f"当前时间: {local_time_str} ({local_tz}) | ArXiv时间: {arxiv_time_str} ({tz_abbr})")
    
    st.markdown("---")
    
    # 初始化应用
    if 'app' not in st.session_state:
        st.session_state.app = StreamlitArxivRecommender()
    
    app = st.session_state.app
    
    # 加载配置和研究兴趣
    if not app.config or st.session_state.get('force_reload_config', False):
        with st.spinner("正在加载配置..."):
            if not app.load_config():
                st.stop()
            if not app.load_research_interests():
                st.stop()
            if not app.load_user_profiles():
                st.stop()
            st.session_state.force_reload_config = False

    # 显示调试模式状态
    if app.config.get('debug_mode', False):
        st.warning("🔧 **调试模式已启用** - 系统将使用模拟数据，不会调用真实的ArXiv API和LLM服务")

    # 用户选择
    st.subheader("👤 用户配置")
    profile_names = [p['username'] for p in app.user_profiles]
    selected_profile_name = st.selectbox("选择一个用户配置:", ["自定义"] + profile_names)

    # 初始化selected_profile变量
    selected_profile = None
    
    # 根据选择更新研究兴趣和分类
    if selected_profile_name != "自定义":
        selected_profile = next((p for p in app.user_profiles if p['username'] == selected_profile_name), None)
        if selected_profile:
            app.research_interests = selected_profile.get('user_input', '').split('\n')
            app.config['arxiv_categories'] = selected_profile.get('category_id', '').split(',')
            
            # 显示完整的用户配置信息
            user_categories_file = project_root / "data" / "users" / "user_categories.json"
            
            # 查找用户在JSON文件中的行号
            line_number = 1
            try:
                with open(user_categories_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines, 1):
                        if f'"username": "{selected_profile_name}"' in line:
                            line_number = i
                            break
            except Exception:
                line_number = 1
            
            # 显示详细配置信息
            st.success(
                f"✅ **已加载用户 {selected_profile_name} 的配置**\n\n"
                f"**分类标签**: `{selected_profile.get('category_id', '未设置')}`\n\n"
                f"**研究兴趣**:\n```\n{selected_profile.get('user_input', '未设置')}\n```\n\n"
            )

    st.markdown("---")

    # 分类标签显示
    if selected_profile and selected_profile.get('category_id'):
        st.subheader("🏷️ 分类标签")
        st.info(f"`{selected_profile.get('category_id', '').replace(',', ' ')}`")
    
    # 研究兴趣输入
    st.subheader("🎯 研究兴趣")
    current_interests = "\n".join(app.research_interests) if app.research_interests else ""
    research_interests_input = st.text_area(
        "请输入您的研究方向，描述即可：",
        value=current_interests,
        height=250,
        help="输入您的研究方向，系统将基于这些方向推荐相关论文"
    )
    
    # 更新研究兴趣
    if research_interests_input.strip():
        app.research_interests = [line.strip() for line in research_interests_input.split('\n') if line.strip()]
    
    st.markdown("---")
    
    # 运行推荐系统按钮
    st.subheader("🚀 运行推荐系统")
    
    # 主按钮：智能推荐（默认功能）
    yesterday_str = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
    prev_str = (datetime.now().date() - timedelta(days=2)).strftime('%Y-%m-%d')
    if st.button(f"🔍 生成最新推荐报告（将优先查询：{yesterday_str}，若无则：{prev_str}）", type="primary", use_container_width=True, help="系统将自动查找最近可用的论文并生成推荐报告"):
        if not app.research_interests:
            st.error("请先输入研究兴趣！")
        elif not app.config.get('dashscope_api_key'):
            st.error("DashScope API Key 未配置，请检查 .env 文件！")
        else:
            # 创建实时日志显示区域
            st.subheader("📋 运行状态")
            
            # 初始化组件
            with st.spinner("正在初始化系统组件..."):
                if not app.initialize_components(selected_profile_name):
                    st.stop()
            
            # 运行推荐系统（带实时日志显示）
            st.info("🚀 开始运行推荐系统...")
            result = app.run_recommendation()
            
            # 处理结果的代码保持不变...
            if result['success']:
                # 检查是否有警告信息
                if 'warning' in result:
                    st.warning(f"⚠️ {result['warning']}")
                else:
                    # 根据是否为调试模式显示不同的成功消息
                    if result.get('debug_mode', False):
                        st.success("🎉 调试模式推荐完成！（使用模拟数据）")
                    else:
                        st.success("🎉 推荐完成！")
                    st.balloons()
                
                # 显示报告结果
                if result.get('debug_mode', False):
                    st.subheader("📊 推荐结果 (调试模式)")
                    st.info("💡 以下内容为调试模式生成的模拟数据，仅用于测试系统功能")
                else:
                    st.subheader("📊 推荐结果")
                
                # 检查是否有HTML报告文件
                if result.get('html_filepath'):
                    # 显示报告路径信息
                    st.info(f"📁 HTML报告已保存至: {result['html_filepath']}")
                else:
                    # 如果没有HTML文件，显示简要信息
                    st.info("📋 报告生成完成，但HTML文件未保存。请检查配置设置。")
                
                # 下载报告按钮
                st.subheader("💾 下载报告")
                
                # 生成下载内容
                download_content = f"""# ArXiv 论文推荐报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
查询日期: {result.get('target_date', '')}

## 配置信息
- ArXiv 分类: {', '.join(app.config.get('arxiv_categories', []))}
- 推荐论文数: {app.config.get('num_recommendations', 10)}
- 详细分析数: {app.config.get('detailed_analysis_count', 3)}
- 研究兴趣: {', '.join(app.research_interests)}

{result['report']}
"""
                
                st.download_button(
                    label="📥 下载完整报告 (Markdown)",
                    data=download_content,
                    file_name=result.get('filename', 'arxiv_recommendations.md'),
                    mime="text/markdown",
                    use_container_width=True
                )
                
                # 显示保存信息
                if 'saved_path' in result:
                    st.info(f"📁 报告已保存至: {result['saved_path']}")
            
            else:
                # 检查是否需要显示周末提示
                if result.get('show_weekend_tip', False):
                    st.warning(
                        f"📅 **连续两天未找到论文**\n\n"
                        f"系统已尝试获取最近两天的论文但均未找到。这可能是因为：\n\n"
                        f"**ArXiv发布时间表：**\n"
                        f"• 📅 周日至周四：正常发布论文（美国东部时间20:00）\n"
                        f"• 🚫 周五和周六：不发布新论文\n\n"
                        f"**可能的原因：**\n"
                        f"• 当前为周末期间，ArXiv不发布新论文\n"
                        f"• 美国联邦假日导致发布延迟\n"
                        f"• 您选择的分类在这两天没有新提交\n\n"
                        f"💡 **建议：**\n"
                        f"• 尝试选择更多的ArXiv分类\n"
                        f"• 等待下个工作日的论文发布\n"
                        f"• 检查ArXiv官方状态页面"
                    )
                else:
                    st.error(f"❌ {result['error']}")
                
                if 'traceback' in result:
                    with st.expander("查看详细错误信息"):
                        st.code(result['traceback'])
    
    # 高级功能：查询特定日期（折叠选项）
    with st.expander("🔧 高级选项：查询特定日期的报告", expanded=False):
        st.markdown(
            "💡 **提示：** 如果您需要查看特定日期的论文推荐，可以在这里指定日期。\n\n"
            "⚠️ **注意：** ArXiv通常在周日至周四发布论文，周五和周六不发布新论文。"
        )
        
        # 日期选择器
        selected_date = st.date_input(
            "选择查询日期",
            value=datetime.now().date() - timedelta(days=1),  # 默认选择昨天
            max_value=datetime.now().date(),  # 不能选择未来日期
            help="选择您想要查询论文的日期"
        )
        
        # 规范化目标日期字符串（用于展示和查询）
        target_date_str = selected_date.strftime('%Y-%m-%d')
        
        # 查询特定日期按钮
        if st.button(f"🔍 查询指定日期（{target_date_str}）", use_container_width=True):
                if not app.research_interests:
                    st.error("请先输入研究兴趣！")
                elif not app.config.get('dashscope_api_key'):
                    st.error("DashScope API Key 未配置，请检查 .env 文件！")
                else:
                    # 创建实时日志显示区域
                    st.subheader("📋 运行状态")
                    
                    # 初始化组件
                    with st.spinner("正在初始化系统组件..."):
                        if not app.initialize_components(selected_profile_name):
                            st.stop()
                    
                    # 运行推荐系统（指定日期）
                    st.info(f"🚀 开始查询 {target_date_str} 的论文...")
                    result = app.run_recommendation(specific_date=target_date_str)
                    
                    # 处理特定日期查询的结果
                    if result['success']:
                        # 根据是否为调试模式显示不同的成功消息
                        if result.get('debug_mode', False):
                            st.success(f"🎉 调试模式：成功获取到 {target_date_str} 的论文推荐！（使用模拟数据）")
                        else:
                            st.success(f"🎉 成功获取到 {target_date_str} 的论文推荐！")
                        st.balloons()
                        
                        # 显示报告结果
                        if result.get('debug_mode', False):
                            st.subheader("📊 推荐结果 (调试模式)")
                            st.info("💡 以下内容为调试模式生成的模拟数据，仅用于测试系统功能")
                        else:
                            st.subheader("📊 推荐结果")
                        
                        # 检查是否有HTML报告文件
                        if result.get('html_filepath'):
                            # 显示报告路径信息
                            st.info(f"📁 HTML报告已保存至: {result['html_filepath']}")
                        else:
                            # 如果没有HTML文件，显示简要信息
                            st.info("📋 报告生成完成，但HTML文件未保存。请检查配置设置。")
                        
                        # 下载报告按钮
                        st.subheader("💾 下载报告")
                        
                        # 生成下载内容
                        download_content = f"""# ArXiv 论文推荐报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
查询日期: {target_date_str}

## 配置信息
- ArXiv 分类: {', '.join(app.config.get('arxiv_categories', []))}
- 推荐论文数: {app.config.get('num_recommendations', 10)}
- 详细分析数: {app.config.get('detailed_analysis_count', 3)}
- 研究兴趣: {', '.join(app.research_interests)}

{result['report']}
"""
                        
                        st.download_button(
                            label="📥 下载完整报告 (Markdown)",
                            data=download_content,
                            file_name=result.get('filename', 'arxiv_recommendations.md'),
                            mime="text/markdown",
                            use_container_width=True
                        )
                        
                        # 显示保存信息
                        if 'saved_path' in result:
                            st.info(f"📁 报告已保存至: {result['saved_path']}")
                    
                    else:
                        # 特定日期查询失败的处理
                        st.error(f"❌ 在 {target_date_str} 未找到相关论文")
                        st.info(
                            f"💡 **可能的原因：**\n\n"
                            f"• 该日期为周末（ArXiv周五和周六不发布新论文）\n"
                            f"• 该日期为美国联邦假日\n"
                            f"• 您选择的分类在该日期没有新提交\n\n"
                            f"**建议：**\n"
                            f"• 尝试选择其他日期\n"
                            f"• 尝试选择更多的ArXiv分类\n"
                            f"• 查看ArXiv官方发布时间表"
                        )
                        
                        if 'traceback' in result:
                            with st.expander("查看详细错误信息"):
                                st.code(result['traceback'])

    
    st.markdown("---")
    
    # 历史报告区域
    st.subheader("📚 历史报告", anchor="history")
    
    def display_history_reports():
        """显示历史报告，包含下载、删除、预览功能"""
        recent_reports = get_recent_reports(10)
        if not recent_reports:
            st.info("暂无历史报告")
            return
        
        st.write(f"最近 {len(recent_reports)} 个报告：")
        
        # 使用容器宽度占满整个区域
        with st.container():
            # 显示历史报告列表
            for report in recent_reports:
                report_name = report['name']
                
                # 获取对应的HTML文件路径
                html_path = report['path'].parent / f"{report_name.replace('.md', '.html')}"
                
                # 创建报告卡片
                col1, col2, col3, col4, col5 = st.columns([5, 1, 1, 1, 1])
                    
                with col1:
                    st.write(f"📄 {report_name}")
                
                with col2:
                    # 下载Markdown按钮
                    try:
                        with open(report['path'], 'r', encoding='utf-8') as f:
                            md_content = f.read()
                        st.download_button(
                        label="📄 MD",
                        data=md_content,
                        file_name=report_name,
                        mime="text/markdown",
                        key=f"download_md_{report_name}",
                        help="下载Markdown格式报告",
                        use_container_width=True
                    )
                    except Exception as e:
                        st.error("❌")
                
                with col3:
                    # 下载HTML按钮（如果存在）
                    if html_path.exists():
                        try:
                            with open(html_path, 'r', encoding='utf-8') as f:
                                html_content = f.read()
                            st.download_button(
                            label="🌐 HTML",
                            data=html_content,
                            file_name=html_path.name,
                            mime="text/html",
                            key=f"download_html_{report_name}",
                            help="下载HTML格式报告",
                            use_container_width=True
                        )
                        except Exception as e:
                            st.error("❌")
                    else:
                        st.button("🌐 HTML", key=f"no_html_{report_name}", disabled=True, help="HTML文件不存在")
                
                with col4:
                    # 预览按钮
                    preview_key = f"preview_{report_name}"
                    if html_path.exists():
                        if st.button("👁️ 预览", key=preview_key, help="在新标签页中打开HTML报告", use_container_width=True):
                            try:
                                # 使用绝对路径并在新标签页打开
                                webbrowser.open(f"file://{html_path.resolve()}", new=2)
                            except Exception as e:
                                st.error(f"打开失败: {str(e)}")
                    else:
                        st.button("👁️ 预览", key=f"no_preview_{report_name}", disabled=True, help="无预览")
                
                with col5:
                    # 删除按钮
                    delete_key = f"delete_{report_name}"
                    if st.button("🗑️ 删除", key=delete_key, help="删除该报告文件", use_container_width=True):
                        try:
                            # 删除Markdown文件
                            report['path'].unlink()
                            
                            # 删除对应的HTML文件（如果存在）
                            if html_path.exists():
                                html_path.unlink()
                            
                            st.success(f"已删除报告: {report_name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"删除失败: {str(e)}")
                
                st.markdown("---")
        

    
    # 调用显示函数
    display_history_reports()
    
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

if __name__ == "__main__":
    main()