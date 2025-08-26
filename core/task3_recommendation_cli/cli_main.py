#!/usr/bin/env python3
"""ArXiv 每日论文推荐系统 - CLI主程序入口

整合了原main.py的功能，使用新的模块化架构。
提供命令行接口，整合论文推荐、邮件发送和报告生成流程。
"""

import os
import sys
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from loguru import logger
from dotenv import load_dotenv

# 脚本移动到子目录后，需要重新计算项目根目录
# 我们假定此脚本位于根目录下的某个文件夹中，例如 task3
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# 加载位于项目根目录的 .env 文件
dotenv_path = project_root / '.env'
load_dotenv(str(dotenv_path), override=True)
os.chdir(project_root)

from core.recommendation_engine import RecommendationEngine
from core.arxiv_fetcher import ArxivFetcher
from core.llm_provider import LLMProvider
from ..utils.template_renderer import TemplateRenderer
from ..utils.mcp_time_service import MCPTimeService
from ..utils.mcp_time_service import get_current_time
from core.output_manager import OutputManager
import re


class ArxivRecommenderCLI:
    """ArXiv推荐系统CLI主类。"""
    
    def __init__(self, username=None):
        """初始化CLI应用。
        
        Args:
            username: 指定用户名，如果为None则使用第一个用户的配置
        """
        logger.info("ArXiv推荐系统初始化开始")
        
        # 初始化组件
        self.username = username  # 存储用户名
        self.arxiv_fetcher = None
        self.llm_provider = None
        self.recommendation_engine = None
        self.output_manager = None
        
        # 配置参数
        logger.debug("加载系统配置")
        self.config = self._load_config()
        # 加载用户分类标签，更新配置
        self._load_user_categories()
        logger.success(f"系统配置加载完成 - 简要分析论文数: {self.config['num_brief_papers']}, 详细分析: {self.config['num_detailed_papers']}, 分类标签: {self.config['arxiv_categories']}")
        
    def _load_config(self) -> Dict[str, Any]:
        """从环境变量加载配置。
        
        Returns:
            配置字典
        """
        config = {
            # API配置
            'dashscope_api_key': os.getenv('DASHSCOPE_API_KEY', ''),
            'dashscope_base_url': os.getenv('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            'qwen_model': os.getenv('QWEN_MODEL', 'qwen-plus'),
            
            # ArXiv获取器配置
            'arxiv_base_url': os.getenv('ARXIV_BASE_URL', 'http://export.arxiv.org/api/query'),
            'arxiv_retries': int(os.getenv('ARXIV_RETRIES', '3')),
            'arxiv_delay': int(os.getenv('ARXIV_DELAY', '5')),
            'arxiv_categories': os.getenv('ARXIV_CATEGORIES', 'cs.CV,cs.LG').split(','),
            'max_entries': int(os.getenv('MAX_ENTRIES', '50')),
            'num_brief_papers': int(os.getenv('NUM_BRIEF_PAPERS', '7')),
            'num_detailed_papers': int(os.getenv('NUM_DETAILED_PAPERS', '3')),
            
            # LLM配置
            'temperature': float(os.getenv('TEMPERATURE', '0.7')),
            'max_workers': int(os.getenv('MAX_WORKERS', '5')),
            
            # 文件路径配置
            'user_categories_file': os.getenv('USER_CATEGORIES_FILE', 'data/users/user_categories.json'),
            'save_directory': os.getenv('SAVE_DIRECTORY', 'arxiv_history'),
            'save_markdown': os.getenv('SAVE_MARKDOWN', 'true').lower() == 'true',
            
            # 邮件配置
            'send_email': os.getenv('SEND_EMAIL', 'false').lower() == 'true',
            'sender_email': os.getenv('SENDER_EMAIL', ''),
            'receiver_email': os.getenv('RECEIVER_EMAIL', ''),
            'email_password': os.getenv('EMAIL_PASSWORD', ''),
            'smtp_server': os.getenv('SMTP_SERVER', ''),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'use_ssl': os.getenv('USE_SSL', 'false').lower() == 'true',
            'use_tls': os.getenv('USE_TLS', 'true').lower() == 'true',
            'subject_prefix': os.getenv('SUBJECT_PREFIX', '每日arXiv'),
            
            # 时区和格式配置
            'timezone': os.getenv('TIMEZONE', 'Asia/Shanghai'),
            'date_format': os.getenv('DATE_FORMAT', '%Y-%m-%d'),
            'time_format': os.getenv('TIME_FORMAT', '%H:%M:%S'),
            
            # 日志配置
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_file': os.getenv('LOG_FILE', 'logs/arxiv_recommender.log'),
            'log_to_console': os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true',
            'log_max_size': int(os.getenv('LOG_MAX_SIZE', '10')),
            'log_backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
        }
        
        return config
    
    def _get_current_username(self) -> str:
        """获取当前用户名。
        
        Returns:
            用户名字符串，如果没有找到则返回默认值"TEST"
        """
        if self.username:
            return self.username
        
        # 从用户配置文件中获取用户名
        categories_file = self.config['user_categories_file']
        try:
            if os.path.exists(categories_file):
                with open(categories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list) and len(data) > 0:
                    first_user = data[0]
                    if isinstance(first_user, dict) and 'username' in first_user:
                        return first_user['username']
        except Exception as e:
            logger.warning(f"获取用户名失败: {e}")
        
        return "TEST"  # 默认用户名
    
    def _load_user_categories(self):
        """从用户分类JSON文件加载分类标签，更新配置。"""
        categories_file = self.config['user_categories_file']
        logger.debug(f"尝试加载用户分类文件: {categories_file}")
        
        try:
            if os.path.exists(categories_file):
                with open(categories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查数据格式
                if isinstance(data, list) and len(data) > 0:
                    target_user = None
                    
                    # 根据username查找对应用户，如果没有指定则使用第一个用户
                    if self.username:
                        # 查找指定用户名的配置
                        for user in data:
                            if isinstance(user, dict) and user.get('username') == self.username:
                                target_user = user
                                logger.debug(f"找到指定用户配置: {self.username}")
                                break
                        
                        if not target_user:
                            logger.warning(f"未找到用户 {self.username} 的配置，使用第一个用户配置")
                            target_user = data[0] if isinstance(data[0], dict) else None
                    else:
                        # 没有指定用户名，使用第一个用户
                        target_user = data[0] if isinstance(data[0], dict) else None
                        logger.debug("未指定用户名，使用第一个用户配置")
                    
                    if target_user and isinstance(target_user, dict):
                        # 处理category_id字段，更新arxiv_categories配置
                        if 'category_id' in target_user and target_user['category_id']:
                            category_str = target_user['category_id'].strip()
                            if category_str:
                                # 解析多个分类标签
                                categories = [cat.strip() for cat in category_str.split(',') if cat.strip()]
                                if categories:
                                    self.config['arxiv_categories'] = categories
                                    username_info = f"用户 {target_user.get('username', '未知')}" if target_user.get('username') else "第一个用户"
                                    logger.success(f"从JSON文件加载{username_info}的分类标签: {categories}")
                                    return
                                else:
                                    logger.warning(f"category_id字段为空或格式不正确: {category_str}")
                            else:
                                logger.warning("category_id字段为空字符串")
                        else:
                            logger.debug("JSON文件中未找到category_id字段，使用环境变量配置")
                    else:
                        logger.warning(f"目标用户数据格式不正确: {categories_file}")
                else:
                    logger.warning(f"JSON文件为空或格式不正确: {categories_file}")
            else:
                logger.warning(f"用户分类文件不存在: {categories_file}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON文件解析失败: {e}，使用环境变量配置")
        except Exception as e:
            logger.error(f"用户分类文件读取失败: {e}，使用环境变量配置")
        
        # 如果没有成功加载，保持环境变量配置
        logger.debug(f"使用环境变量分类标签: {self.config['arxiv_categories']}")
    
    def _initialize_components(self):
        """初始化所有组件。"""
        logger.info("系统组件初始化开始")
        try:
            # 初始化ArXiv获取器
            logger.debug("初始化ArXiv获取器")
            self.arxiv_fetcher = ArxivFetcher(
                base_url=self.config['arxiv_base_url'],
                retries=self.config['arxiv_retries'],
                delay=self.config['arxiv_delay']
            )
            logger.debug(f"ArXiv获取器初始化完成 - URL: {self.config['arxiv_base_url']}, 重试: {self.config['arxiv_retries']}, 延迟: {self.config['arxiv_delay']}s")
            
            # 初始化LLM提供商
            logger.debug(f"初始化LLM提供商 - 模型: {self.config['qwen_model']}")
            self.llm_provider = LLMProvider(
                model=self.config['qwen_model'],
                base_url=self.config['dashscope_base_url'],
                api_key=self.config['dashscope_api_key']
            )
            logger.debug("LLM提供商初始化完成")
            
            # 初始化推荐引擎
            logger.debug("初始化推荐引擎")
            research_interests = self._load_research_interests()
            
            # 获取用户名，如果没有指定则从用户配置中获取
            username = self._get_current_username()
            
            self.recommendation_engine = RecommendationEngine(
                categories=self.config['arxiv_categories'],
                max_entries=self.config['max_entries'],
                num_brief_papers=self.config['num_brief_papers'],
                num_detailed_papers=self.config['num_detailed_papers'],
                model=self.config['qwen_model'],
                base_url=self.config['dashscope_base_url'],
                api_key=self.config['dashscope_api_key'],
                description=research_interests,
                username=username,
                num_workers=self.config['max_workers'],
                temperature=self.config['temperature']
            )
            logger.debug(f"推荐引擎初始化完成 - 类别: {self.config['arxiv_categories']}, 工作线程: {self.config['max_workers']}")
            
            # 初始化输出管理器
            logger.debug("初始化输出管理器")
            template_dir = project_root / 'templates'
            self.output_manager = OutputManager(str(template_dir))
            logger.debug("输出管理器初始化完成")
            
            logger.success("系统组件初始化完成")
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    def _load_research_interests(self) -> str:
        """从用户分类JSON文件加载研究兴趣。
        
        Returns:
            研究兴趣文本
        """
        categories_file = self.config['user_categories_file']
        logger.debug(f"尝试加载研究兴趣文件: {categories_file}")
        
        try:
            if os.path.exists(categories_file):
                with open(categories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查数据格式
                if isinstance(data, list) and len(data) > 0:
                    target_user = None
                    
                    # 根据username查找对应用户，如果没有指定则使用第一个用户
                    if self.username:
                        # 查找指定用户名的配置
                        for user in data:
                            if isinstance(user, dict) and user.get('username') == self.username:
                                target_user = user
                                logger.debug(f"找到指定用户的研究兴趣: {self.username}")
                                break
                        
                        if not target_user:
                            logger.warning(f"未找到用户 {self.username} 的研究兴趣，使用第一个用户配置")
                            target_user = data[0] if isinstance(data[0], dict) else None
                    else:
                        # 没有指定用户名，使用第一个用户
                        target_user = data[0] if isinstance(data[0], dict) else None
                        logger.debug("未指定用户名，使用第一个用户的研究兴趣")
                    
                    if target_user and isinstance(target_user, dict):
                        # 处理user_input字段
                        if 'user_input' in target_user and target_user['user_input']:
                            interests = target_user['user_input']
                            username_info = f"用户 {target_user.get('username', '未知')}" if target_user.get('username') else "第一个用户"
                            logger.success(f"从JSON文件加载{username_info}的研究兴趣: {categories_file}")
                            return interests
                        else:
                            logger.warning(f"目标用户缺少user_input字段: {categories_file}")
                    else:
                        logger.warning(f"目标用户数据格式不正确: {categories_file}")
                else:
                    logger.warning(f"JSON文件为空或格式不正确: {categories_file}")
            else:
                logger.warning(f"用户分类文件不存在: {categories_file}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON文件解析失败: {e}，使用默认配置")
        except Exception as e:
            logger.error(f"用户分类文件读取失败: {e}，使用默认配置")
        
        # 回退到默认配置
        logger.info("使用默认研究兴趣配置")
        return "机器学习、深度学习、计算机视觉、自然语言处理"
    
    def _get_current_time(self) -> str:
        """获取当前时间。
        
        Returns:
            格式化的当前时间字符串
        """
        logger.debug("获取当前时间")
        try:
            # 尝试通过LLM工具获取时间
            current_time = get_current_time()
            if current_time:
                logger.debug(f"LLM时间服务获取成功: {current_time}")
                return current_time
        except Exception as e:
            logger.warning(f"LLM时间服务失败，回退到本地时间: {e}")
        
        # 回退到本地时间
        local_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.debug(f"使用本地时间: {local_time}")
        return local_time
    
    def _send_email_if_configured(self, html_content: str):
        """如果配置了邮件，则发送邮件。
        
        Args:
            html_content: 预处理的HTML内容
        """
        logger.debug("检查邮件发送配置")
        # 首先检查是否启用邮件发送
        if not self.config['send_email']:
            logger.debug("邮件发送已禁用")
            return
            
        if not all([
            self.config['sender_email'],
            self.config['receiver_email'],
            self.config['email_password'],
            self.config['smtp_server']
        ]):
            logger.warning("邮件配置不完整，跳过发送")
            return
        
        # 如果没有HTML内容，跳过发送
        if not html_content:
            logger.warning("HTML内容为空，跳过邮件发送")
            return
        
        logger.info(f"邮件发送开始 - 发送方: {self.config['sender_email']}, 接收方: {self.config['receiver_email']}")
        
        try:
            self.output_manager.send_email(
                sender=self.config['sender_email'],
                receiver=self.config['receiver_email'],
                password=self.config['email_password'],
                smtp_server=self.config['smtp_server'],
                smtp_port=self.config['smtp_port'],
                html_content=html_content,
                subject_prefix=self.config['subject_prefix'],
                use_ssl=self.config['use_ssl'],
                use_tls=self.config['use_tls']
            )
            logger.success("邮件发送成功")
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            logger.warning("邮件发送失败，但报告已成功生成并保存到本地")
            # 不重新抛出异常，让程序继续运行
    
    def _sanitize_username(self, username: str) -> str:
        """将用户名转换为安全的文件名片段"""
        return re.sub(r'[\\/:*?"<>|\s]+', '_', username.strip()) if username else "USER"
    
    def _save_markdown_if_configured(self, markdown_content: str, current_time: str, target_date: str = None):
        """如果配置了保存Markdown，则保存报告。
        
        Args:
            markdown_content: Markdown内容
            current_time: 当前时间
            target_date: 查询目标日期（用于文件命名）
        """
        if not self.config['save_markdown']:
            logger.debug("Markdown保存已禁用")
            return
        
        logger.debug("Markdown报告保存开始")
        try:
            # 生成文件名
            date_str = target_date if target_date else datetime.datetime.now().strftime("%Y-%m-%d")
            username = self._get_current_username()
            safe_username = self._sanitize_username(username)
            filename = f"{date_str}_{safe_username}_ARXIV_summary.md"
            logger.debug(f"生成文件名: {filename}")
            
            # 保存文件
            filepath = self.output_manager.save_markdown_report(
                content=markdown_content,
                save_dir=self.config['save_directory'],
                filename=filename,
                username=username,
                target_date=target_date,
            )
            
            if not filepath:
                logger.error("Markdown报告保存失败")
                
        except Exception as e:
            logger.error(f"Markdown报告保存异常: {e}")
    
    def _save_html_report_if_configured(self, markdown_content: str, current_time: str, target_date: str = None):
        """如果配置了保存Markdown，则同时保存HTML格式的研究报告。
        
        Args:
            markdown_content: Markdown内容
            save_dir: 保存目录
            current_time: 当前时间
            target_date: 查询目标日期（用于文件命名与展示）
        """
        if not self.config['save_markdown']:
            logger.debug("HTML报告保存已禁用")
            return
        
        try:
            # 生成文件名
            date_str = target_date if target_date else datetime.datetime.now().strftime("%Y-%m-%d")
            username = self._get_current_username()
            safe_username = self._sanitize_username(username)
            filename = f"{date_str}_{safe_username}_ARXIV_summary.html"
            
            # 保存HTML文件
            filepath = self.output_manager.save_markdown_report_as_html(
                markdown_content=markdown_content,
                save_dir=self.config['save_directory'],
                current_time=current_time,
                username=username,
                filename=filename,
                target_date=target_date,
            )
            
            if not filepath:
                logger.error("HTML报告保存失败")
                
        except Exception as e:
            logger.error(f"HTML报告保存异常: {e}")
            return None
    
    def _save_html_report_if_configured_separated(self, summary_content: str, detailed_analysis: str, brief_analysis: str, current_time: str, papers: list = None, target_date: str = None):
        """如果配置了保存Markdown，则保存分离内容的HTML格式研究报告。
        
        Args:
            summary_content: 总结内容
            detailed_analysis: 详细分析内容
            brief_analysis: 简要分析内容
            current_time: 当前时间
            papers: 论文数据列表，用于生成统计信息
            target_date: 查询目标日期（用于文件命名与展示）
            
        Returns:
            tuple: (HTML文件路径, HTML内容字符串)，如果未配置保存或失败则返回(None, None)
        """
        if not self.config['save_markdown']:
            logger.debug("HTML报告保存已禁用")
            return None, None
        
        logger.debug("HTML报告生成开始")
        try:
            # 生成文件名
            date_str = target_date if target_date else datetime.datetime.now().strftime("%Y-%m-%d")
            username = self._get_current_username()
            safe_username = self._sanitize_username(username)
            filename = f"{date_str}_{safe_username}_ARXIV_summary.html"
            logger.debug(f"生成HTML文件名: {filename}")
            
            # 保存HTML文件，传递分离的内容
            filepath, html_content = self.output_manager.save_markdown_report_as_html_separated(
                summary_content=summary_content,
                detailed_analysis=detailed_analysis,
                brief_analysis=brief_analysis,
                save_dir=self.config['save_directory'],
                current_time=current_time,
                username=username,
                filename=filename,
                papers=papers,
                target_date=target_date,
            )
            
            if filepath:
                return filepath, html_content
            else:
                logger.error("HTML报告保存失败")
                return None, None
                
        except Exception as e:
            logger.error(f"HTML报告保存异常: {e}")
            return None, None
    
    def get_recommendations(self, specific_date=None):
        """获取推荐结果，适用于Streamlit调用。
        
        Args:
            specific_date: 指定日期，格式为YYYY-MM-DD，如果为None则使用智能回溯逻辑
        
        Returns:
            dict: 包含推荐结果的字典，格式为:
            {
                'success': bool,  # 是否成功获取推荐
                'data': dict,     # 推荐数据（如果成功）
                'error': str,     # 错误信息（如果失败）
                'current_time': str,  # 当前时间
                'target_date': str    # 目标日期
            }
        """
        logger.info("ArXiv每日论文推荐系统启动")
        try:
            # 初始化组件
            self._initialize_components()
            
            # 获取当前时间
            current_time = self._get_current_time()
            
            # 加载研究兴趣
            research_interests = self._load_research_interests()
            
            # 根据是否指定日期选择不同的逻辑
            report_result = None
            target_date_str = None
            
            if specific_date:
                # 指定日期模式：直接查询指定日期
                target_date_str = specific_date
                logger.info(f"论文获取日期: {target_date_str} (用户指定日期)")
                
                # 执行推荐流程
                logger.info("论文推荐流程开始")
                report_result = self.recommendation_engine.run(current_time, target_date_str)
                
                if report_result:
                    logger.success(f"在{target_date_str}找到了论文")
                else:
                    logger.warning(f"在{target_date_str}未找到相关论文")
            else:
                # 智能回溯模式：尝试获取昨天和前天的论文
                for days_back in [1, 2]:  # 先尝试昨天，再尝试前天
                    target_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
                    target_date_str = target_date.strftime('%Y-%m-%d')
                    logger.info(f"论文获取日期: {target_date_str} (往前{days_back}天)")
                    
                    # 执行推荐流程
                    logger.info("论文推荐流程开始")
                    report_result = self.recommendation_engine.run(current_time, target_date_str)
                    
                    if report_result:
                        logger.success(f"在{target_date_str}找到了论文")
                        break
                    else:
                        logger.warning(f"在{target_date_str}未找到相关论文")
            
            if report_result:
                logger.success("论文推荐流程完成")
                return {
                    'success': True,
                    'data': report_result,
                    'error': None,
                    'current_time': current_time,
                    'target_date': target_date_str
                }
            else:
                logger.warning("在目标日期范围内未找到相关论文")
                # 根据模式确定错误信息
                if specific_date:
                    error_msg = f"在指定日期 {target_date_str} 未找到相关论文"
                else:
                    # 智能回溯模式的错误信息
                    final_target_date_str = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
                    error_msg = f"在目标日期 {final_target_date_str} 未找到相关论文"
                    target_date_str = final_target_date_str
                
                return {
                    'success': False,
                    'data': None,
                    'error': error_msg,
                    'current_time': current_time,
                    'target_date': target_date_str
                }
            
        except Exception as e:
            logger.error(f"系统运行异常: {e}")
            return {
                'success': False,
                'data': None,
                'error': str(e),
                'current_time': None,
                'target_date': None
            }
    
    def save_reports(self, report_result: dict, current_time: str, target_date: str = None):
        """保存报告文件，适用于Streamlit调用。
        
        Args:
            report_result: 推荐结果数据
            current_time: 当前时间
            target_date: 查询目标日期
            
        Returns:
            dict: 保存结果，格式为:
            {
                'markdown_saved': bool,
                'html_saved': bool,
                'html_content': str,
                'email_sent': bool
            }
        """
        try:
            # 获取分离的内容
            summary_content = report_result['summary']
            detailed_analysis = report_result['detailed_analysis']
            brief_analysis = report_result.get('brief_analysis', '')  # 获取简要分析内容
            papers = report_result.get('papers', [])  # 获取papers数据用于统计
            # 为向后兼容，合并内容用于Markdown保存
            markdown_content = summary_content + detailed_analysis + brief_analysis
            logger.debug("报告内容生成完成")
            
            logger.info("报告保存和发送开始")
            # 保存为Markdown
            self._save_markdown_if_configured(markdown_content, current_time, target_date)
            # 保存为HTML研究报告，传递分离的内容和papers数据
            html_filepath, html_content = self._save_html_report_if_configured_separated(summary_content, detailed_analysis, brief_analysis, current_time, papers, target_date)
            # 发送邮件，使用生成的HTML内容
            self._send_email_if_configured(html_content)
            
            return {
                'markdown_saved': self.config['save_markdown'],
                'html_saved': html_content is not None,
                'html_content': html_content,
                'html_filepath': html_filepath,
                'email_sent': self.config['send_email']
            }
        except Exception as e:
            logger.error(f"报告保存异常: {e}")
            return {
                'markdown_saved': False,
                'html_saved': False,
                'html_content': None,
                'email_sent': False
            }

    def run(self):
        """运行推荐系统主流程。"""
        logger.info("ArXiv每日论文推荐系统启动")
        try:
            # 获取推荐结果
            result = self.get_recommendations()
            
            if result['success']:
                # 保存报告
                save_result = self.save_reports(result['data'], result['current_time'], target_date=result['target_date'])
                logger.success("ArXiv每日论文推荐系统运行完成")
            else:
                logger.error(result['error'])
                sys.exit(0)  # 正常退出，因为这不是错误情况
            
        except Exception as e:
            logger.error(f"系统运行异常: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主程序入口。"""
    try:
        # 加载环境变量以获取日志配置
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'), override=True)
        
        # 配置日志
        logger.remove()  # 移除默认处理器
        
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_to_console = os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true'
        log_file = os.getenv('LOG_FILE', 'logs/arxiv_recommender.log')
        
        # 控制台日志
        if log_to_console:
            logger.add(
                sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level=log_level
            )
        
        # 文件日志
        if log_file:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            log_max_size = int(os.getenv('LOG_MAX_SIZE', '10')) * 1024 * 1024  # 转换为字节
            log_backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))
            
            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=log_level,
                rotation=log_max_size,
                retention=log_backup_count,
                encoding="utf-8"
            )
        
        # 创建并运行CLI应用
        cli_app = ArxivRecommenderCLI()
        cli_app.run()
        
    except KeyboardInterrupt:
        logger.warning("用户中断程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()