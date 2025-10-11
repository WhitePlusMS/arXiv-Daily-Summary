#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv 推荐服务 - FastAPI重构版本
移除Streamlit依赖，添加控制台日志记录
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import traceback
from typing import List, Dict, Any, Optional, Tuple

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'), override=True)

# 导入核心模块
from core.arxiv_cli import ArxivRecommenderCLI
from core.output_manager import OutputManager
from .base_service import BaseService, ServiceResponse


class ArxivRecommenderService(BaseService):
    """ArXiv 推荐系统业务逻辑服务类 - FastAPI版本"""
    
    def __init__(self):
        super().__init__("ArxivRecommenderService")
        self.config = None
        self.research_interests = []
        self.user_profiles = []
        self.cli_app = None  # CLI应用实例
        self.output_manager = None  # 用于配置显示
        self.log_messages = []  # 存储日志消息
        
        self.log_info("ArxivRecommenderService 初始化完成")
    
    async def load_config(self) -> ServiceResponse:
        """加载配置（通过CLI模块）"""
        self.log_info("开始加载配置")
        try:
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            self.config = self.cli_app.get_config()
            self.log_info("配置加载成功", config_keys=list(self.config.keys()) if self.config else [])
            return self.success_response(self.config, "配置加载成功")
        except Exception as e:
            self.log_error("配置加载失败", e)
            return self.error_response(f"配置加载失败: {str(e)}")
    
    async def load_research_interests(self) -> ServiceResponse:
        """加载研究兴趣（通过CLI模块）"""
        self.log_info("开始加载研究兴趣")
        try:
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            success = self.cli_app.load_research_interests_from_file()
            if success:
                self.research_interests = self.cli_app.get_research_interests()
                self.log_info("研究兴趣加载成功", count=len(self.research_interests))
                return self.success_response(self.research_interests, "研究兴趣加载成功")
            else:
                self.research_interests = []
                self.log_info("研究兴趣文件不存在或为空，使用空列表")
                return self.success_response([], "研究兴趣加载成功（空列表）")
        except Exception as e:
            self.log_error("研究兴趣加载失败", e)
            return self.error_response(f"研究兴趣加载失败: {str(e)}")

    async def load_user_profiles(self) -> ServiceResponse:
        """加载用户配置（通过CLI模块）"""
        self.log_info("开始加载用户配置")
        try:
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            success = self.cli_app.load_user_profiles()
            if success:
                self.user_profiles = self.cli_app.get_user_profiles()
                self.log_info("用户配置加载成功", count=len(self.user_profiles))
                return self.success_response(self.user_profiles, "用户配置加载成功")
            else:
                self.user_profiles = []
                self.log_info("用户配置文件不存在或为空，使用空列表")
                return self.success_response([], "用户配置加载成功（空列表）")
        except Exception as e:
            self.log_error("用户配置加载失败", e)
            return self.error_response(f"用户配置加载失败: {str(e)}")
    
    async def initialize_components(self, selected_username: Optional[str] = None) -> ServiceResponse:
        """初始化系统组件（通过CLI模块）
        
        Args:
            selected_username: 选择的用户名，如果为None或"自定义"则不传入用户名
        """
        self.log_info("开始初始化系统组件", username=selected_username)
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
            
            self.log_info("系统组件初始化成功")
            return self.success_response({"username": username}, "系统组件初始化成功")
        except Exception as e:
            self.log_error("组件初始化失败", e)
            return self.error_response(f"组件初始化失败: {str(e)}")
    
    async def setup_realtime_logging(self) -> ServiceResponse:
        """设置实时日志显示"""
        self.log_info("开始设置实时日志")
        try:
            # 创建日志容器
            self.log_messages = []
            
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            # 调用CLI模块的日志设置方法
            log_handler = self.cli_app.setup_realtime_logging()
            
            self.log_info("实时日志设置成功")
            return self.success_response({"handler": str(log_handler)}, "实时日志设置成功")
            
        except Exception as e:
            self.log_error("实时日志设置失败", e)
            return self.error_response(f"实时日志设置失败: {str(e)}")
    
    async def _run_debug_mode(self, profile_name: str) -> Dict[str, Any]:
        """调试模式：通过CLI模块运行"""
        self.log_info("开始运行调试模式", profile_name=profile_name)
        try:
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            # 调用CLI模块的调试模式
            success, result_data, error_msg = self.cli_app.run_debug_mode(None)
            
            if success:
                self.log_info("调试模式运行成功", target_date=result_data['target_date'])
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
                self.log_error("调试模式运行失败", error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'debug_mode': True
                }
                
        except Exception as e:
            self.log_error("调试模式运行异常", e)
            return {
                'success': False,
                'error': f"调试模式运行失败: {str(e)}",
                'debug_mode': True
            }
    
    async def run_recommendation(self, profile_name: str, debug_mode: bool = False) -> ServiceResponse:
        """运行推荐系统（调用CLI核心逻辑）
        
        Args:
            profile_name: 用户配置名称
            debug_mode: 是否启用调试模式
        """
        self.log_info("开始运行推荐系统", profile_name=profile_name, debug_mode=debug_mode)
        try:
            # 检查是否启用调试模式
            if debug_mode:
                self.log_info("使用调试模式运行")
                result = await self._run_debug_mode(profile_name)
                return self.success_response(result) if result['success'] else self.error_response(result['error'], result)
            
            if self.cli_app is None:
                self.cli_app = ArxivRecommenderCLI()
            
            # 调用CLI的完整推荐流程
            success, result_data, error_msg = self.cli_app.run_full_recommendation(None)
            
            if success:
                self.log_info("推荐系统运行成功", target_date=result_data['target_date'])
                result = {
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
                return self.success_response(result, "推荐系统运行成功")
            else:
                # 检查是否是"未找到论文"的特定情况
                no_papers_found_messages = ["未找到相关论文", "在目标日期范围内未找到相关论文"]
                is_no_papers_error = any(msg in error_msg for msg in no_papers_found_messages)

                if is_no_papers_error:
                    target_date_str = result_data.get('target_date', '最近') if result_data else '最近'
                    self.log_info("未找到论文", target_date=target_date_str)
                    
                    # 检查是否为连续两天未找到论文的情况
                    if "在目标日期" in error_msg and "未找到相关论文" in error_msg:
                        result = {
                            'success': False,
                            'error': error_msg,
                            'warning': f"在 {target_date_str} 未找到论文",
                            'show_weekend_tip': True
                        }
                    else:
                        result = {
                            'success': False,
                            'error': error_msg,
                            'warning': f"在 {target_date_str} 未找到论文"
                        }
                    return self.error_response(error_msg, result)
                else:
                    self.log_error("推荐系统运行失败", error_msg)
                    return self.error_response(error_msg)
                    
        except Exception as e:
            self.log_error("推荐系统运行异常", e)
            result = {
                'success': False, 
                'error': f"推荐系统运行失败: {str(e)}",
                'traceback': traceback.format_exc()
            }
            return self.error_response(f"推荐系统运行失败: {str(e)}", result)
    
    async def get_recent_reports(self, limit: int = 10) -> ServiceResponse:
        """获取最近的报告文件"""
        self.log_info("开始获取最近的报告文件", limit=limit)
        try:
            cli_app = ArxivRecommenderCLI()
            reports = cli_app.get_recent_reports(limit)
            self.log_info("获取报告文件成功", count=len(reports))
            return self.success_response(reports, f"获取到 {len(reports)} 个报告文件")
        except Exception as e:
            self.log_error("获取报告文件失败", e)
            return self.error_response(f"获取报告文件失败: {str(e)}", [])
    
    async def update_research_interests(self, interests: List[str]) -> ServiceResponse:
        """更新研究兴趣"""
        self.log_info("开始更新研究兴趣", count=len(interests))
        try:
            self.research_interests = interests
            if self.cli_app:
                self.cli_app.update_research_interests(interests)
            self.log_info("研究兴趣更新成功")
            return self.success_response(interests, "研究兴趣更新成功")
        except Exception as e:
            self.log_error("研究兴趣更新失败", e)
            return self.error_response(f"研究兴趣更新失败: {str(e)}")
    
    async def get_config(self) -> ServiceResponse:
        """获取配置"""
        self.log_info("获取配置信息")
        return self.success_response(self.config, "获取配置成功")
    
    async def get_research_interests(self) -> ServiceResponse:
        """获取研究兴趣"""
        self.log_info("获取研究兴趣", count=len(self.research_interests))
        return self.success_response(self.research_interests, "获取研究兴趣成功")
    
    async def get_user_profiles(self) -> ServiceResponse:
        """获取用户配置"""
        self.log_info("获取用户配置", count=len(self.user_profiles))
        return self.success_response(self.user_profiles, "获取用户配置成功")
    
    async def initialize_service(self) -> ServiceResponse:
        """初始化服务并加载所有配置"""
        self.log_info("开始初始化完整服务")
        try:
            # 加载配置
            config_result = await self.load_config()
            if not config_result.success:
                return config_result
            
            # 加载研究兴趣
            interests_result = await self.load_research_interests()
            if not interests_result.success:
                return interests_result
            
            # 加载用户配置
            profiles_result = await self.load_user_profiles()
            if not profiles_result.success:
                return profiles_result
            
            self.log_info("完整服务初始化成功")
            return self.success_response({
                "config": self.config,
                "research_interests": self.research_interests,
                "user_profiles": self.user_profiles
            }, "服务初始化成功")
            
        except Exception as e:
            self.log_error("服务初始化失败", e)
            return self.error_response(f"服务初始化失败: {str(e)}")