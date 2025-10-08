#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 组件 - Streamlit 界面渲染组件
"""

import streamlit as st
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
import pytz


def render_header():
    """渲染页面头部"""
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


def render_user_config_section(user_profiles, service):
    """渲染用户配置区域
    
    Args:
        user_profiles: 用户配置列表
        service: ArXiv服务实例
        
    Returns:
        tuple: (selected_profile_name, selected_profile)
    """
    st.subheader("👤 用户配置")
    profile_names = [p['username'] for p in user_profiles]
    selected_profile_name = st.selectbox("选择一个用户配置:", ["自定义"] + profile_names)

    # 初始化selected_profile变量
    selected_profile = None
    
    # 根据选择更新研究兴趣和分类
    if selected_profile_name != "自定义":
        selected_profile = next((p for p in user_profiles if p['username'] == selected_profile_name), None)
        if selected_profile:
            # 更新服务中的研究兴趣
            interests = selected_profile.get('user_input', '').split('\n')
            service.update_research_interests(interests)
            
            # 更新配置中的分类
            config = service.get_config()
            if config:
                config['arxiv_categories'] = selected_profile.get('category_id', '').split(',')
            
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
    
    return selected_profile_name, selected_profile


def render_research_interests_section(service):
    """渲染研究兴趣输入区域
    
    Args:
        service: ArXiv服务实例
    """
    st.subheader("🎯 研究兴趣")
    current_interests = "\n".join(service.get_research_interests()) if service.get_research_interests() else ""
    research_interests_input = st.text_area(
        "请输入您的研究方向，描述即可：",
        value=current_interests,
        height=250,
        help="输入您的研究方向，系统将基于这些方向推荐相关论文"
    )
    
    # 更新研究兴趣
    if research_interests_input.strip():
        interests = [line.strip() for line in research_interests_input.split('\n') if line.strip()]
        service.update_research_interests(interests)
    
    st.markdown("---")


def render_recommendation_section(service, selected_profile_name):
    """渲染推荐系统运行区域
    
    Args:
        service: ArXiv服务实例
        selected_profile_name: 选择的用户配置名称
    """
    st.subheader("🚀 运行推荐系统")
    
    # 显示调试模式状态
    config = service.get_config()
    if config and config.get('debug_mode', False):
        st.warning("🔧 **调试模式已启用** - 系统将使用模拟数据，不会调用真实的ArXiv API和LLM服务")
    
    # 主按钮：智能推荐（默认功能）
    yesterday_str = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
    prev_str = (datetime.now().date() - timedelta(days=2)).strftime('%Y-%m-%d')
    
    if st.button(f"🔍 生成最新推荐报告（将优先查询：{yesterday_str}，若无则：{prev_str}）", 
                 type="primary", use_container_width=True, 
                 help="系统将自动查找最近可用的论文并生成推荐报告"):
        _handle_recommendation_run(service, selected_profile_name)
    
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
            _handle_recommendation_run(service, selected_profile_name, target_date_str)
    
    st.markdown("---")


def _handle_recommendation_run(service, selected_profile_name, specific_date=None):
    """处理推荐系统运行逻辑
    
    Args:
        service: ArXiv服务实例
        selected_profile_name: 选择的用户配置名称
        specific_date: 指定日期（可选）
    """
    research_interests = service.get_research_interests()
    config = service.get_config()
    
    if not research_interests:
        st.error("请先输入研究兴趣！")
    elif not config or not config.get('dashscope_api_key'):
        st.error("DashScope API Key 未配置，请检查 .env 文件！")
    else:
        # 创建实时日志显示区域
        st.subheader("📋 运行状态")
        
        # 初始化组件
        with st.spinner("正在初始化系统组件..."):
            success, message = service.initialize_components(selected_profile_name)
            if not success:
                st.error(f"❌ {message}")
                st.stop()
        
        # 运行推荐系统
        if specific_date:
            st.info(f"🚀 开始查询 {specific_date} 的论文...")
        else:
            st.info("🚀 开始运行推荐系统...")
            
        result = service.run_recommendation(specific_date)
        
        # 处理结果
        _display_recommendation_result(result, service, specific_date)


def _display_recommendation_result(result, service, specific_date=None):
    """显示推荐结果
    
    Args:
        result: 推荐结果
        service: ArXiv服务实例
        specific_date: 指定日期（可选）
    """
    if result['success']:
        # 检查是否有警告信息
        if 'warning' in result:
            st.warning(f"⚠️ {result['warning']}")
        else:
            # 根据是否为调试模式显示不同的成功消息
            if result.get('debug_mode', False):
                if specific_date:
                    st.success(f"🎉 调试模式：成功获取到 {specific_date} 的论文推荐！（使用模拟数据）")
                else:
                    st.success("🎉 调试模式推荐完成！（使用模拟数据）")
            else:
                if specific_date:
                    st.success(f"🎉 成功获取到 {specific_date} 的论文推荐！")
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
            st.info(f"📁 HTML报告已保存至: {result['html_filepath']}")
        else:
            st.info("📋 报告生成完成，但HTML文件未保存。请检查配置设置。")
        
        # 下载报告按钮
        _render_download_section(result, service, specific_date)
        
        # 显示保存信息
        if 'saved_path' in result:
            st.info(f"📁 报告已保存至: {result['saved_path']}")
    
    else:
        # 处理失败情况
        _display_error_result(result, specific_date)


def _render_download_section(result, service, specific_date=None):
    """渲染下载区域
    
    Args:
        result: 推荐结果
        service: ArXiv服务实例
        specific_date: 指定日期（可选）
    """
    st.subheader("💾 下载报告")
    
    config = service.get_config()
    research_interests = service.get_research_interests()
    
    # 生成下载内容
    download_content = f"""# ArXiv 论文推荐报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
查询日期: {result.get('target_date', specific_date or '')}

## 配置信息
- ArXiv 分类: {', '.join(config.get('arxiv_categories', []) if config else [])}
- 推荐论文数: {config.get('num_recommendations', 10) if config else 10}
- 详细分析数: {config.get('detailed_analysis_count', 3) if config else 3}
- 研究兴趣: {', '.join(research_interests)}

{result['report']}
"""
    
    st.download_button(
        label="📥 下载完整报告 (Markdown)",
        data=download_content,
        file_name=result.get('filename', 'arxiv_recommendations.md'),
        mime="text/markdown",
        use_container_width=True
    )


def _display_error_result(result, specific_date=None):
    """显示错误结果
    
    Args:
        result: 推荐结果
        specific_date: 指定日期（可选）
    """
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
    elif specific_date:
        # 特定日期查询失败的处理
        st.error(f"❌ 在 {specific_date} 未找到相关论文")
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
    else:
        st.error(f"❌ {result['error']}")
    
    if 'traceback' in result:
        with st.expander("查看详细错误信息"):
            st.code(result['traceback'])


def render_history_section(service):
    """渲染历史报告区域
    
    Args:
        service: ArXiv服务实例
    """
    st.subheader("📚 历史报告", anchor="history")
    
    recent_reports = service.get_recent_reports(10)
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