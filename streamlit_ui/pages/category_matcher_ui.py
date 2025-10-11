#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv分类匹配器 - Streamlit Web界面

基于category_matcher.py功能创建的用户友好界面，支持：
- 用户输入研究内容
- 实时匹配计算
- 结果可视化展示
- JSON数据管理

重构版本：采用模块化架构，完全分离UI组件和业务逻辑
不直接使用 Streamlit，所有 UI 操作都通过组件层封装
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入服务层和UI组件
from streamlit_ui.services.category_matcher_service import CategoryMatcherService
from streamlit_ui.ui_components.category_matcher_components import (
    # 页面配置和样式
    render_page_config,
    render_custom_css,
    render_header,
    render_sidebar_config,
    render_footer,
    
    # 输入和表单组件
    render_research_input_section,
    render_ai_optimize_section,
    render_matching_form,
    
    # 结果显示
    render_matching_success,
    render_results_section,
    render_token_usage_section,
    render_user_data_management_section,
    
    # 会话状态管理封装
    initialize_session_state,
    get_latest_results,
    set_latest_results,
    get_latest_matcher,
    set_latest_matcher,
    get_matching_status,
    set_matching_status,
    
    # 消息显示封装
    show_info,
    show_error,
    show_success,
    show_warning,
    
    # 进度控制封装
    create_progress_context
)


def handle_matching_process(service, username, user_input, top_n):
    """处理匹配流程"""
    # 添加调试日志，确认函数被调用
    
    # 验证用户输入
    if not username or not username.strip():
        show_error("❌ 请输入用户名")
        set_matching_status(False)
        return False
    
    if not user_input or not user_input.strip():
        show_error("❌ 请输入研究内容描述")
        set_matching_status(False)
        return False
    
    # 设置匹配状态
    set_matching_status(True)
    show_info("⏳ 正在初始化匹配器...")
    
    try:
        # 初始化匹配器
        matcher = service.initialize_matcher()
        if not matcher:
            show_error("❌ 匹配器初始化失败，请检查配置")
            set_matching_status(False)
            return False
        
        show_info("✅ 匹配器初始化成功")
        
        # 重置token计数器
        matcher.total_input_tokens = 0
        matcher.total_output_tokens = 0
        matcher.total_tokens = 0
        
        show_info(f"🚀 开始执行匹配 - Top {top_n} 结果")
        
        # 执行匹配
        results = service.execute_matching(user_input, username, top_n)
        
        show_info(f"📊 匹配完成，获得 {len(results) if results else 0} 个结果")
        
        if results:
            # 保存结果
            show_info("💾 正在保存匹配结果...")
            success = service.save_matching_results(username, user_input, results)
            
            if success:
                # 显示成功消息
                render_matching_success()
                
                # 存储结果到session state
                set_latest_results(results)
                set_latest_matcher(matcher)
                
                # 清除缓存
                service.clear_caches()
                
                show_info("✅ 匹配流程完成")
                return True
            else:
                show_error("❌ 保存结果失败")
                return False
        else:
            show_error("❌ 匹配失败，请重试")
            return False
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        show_error(f"❌ 匹配过程中出现错误: {str(e)}")
        show_error(f"详细错误信息: {error_details}")
        return False
    
    finally:
        # 重置匹配状态
        set_matching_status(False)
        show_info("🔄 匹配状态已重置")

def main():
    """主函数 - 组装UI界面"""
    # 渲染页面配置
    render_page_config()
    
    # 渲染自定义CSS
    render_custom_css()
    
    # 初始化会话状态
    initialize_session_state()
    
    # 获取服务实例
    service = CategoryMatcherService.get_service()
    
    # 渲染页面头部
    render_header()
    
    # 渲染侧边栏配置
    top_n = render_sidebar_config(service)
    
    # 渲染研究信息输入区域
    username, user_input = render_research_input_section(service)
    
    # 渲染AI优化描述区域
    render_ai_optimize_section(service, user_input)
    
    # 渲染匹配表单
    submitted = render_matching_form()
    
    # 处理匹配请求
    if submitted:
        # 验证输入
        if not username.strip():
            show_error("❌ 请输入用户名")
        elif not user_input.strip():
            show_error("❌ 请输入研究内容描述")
        else:
            # 开始匹配处理
            with create_progress_context("🔄 正在处理匹配请求..."):
                result = handle_matching_process(service, username, user_input, top_n)
                
                if result:
                    show_success("✅ 匹配处理完成！")
                else:
                    show_error("❌ 匹配处理失败，请查看终端日志")
    
    # 渲染结果展示区域
    render_results_section(get_latest_results(), service)
    
    # 渲染Token使用统计区域
    render_token_usage_section(service)
    
    # 渲染用户数据管理区域
    render_user_data_management_section(service)
    
    # 渲染页脚
    render_footer()

if __name__ == "__main__":
    main()