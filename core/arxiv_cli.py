#!/usr/bin/env python3
"""ArXiv 每日论文推荐系统 - CLI主程序入口

整合了原main.py的功能，使用新的模块化架构。
提供命令行接口，整合论文推荐、邮件发送和报告生成流程。
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from datetime import datetime, timedelta
from core.arxiv_fetcher import ArxivFetcher
from core.llm_provider import LLMProvider
from core.recommendation_engine import RecommendationEngine
from core.output_manager import OutputManager
from core.common_utils import format_timezone_date, get_timezone_aware_now
from core.debug_recommendation_data import run_debug_recommendation
from core.env_config import get_str, get_int, get_bool, get_float
from core.logging_config import setup_cli_logging
from core.report_workflow import ReportWorkflow
from core.user_config_loader import (
    get_username_from_config,
    load_selected_user_config,
    parse_research_interests,
    parse_user_categories,
)
from core.progress_utils import ProgressTracker

# 项目根目录路径（用于文件读取）
project_root = Path(__file__).parent.parent


class RecommendationWorkflow(ProgressTracker):
    """ArXiv推荐系统核心工作流。"""
    
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
        
        # 初始化数据存储
        self.research_interests = []
        self.user_profiles = []
        
        # 进度跟踪
        self.task_id = None  # 当前任务ID（用于进度更新）
        
        # 配置参数
        logger.debug("加载系统配置")
        self.config = self._load_config()
        # 加载用户分类标签，更新配置
        self._load_user_categories()
        logger.success(f"系统配置加载完成 - 简要分析论文数: {self.config['num_brief_papers']}, 详细分析: {self.config['num_detailed_papers']}, 分类标签: {self.config['arxiv_categories']}")
        
        # 记录系统启动时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"系统启动时间: {current_time}")
        
    def _load_config(self) -> Dict[str, Any]:
        """从集中化 env 配置模块加载配置。
        
        Returns:
            配置字典
        """
        # 重新加载 .env 文件，确保获取最新配置
        from core.env_config import reload
        reload()
        
        config = {
            # API配置
            'dashscope_api_key': get_str('DASHSCOPE_API_KEY', ''),
            'dashscope_base_url': get_str('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            'qwen_model': get_str('QWEN_MODEL', 'qwen-plus'),

            # 提供方与模型映射（前端需要感知）
            'heavy_model_provider': get_str('HEAVY_MODEL_PROVIDER', 'dashscope'),
            'light_model_provider': get_str('LIGHT_MODEL_PROVIDER', get_str('HEAVY_MODEL_PROVIDER', 'dashscope')),
            'qwen_model_light': get_str('QWEN_MODEL_LIGHT', ''),
            
            # ArXiv获取器配置
            'arxiv_base_url': get_str('ARXIV_BASE_URL', 'http://export.arxiv.org/api/query'),
            'arxiv_retries': get_int('ARXIV_RETRIES', 3),
            'arxiv_delay': get_int('ARXIV_DELAY', 5),
            # arxiv_categories 现在从用户配置文件中的 category_id 字段读取，不再从环境变量读取
            # 如果用户配置文件中没有 category_id，则使用默认值
            'arxiv_categories': ['cs.CV', 'cs.LG'],  # 默认值，会被 _load_user_categories() 覆盖
            'max_entries': get_int('MAX_ENTRIES', 50),
            'num_brief_papers': get_int('NUM_BRIEF_PAPERS', 7),
            'num_detailed_papers': get_int('NUM_DETAILED_PAPERS', 3),
            # 相关性过滤阈值（用于剔除低分项）
            'relevance_filter_threshold': get_int('RELEVANCE_FILTER_THRESHOLD', 6),
            
            # LLM配置

            'qwen_model_temperature': get_float('QWEN_MODEL_TEMPERATURE', 0.7),
            'qwen_model_top_p': get_float('QWEN_MODEL_TOP_P', 0.9),
            'qwen_model_max_tokens': get_int('QWEN_MODEL_MAX_TOKENS', 4000),
            'qwen_model_light_temperature': get_float('QWEN_MODEL_LIGHT_TEMPERATURE', 0.5),
            'qwen_model_light_top_p': get_float('QWEN_MODEL_LIGHT_TOP_P', 0.8),
            'qwen_model_light_max_tokens': get_int('QWEN_MODEL_LIGHT_MAX_TOKENS', 2000),
            'max_workers': get_int('MAX_WORKERS', 5),
            
            # 文件路径配置（硬编码）
            'user_categories_file': str(project_root / 'data' / 'users' / 'user_categories.json'),
            'save_directory': str(project_root / 'arxiv_history'),
            'save_markdown': get_bool('SAVE_MARKDOWN', True),
            
            # 邮件配置
            'send_email': get_bool('SEND_EMAIL', False),
            'sender_email': get_str('SENDER_EMAIL', ''),
            'receiver_email': get_str('RECEIVER_EMAIL', ''),
            'email_password': get_str('EMAIL_PASSWORD', ''),
            'smtp_server': get_str('SMTP_SERVER', ''),
            'smtp_port': get_int('SMTP_PORT', 587),
            'use_ssl': get_bool('USE_SSL', False),
            'use_tls': get_bool('USE_TLS', True),
            'subject_prefix': get_str('SUBJECT_PREFIX', '每日arXiv'),
            
            # 时区配置
            'timezone': get_str('TIMEZONE', 'Asia/Shanghai'),
            
            # 日志配置（简化：只保留用户可配置的3项）
            'log_level': 'DEBUG',  # 固定为DEBUG，不再可配置
            'log_file': 'logs/arxiv_recommender.log',  # 固定路径，不再可配置
            'log_to_console': get_bool('LOG_TO_CONSOLE', True),
            'log_max_size': get_int('LOG_MAX_SIZE', 10),
            'log_backup_count': get_int('LOG_BACKUP_COUNT', 5),
        }
        
        return config
    
    def _get_current_username(self) -> str:
        """获取当前用户名。
        
        Returns:
            用户名字符串，如果没有找到则返回默认值"TEST"
        """
        if self.username:
            return self.username
        
        return get_username_from_config(self.config['user_categories_file'], self.username)
    
    def _load_user_categories(self):
        """从用户分类JSON文件加载分类标签，更新配置。"""
        categories_file = self.config['user_categories_file']
        logger.debug(f"尝试加载用户分类文件: {categories_file}")
        
        target_user = load_selected_user_config(categories_file, self.username)
        categories = parse_user_categories(target_user)
        if categories:
            self.config['arxiv_categories'] = categories
            username_info = f"用户 {target_user.get('username', '未知')}" if target_user and target_user.get('username') else "第一个用户"
            logger.success(f"从JSON文件加载{username_info}的分类标签: {categories}")
            return

        logger.debug(f"使用环境变量分类标签: {self.config['arxiv_categories']}")
    
    def load_research_interests_from_file(self):
        """从文件加载研究兴趣（用于Streamlit界面）
        
        Returns:
            bool: 加载是否成功
        """
        try:
            interests_file = project_root / "research_interests.md"
            if interests_file.exists():
                with open(interests_file, 'r', encoding='utf-8') as f:
                    self.research_interests = [line.strip() for line in f if line.strip()]
                logger.success(f"从文件加载研究兴趣: {len(self.research_interests)} 条")
            else:
                logger.warning("研究兴趣文件不存在，使用空列表")
                self.research_interests = []
            return True
        except Exception as e:
            logger.error(f"研究兴趣加载失败: {str(e)}")
            self.research_interests = []
            return False
    
    def load_user_profiles(self):
        """加载用户配置（用于Streamlit界面）
        
        Returns:
            bool: 加载是否成功
        """
        try:
            user_profiles_file = project_root / "data" / "users" / "user_categories.json"
            if user_profiles_file.exists():
                with open(user_profiles_file, 'r', encoding='utf-8') as f:
                    self.user_profiles = json.load(f)
                logger.success(f"加载用户配置: {len(self.user_profiles)} 个用户")
            else:
                logger.warning("用户配置文件不存在，使用空列表")
                self.user_profiles = []
            return True
        except Exception as e:
            logger.error(f"用户配置加载失败: {str(e)}")
            self.user_profiles = []
            return False
    
    def get_config(self):
        """获取当前配置（用于Streamlit界面）
        
        Returns:
            dict: 当前配置字典
        """
        return self.config.copy()
    
    def get_research_interests(self):
        """获取研究兴趣列表（用于Streamlit界面）
        
        Returns:
            list: 研究兴趣列表
        """
        return self.research_interests.copy()
    
    def get_user_profiles(self):
        """获取用户配置列表（用于Streamlit界面）
        
        Returns:
            list: 用户配置列表
        """
        return self.user_profiles.copy()
    
    def update_research_interests(self, interests):
        """更新研究兴趣（用于Streamlit界面）
        
        Args:
            interests: 研究兴趣列表或字符串
        """
        if isinstance(interests, str):
            self.research_interests = [line.strip() for line in interests.split('\n') if line.strip()]
        elif isinstance(interests, list):
            self.research_interests = interests
        else:
            logger.warning(f"无效的研究兴趣格式: {type(interests)}")
        
        logger.debug(f"更新研究兴趣: {len(self.research_interests)} 条")
    
    def set_task_id(self, task_id: str):
        """设置当前任务ID（用于进度更新）
        
        Args:
            task_id: 任务ID
        """
        self.task_id = task_id
        logger.debug(f"设置任务ID: {task_id}")
    
    # 进度更新方法已从 ProgressTracker 继承
    
    def run_debug_mode(self, target_date=None):
        """运行调试模式（用于Streamlit界面）
        
        Args:
            target_date: 目标日期，格式为YYYY-MM-DD，如果为None则使用今天
            
        Returns:
            tuple: (success, result_data, error_message)
        """
        try:
            return run_debug_recommendation(project_root, target_date)
        except Exception as e:
            error_msg = f"调试模式运行失败: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def setup_realtime_logging(self):
        """设置实时日志（用于Streamlit界面）
        
        Returns:
            bool: 设置是否成功
        """
        try:
            # 这里可以添加特定的日志配置
            # 目前使用默认的logger配置
            logger.info("实时日志已设置")
            return True
        except Exception as e:
            logger.error(f"实时日志设置失败: {str(e)}")
            return False
    
    def get_recent_reports(self, limit=None, username_filter=None):
        """获取最近的报告文件（用于Streamlit界面）
        
        Args:
            limit: 返回的报告数量限制，如果为 None 则不限制数量
            username_filter: 可选的用户名筛选，如果提供则只返回匹配的报告
            
        Returns:
            list: 报告文件信息列表
        """
        try:
            # 使用硬编码的保存目录
            save_dir = self.config.get('save_directory', 'arxiv_history')
            reports_dir = Path(save_dir)
            if not reports_dir.is_absolute():
                reports_dir = project_root / reports_dir
            
            if not reports_dir.exists():
                return []
            
            # 获取所有markdown报告文件
            report_files = list(reports_dir.glob("*.md"))
            
            # 按修改时间排序
            report_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 构建报告信息
            reports = []
            for file_path in report_files:
                try:
                    stat = file_path.stat()
                    # 文件名格式：YYYY-MM-DD_{username}_ARXIV_summary.md
                    # 提取用户名：按 _ 分割，取索引1的部分（索引0是日期）
                    stem_parts = file_path.stem.split('_')
                    date_str = stem_parts[0] if len(stem_parts) > 0 else 'unknown'
                    
                    # 提取用户名：找到 "ARXIV" 的位置，用户名在日期和ARXIV之间
                    username = None
                    if len(stem_parts) >= 3:
                        # 查找 "ARXIV" 的位置
                        arxiv_index = None
                        for i, part in enumerate(stem_parts):
                            if part.upper() == 'ARXIV':
                                arxiv_index = i
                                break
                        
                        if arxiv_index and arxiv_index > 1:
                            # 用户名是索引1到arxiv_index-1之间的所有部分，用下划线连接
                            username_parts = stem_parts[1:arxiv_index]
                            username = '_'.join(username_parts)
                        elif len(stem_parts) >= 2:
                            # 如果没有找到ARXIV，假设第二个片段是用户名（向后兼容）
                            username = stem_parts[1]
                    
                    # 如果提供了用户名筛选，只返回匹配的报告
                    if username_filter and username != username_filter:
                        continue
                    
                    reports.append({
                        'filename': file_path.name,
                        'name': file_path.name,
                        'filepath': str(file_path),
                        'path': file_path,
                        'size': stat.st_size,
                        'modified_time': stat.st_mtime,
                        'date': date_str,
                        'username': username  # 添加用户名字段
                    })
                except Exception as e:
                    logger.warning(f"无法获取文件信息 {file_path}: {str(e)}")
                    continue
            
            # 限制数量（在筛选后），只有当 limit 不为 None 时才限制
            if limit is not None:
                reports = reports[:limit]
            
            return reports
            
        except Exception as e:
            logger.error(f"获取最近报告失败: {str(e)}")
            return []
    
    def run_full_recommendation(self, specific_date=None):
        """运行完整的推荐流程（获取推荐 + 保存报告）
        
        Args:
            specific_date: 指定日期，格式为YYYY-MM-DD
            
        Returns:
            tuple: (success, result_data, error_msg)
        """
        try:
            # 更新进度：初始化组件
            self._update_progress(
                step="初始化系统组件...",
                percentage=5,
                log_message="正在初始化ArXiv获取器和LLM提供商"
            )
            
            # 获取推荐结果
            self._update_progress(
                step="获取论文推荐...",
                percentage=10,
                log_message="开始获取推荐结果"
            )
            
            cli_result = self.get_recommendations(specific_date=specific_date)
            
            if not cli_result['success']:
                self._update_progress(
                    step="推荐失败",
                    percentage=0,
                    log_message=f"推荐失败: {cli_result.get('error', '未知错误')}",
                    log_level="error"
                )
                return False, cli_result.get('data'), cli_result.get('error', '未知错误')
            
            # 获取推荐数据
            report_data = cli_result['data']
            target_date = cli_result['target_date']
            current_time = cli_result['current_time']
            
            # 保存报告
            self._update_progress(
                step="保存报告...",
                percentage=70,
                log_message="正在生成并保存推荐报告"
            )
            
            save_result = self.save_reports(report_data, current_time, target_date=target_date)
            
            # 获取分离的内容
            summary_content = report_data.get('summary', '')
            detailed_analysis = report_data.get('detailed_analysis', '')
            brief_analysis = report_data.get('brief_analysis', '')
            
            # 合并内容
            markdown_content = summary_content + detailed_analysis + brief_analysis
            
            # 生成文件名
            timestamp = get_timezone_aware_now().strftime("%Y%m%d_%H%M%S")
            filename = f"arxiv_recommendations_{timestamp}.md"
            
            result_data = {
                'markdown_content': markdown_content,
                'summary_content': summary_content,
                'detailed_analysis': detailed_analysis,
                'brief_analysis': brief_analysis,
                'html_content': save_result.get('html_content'),
                'html_filepath': save_result.get('html_filepath'),
                'filename': filename,
                'target_date': target_date
            }
            
            # 完成
            self._update_progress(
                step="推荐完成",
                percentage=100,
                log_message=f"推荐报告已生成: {filename}"
            )
            
            return True, result_data, None
            
        except Exception as e:
            logger.error(f"完整推荐流程失败: {str(e)}")
            self._update_progress(
                step="推荐失败",
                percentage=0,
                log_message=f"完整推荐流程失败: {str(e)}",
                log_level="error"
            )
            return False, None, f"完整推荐流程失败: {str(e)}"
    
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
            
            # 初始化LLM提供商（统一使用 DashScope/Qwen）
            heavy_model = get_str('QWEN_MODEL', self.config['qwen_model'])
            heavy_base_url = get_str('DASHSCOPE_BASE_URL', self.config['dashscope_base_url'])
            heavy_api_key = get_str('DASHSCOPE_API_KEY', self.config['dashscope_api_key'])
            heavy_temperature = self.config['qwen_model_temperature']
            heavy_top_p = self.config['qwen_model_top_p']
            heavy_max_tokens = self.config['qwen_model_max_tokens']

            logger.debug(f"初始化LLM提供商 - 提供方: dashscope, 模型: {heavy_model}")
            # 构造主LLM提供者，并作为依赖注入传递给推荐引擎
            # LLMProvider 的 description 参数仍然是字符串，提取 positive_query
            research_interests_dict = self._load_research_interests()
            description_str = research_interests_dict.get("positive_query", "") if isinstance(research_interests_dict, dict) else str(research_interests_dict)
            self.llm_provider = LLMProvider(
                model=heavy_model,
                base_url=heavy_base_url,
                api_key=heavy_api_key,
                description=description_str,
                username=self._get_current_username(),
                temperature=heavy_temperature,
                top_p=heavy_top_p,
                max_tokens=heavy_max_tokens,
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
                relevance_filter_threshold=self.config.get('relevance_filter_threshold', 6),
                model=heavy_model,
                base_url=heavy_base_url,
                api_key=heavy_api_key,
                description=research_interests,
                username=username,
                num_workers=self.config['max_workers'],
                temperature=heavy_temperature,
                top_p=heavy_top_p,
                max_tokens=heavy_max_tokens,
                arxiv_fetcher=self.arxiv_fetcher,
                llm_provider=self.llm_provider,
                task_id=self.task_id,  # 传递task_id用于进度更新
            )
            logger.debug(f"推荐引擎初始化完成 - 类别: {self.config['arxiv_categories']}, 工作线程: {self.config['max_workers']}")
            
            # 初始化输出管理器
            logger.debug("初始化输出管理器")
            template_dir = project_root / 'config' / 'templates'
            self.output_manager = OutputManager(str(template_dir))
            logger.debug("输出管理器初始化完成")
            
            logger.success("系统组件初始化完成")
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    def _load_research_interests(self) -> Dict[str, str]:
        """从用户分类JSON文件加载研究兴趣。
        
        Returns:
            研究兴趣字典，包含 positive_query 和 negative_query
        """
        categories_file = self.config['user_categories_file']
        logger.debug(f"尝试加载研究兴趣文件: {categories_file}")
        
        target_user = load_selected_user_config(categories_file, self.username)
        interests = parse_research_interests(target_user)
        if target_user and target_user.get("user_input"):
            username_info = f"用户 {target_user.get('username', '未知')}" if target_user.get('username') else "第一个用户"
            logger.success(f"从JSON文件加载{username_info}的研究兴趣: {categories_file}")
            return interests

        logger.info("使用默认研究兴趣配置")
        return interests
    
    def _get_current_time(self) -> str:
        """获取当前时间。
        
        Returns:
            格式化的当前时间字符串
        """
        logger.debug("获取当前时间")
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.debug(f"使用本地时间: {local_time}")
        return local_time
    
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
                    logger.warning(f"在{target_date_str}经评估未发现符合兴趣的论文")
            else:
                # 智能回溯模式：尝试获取昨天和前天的论文
                for days_back in [1, 2]:  # 先尝试昨天，再尝试前天
                    target_date = get_timezone_aware_now() - timedelta(days=days_back)
                    target_date_str = target_date.strftime('%Y-%m-%d')
                    logger.info(f"论文获取日期: {target_date_str} (往前{days_back}天)")
                    
                    # 执行推荐流程
                    logger.info("论文推荐流程开始")
                    report_result = self.recommendation_engine.run(current_time, target_date_str)
                    
                    if report_result:
                        logger.success(f"在{target_date_str}找到了论文")
                        break
                    else:
                        logger.warning(f"在{target_date_str}经评估未发现符合兴趣的论文")
            
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
                logger.warning("在目标日期范围内经评估未发现符合兴趣的论文")
                # 根据模式确定错误信息
                if specific_date:
                    error_msg = f"在指定日期 {target_date_str} 经评估未发现符合兴趣的论文"
                else:
                    # 智能回溯模式的错误信息
                    final_target_date_str = (get_timezone_aware_now() - timedelta(days=2)).strftime('%Y-%m-%d')
                    error_msg = f"在目标日期 {final_target_date_str} 经评估未发现符合兴趣的论文"
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
        workflow = ReportWorkflow(self.config, self.output_manager, self._get_current_username)
        return workflow.save_reports(report_result, current_time, target_date)

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


class ArxivRecommenderCLI(RecommendationWorkflow):
    """CLI 兼容入口，实际推荐编排由 RecommendationWorkflow 承担。"""


def main():
    """主程序入口。"""
    try:
        # 日志配置（简化：LOG_LEVEL和LOG_FILE使用固定值，不再从环境变量读取）
        log_level = 'DEBUG'  # 固定为DEBUG
        log_to_console = get_bool('LOG_TO_CONSOLE', True)
        log_file = 'logs/arxiv_recommender.log'  # 固定路径
        log_max_size = get_int('LOG_MAX_SIZE', 10)
        log_backup_count = get_int('LOG_BACKUP_COUNT', 5)
        setup_cli_logging(log_to_console, log_file, log_level, log_max_size, log_backup_count)
        
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
