#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv 推荐服务 - 业务逻辑层
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import traceback
import streamlit as st

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'), override=True)

# 导入核心模块
from core.arxiv_cli import ArxivRecommenderCLI
from core.output_manager import OutputManager


class ArxivRecommenderService:
    """ArXiv 推荐系统业务逻辑服务类"""
    
    def __init__(self):
        self.config = None
        self.research_interests = []
        self.user_profiles = []
        self.cli_app = None  # CLI应用实例
        self.output_manager = None  # 用于配置显示
        self.log_container = None  # 实时日志显示容器
        self.log_messages = []  # 存储日志消息
    
    @staticmethod
    def get_service():
        """获取或创建ArXiv服务实例（原SessionManager功能）"""
        if 'arxiv_service' not in st.session_state:
            st.session_state.arxiv_service = ArxivRecommenderService()
        return st.session_state.arxiv_service
    
    @staticmethod
    def initialize_service():
        """初始化服务并加载配置（原SessionManager功能）"""
        service = ArxivRecommenderService.get_service()
        
        # 检查是否需要重新加载配置
        if not service.config or st.session_state.get('force_reload_config', False):
            # 加载配置
            success, message = service.load_config()
            if not success:
                st.error(f"❌ {message}")
                st.stop()
                return
            
            # 加载研究兴趣
            success, message = service.load_research_interests()
            if not success:
                st.error(f"❌ {message}")
                st.stop()
                return
            
            # 加载用户配置
            success, message = service.load_user_profiles()
            if not success:
                st.error(f"❌ {message}")
                st.stop()
                return
            
            # 重置强制重新加载标志
            st.session_state.force_reload_config = False
            
            st.success("✅ 配置加载成功")
    
    @staticmethod
    def force_reload_config():
        """强制重新加载配置（原SessionManager功能）"""
        st.session_state.force_reload_config = True
        if 'arxiv_service' in st.session_state:
            del st.session_state.arxiv_service
        
    def load_config(self):
        """加载配置（通过CLI模块）"""
        try:
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            self.config = self.cli_app.get_config()
            return True, "配置加载成功"
        except Exception as e:
            return False, f"配置加载失败: {str(e)}"
    
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
            return success, "研究兴趣加载成功" if success else "研究兴趣加载失败"
        except Exception as e:
            return False, f"研究兴趣加载失败: {str(e)}"

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
            return success, "用户配置加载成功" if success else "用户配置加载失败"
        except Exception as e:
            return False, f"用户配置加载失败: {str(e)}"
    
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
            
            return True, "系统组件初始化成功"
        except Exception as e:
            return False, f"组件初始化失败: {str(e)}"
    
    def setup_realtime_logging(self):
        """设置实时日志显示"""
        try:
            # 创建日志容器
            self.log_messages = []
            
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            # 调用CLI模块的日志设置方法
            log_handler = self.cli_app.setup_realtime_logging()
            
            return log_handler
            
        except Exception as e:
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
    
    def get_recent_reports(self, limit=10):
        """获取最近的报告文件"""
        try:
            cli_app = ArxivRecommenderCLI()
            return cli_app.get_recent_reports(limit)
        except Exception:
            return []
    
    def update_research_interests(self, interests):
        """更新研究兴趣"""
        self.research_interests = interests
        if self.cli_app:
            self.cli_app.update_research_interests(interests)
    
    def get_config(self):
        """获取配置"""
        return self.config
    
    def get_research_interests(self):
        """获取研究兴趣"""
        return self.research_interests
    
    def get_user_profiles(self):
        """获取用户配置"""
        return self.user_profiles