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
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'), override=True)

# 导入CLI模块
from core.task3_recommendation_cli.cli_main import ArxivRecommenderCLI
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
        """加载配置（与cli_main.py保持一致）"""
        try:
            # 强制重新加载环境变量
            load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)
            
            self.config = {
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
                
                # 调试模式配置
                'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true',
                
                # 日志配置
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'log_file': os.getenv('LOG_FILE', 'logs/arxiv_recommender.log'),
                'log_to_console': os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true',
                'log_max_size': int(os.getenv('LOG_MAX_SIZE', '10')),
                'log_backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
            }
            return True
        except Exception as e:
            st.error(f"配置加载失败: {str(e)}")
            return False
    
    def load_research_interests(self):
        """加载研究兴趣"""
        try:
            interests_file = project_root / "research_interests.md"
            if interests_file.exists():
                with open(interests_file, 'r', encoding='utf-8') as f:
                    self.research_interests = [line.strip() for line in f if line.strip()]
            return True
        except Exception as e:
            st.error(f"研究兴趣加载失败: {str(e)}")
            return False

    def load_user_profiles(self):
        """加载用户配置"""
        try:
            user_profiles_file = project_root / "data" / "users" / "user_categories.json"
            if user_profiles_file.exists():
                with open(user_profiles_file, 'r', encoding='utf-8') as f:
                    self.user_profiles = json.load(f)
            return True
        except Exception as e:
            st.error(f"用户配置加载失败: {str(e)}")
            return False
    
    def initialize_components(self, selected_username=None):
        """初始化系统组件
        
        Args:
            selected_username: 选择的用户名，如果为None或"自定义"则不传入用户名
        """
        try:
            # 初始化CLI应用实例，传入用户名（如果不是自定义的话
            username = selected_username if selected_username and selected_username != "自定义" else None
            self.cli_app = ArxivRecommenderCLI(username=username)
            
            # 更新CLI应用的研究兴趣
            self.cli_app.research_interests = self.research_interests
            
            # 初始化输出管理器（用于配置显示）
            template_dir = project_root / 'templates'
            self.output_manager = OutputManager(str(template_dir))
            
            return True
        except Exception as e:
            st.error(f"组件初始化失败: {str(e)}")
            return False
    
    def setup_realtime_logging(self):
        """设置实时日志显示"""
        # 创建日志容器
        self.log_container = st.empty()
        self.log_messages = []
        
        # 创建自定义日志处理器
        class StreamlitLogHandler(logging.Handler):
            def __init__(self, app_instance):
                super().__init__()
                self.app = app_instance
                
            def emit(self, record):
                try:
                    # 检查是否在主线程中且有有效的Streamlit会话
                    import threading
                    from streamlit.runtime.scriptrunner import get_script_run_ctx
                    
                    if (self.app.log_container is not None and 
                        threading.current_thread() == threading.main_thread() and
                        get_script_run_ctx() is not None):
                        
                        log_entry = self.format(record)
                        self.app.log_messages.append(log_entry)
                        # 只保留最近的20条日志
                        if len(self.app.log_messages) > 20:
                            self.app.log_messages = self.app.log_messages[-20:]
                        
                        # 更新显示
                        log_text = "\n".join(self.app.log_messages)
                        self.app.log_container.text_area(
                            "📋 实时运行日志",
                            value=log_text,
                            height=200,
                            disabled=True
                        )
                    else:
                        # 在多线程环境中，只添加到消息列表，不更新UI
                        if self.app.log_container is not None:
                            log_entry = self.format(record)
                            self.app.log_messages.append(log_entry)
                            # 只保留最近的20条日志
                            if len(self.app.log_messages) > 20:
                                self.app.log_messages = self.app.log_messages[-20:]
                except Exception:
                    # 如果日志处理失败，静默忽略，避免影响主程序
                    pass
        
        # 添加处理器到根日志记录器
        handler = StreamlitLogHandler(self)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # 获取根日志记录器并添加处理器
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        
        return handler
    
    def _run_debug_mode(self, specific_date=None):
        """调试模式：返回假数据，不调用真实API"""
        try:
            # 设置实时日志显示
            log_handler = self.setup_realtime_logging()
            
            try:
                target_date = specific_date or (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
                
                # 模拟日志输出
                self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - INFO - [调试模式] 开始获取 {target_date} 的论文推荐...")
                self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - INFO - [调试模式] 模拟获取ArXiv论文数据...")
                self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - INFO - [调试模式] 模拟LLM分析处理...")
                self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - SUCCESS - [调试模式] 成功获取到 {target_date} 的论文！")
                
                # 生成假数据
                fake_summary = f"""# ArXiv 每日论文推荐报告 - {target_date}

## 📊 今日概览

**[调试模式]** 本报告为测试数据，未调用真实API。

- 📅 **目标日期**: {target_date}
- 🔍 **检索分类**: {', '.join(self.config.get('arxiv_categories', ['cs.CV', 'cs.LG']))}
- 📄 **论文总数**: 15篇
- ⭐ **重点推荐**: 3篇
- 📝 **简要分析**: 7篇

## 🎯 研究兴趣匹配度

根据您的研究方向：
{chr(10).join([f'- {interest}' for interest in self.research_interests[:3]])}

系统为您筛选出最相关的论文。

---

"""
                
                fake_detailed = """## 🌟 重点推荐论文

### 1. [调试] Advanced Deep Learning Techniques for Computer Vision

**作者**: Zhang Wei, Li Ming, Wang Xiaoli  
**发布时间**: {target_date}  
**分类**: cs.CV, cs.LG  
**链接**: https://arxiv.org/abs/2024.12345

#### 📋 论文摘要
本文提出了一种新的深度学习方法，用于改进计算机视觉任务的性能。该方法结合了注意力机制和残差网络，在多个基准数据集上取得了显著的改进。

#### 🔍 详细分析
**技术创新点**:
- 提出了多尺度注意力机制
- 设计了新的残差连接结构
- 引入了自适应学习率调整策略

**实验结果**:
- 在ImageNet上准确率提升2.3%
- 推理速度提升15%
- 模型参数减少10%

**研究意义**:
该工作为计算机视觉领域提供了新的思路，特别是在模型效率和性能平衡方面有重要贡献。

---

### 2. [调试] Efficient Natural Language Processing with Transformer Variants

**作者**: Chen Yifan, Liu Jiawei, Zhou Mengting  
**发布时间**: {target_date}  
**分类**: cs.CL, cs.LG  
**链接**: https://arxiv.org/abs/2024.12346

#### 📋 论文摘要
本研究探索了Transformer架构的新变体，旨在提高自然语言处理任务的效率和性能。

#### 🔍 详细分析
**技术创新点**:
- 优化了自注意力机制的计算复杂度
- 提出了新的位置编码方法
- 设计了层次化的特征融合策略

**实验结果**:
- 在GLUE基准上平均提升1.8%
- 训练时间减少30%
- 内存使用降低25%

---

""".format(target_date=target_date)
                
                fake_brief = """## 📝 简要分析论文

### 3. [调试] Reinforcement Learning for Robotics Applications
**作者**: Wang Hao, Li Shan  
**分类**: cs.RO, cs.LG  
**简要**: 提出了一种新的强化学习算法，用于机器人控制任务，在仿真环境中表现优异。

### 4. [调试] Graph Neural Networks for Social Network Analysis
**作者**: Yang Mei, Zhang Lei  
**分类**: cs.SI, cs.LG  
**简要**: 设计了专门用于社交网络分析的图神经网络架构，能够有效捕获社交关系的复杂模式。

### 5. [调试] Federated Learning with Privacy Preservation
**作者**: Liu Qiang, Chen Xin  
**分类**: cs.CR, cs.LG  
**简要**: 在联邦学习框架中引入了新的隐私保护机制，平衡了模型性能和隐私安全。

### 6. [调试] Multi-Modal Learning for Medical Image Analysis
**作者**: Zhou Ling, Wang Jun  
**分类**: cs.CV, cs.LG  
**简要**: 结合多模态数据进行医学图像分析，在疾病诊断任务上取得了显著改进。

### 7. [调试] Quantum Machine Learning Algorithms
**作者**: Li Feng, Zhang Yu  
**分类**: quant-ph, cs.LG  
**简要**: 探索了量子计算在机器学习中的应用，提出了几种新的量子机器学习算法。

---

## 📈 总结

**[调试模式提示]** 以上内容为模拟数据，用于测试系统功能。在实际使用中，系统会调用真实的ArXiv API和LLM服务来生成准确的论文推荐报告。

今日推荐的论文涵盖了计算机视觉、自然语言处理、强化学习等多个前沿领域，为您的研究提供了丰富的参考资料。

"""
                
                # 合并内容
                markdown_content = fake_summary + fake_detailed + fake_brief
                
                # 生成HTML内容（简化版）
                fake_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>ArXiv推荐报告 - {target_date}</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>ArXiv 每日论文推荐报告 - {target_date}</h1>
    <p><strong>[调试模式]</strong> 本报告为测试数据</p>
    <div>{markdown_content.replace(chr(10), '<br>')}</div>
</body>
</html>"""
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"arxiv_recommendations_debug_{timestamp}.md"
                html_filename = f"arxiv_recommendations_debug_{timestamp}.html"
                
                # 为调试模式创建临时HTML文件
                save_dir = Path(self.config.get('save_directory', './arxiv_history'))
                save_dir.mkdir(exist_ok=True)
                html_filepath = save_dir / html_filename
                
                # 保存HTML文件以便查看
                try:
                    with open(html_filepath, 'w', encoding='utf-8') as f:
                        f.write(fake_html)
                    self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - INFO - [调试模式] HTML报告已保存: {html_filepath}")
                except Exception as e:
                    self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - WARNING - [调试模式] HTML保存失败: {str(e)}")
                    html_filepath = None
                
                self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - SUCCESS - [调试模式] 推荐系统运行完成！")
                
                return {
                    'success': True,
                    'report': markdown_content,
                    'summary_content': fake_summary,
                    'detailed_analysis': fake_detailed,
                    'brief_analysis': fake_brief,
                    'html_content': fake_html,
                    'html_filepath': str(html_filepath) if html_filepath else None,
                    'filename': filename,
                    'target_date': target_date,
                    'debug_mode': True
                }
                
            finally:
                # 移除日志处理器
                root_logger = logging.getLogger()
                root_logger.removeHandler(log_handler)
                
        except Exception as e:
            if hasattr(self, 'log_messages'):
                self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - ERROR - [调试模式] 系统异常: {str(e)}")
            return {
                'success': False,
                'error': f"[调试模式] 推荐系统运行失败: {str(e)}",
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
            
            # 设置实时日志显示
            log_handler = self.setup_realtime_logging()
            
            try:
                # 调用CLI的get_recommendations方法获取推荐结果
                if specific_date:
                    self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - INFO - 开始获取 {specific_date} 的论文推荐...")
                else:
                    self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - INFO - 开始获取论文推荐...")
                cli_result = self.cli_app.get_recommendations(specific_date=specific_date)
                
                if cli_result['success']:
                    # 显示成功信息
                    self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - SUCCESS - 成功获取到 {cli_result['target_date']} 的论文！")
                    
                    # 获取推荐数据
                    report_data = cli_result['data']
                    
                    # 调用CLI的save_reports方法保存报告
                    self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - INFO - 正在保存报告...")
                    save_result = self.cli_app.save_reports(report_data, cli_result['current_time'], target_date=cli_result.get('target_date'))
                    
                    # 获取分离的内容
                    summary_content = report_data.get('summary', '')
                    detailed_analysis = report_data.get('detailed_analysis', '')
                    brief_analysis = report_data.get('brief_analysis', '')
                    
                    # 为向后兼容，合并内容
                    markdown_content = summary_content + detailed_analysis + brief_analysis
                    
                    # 生成文件名用于下载
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"arxiv_recommendations_{timestamp}.md"
                    
                    self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - SUCCESS - 推荐系统运行完成！")
                    
                    return {
                        'success': True,
                        'report': markdown_content,
                        'summary_content': summary_content,
                        'detailed_analysis': detailed_analysis,
                        'brief_analysis': brief_analysis,
                        'html_content': save_result.get('html_content'),
                        'html_filepath': save_result.get('html_filepath'),
                        'filename': filename,
                        'target_date': cli_result['target_date']
                    }
                else:
                    # 检查是否是"未找到论文"的特定情况
                    no_papers_found_messages = ["未找到相关论文", "在目标日期范围内未找到相关论文"]
                    is_no_papers_error = any(msg in cli_result.get('error', '') for msg in no_papers_found_messages)

                    if is_no_papers_error:
                        target_date_str = cli_result.get('target_date', '最近')
                        self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - WARNING - 在 {target_date_str} 未找到符合条件的论文")
                        
                        # 检查是否为连续两天未找到论文的情况（CLI已经尝试了昨天和前天）
                        # CLI返回的错误信息格式为："在目标日期 YYYY-MM-DD 未找到相关论文"
                        if "在目标日期" in cli_result.get('error', '') and "未找到相关论文" in cli_result.get('error', ''):
                            # 显示周末提示
                            return {
                                'success': False,
                                'error': cli_result['error'],
                                'warning': f"在 {target_date_str} 未找到论文",
                                'show_weekend_tip': True  # 标记需要显示周末提示
                            }
                        else:
                            return {
                                'success': False,
                                'error': cli_result['error'],
                                'warning': f"在 {target_date_str} 未找到论文"
                            }
                    else:
                        # 处理其他未知错误
                        self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - ERROR - 推荐系统运行失败: {cli_result['error']}")
                        return {
                            'success': False,
                            'error': cli_result['error']
                        }
            finally:
                # 移除日志处理器
                root_logger = logging.getLogger()
                root_logger.removeHandler(log_handler)
                    
        except Exception as e:
            if hasattr(self, 'log_messages'):
                self.log_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - ERROR - 系统异常: {str(e)}")
            return {
                'success': False, 
                'error': f"推荐系统运行失败: {str(e)}",
                'traceback': traceback.format_exc()
            }



def get_recent_reports(limit=10):
    """获取最近的报告文件"""
    try:
        reports_dir = project_root / "arxiv_history"
        if not reports_dir.exists():
            return []
        
        report_files = []
        for file_path in reports_dir.glob("*.md"):
            if file_path.is_file():
                report_files.append({
                    'name': file_path.name,
                    'path': file_path,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                })
        
        # 按修改时间排序，最新的在前
        report_files.sort(key=lambda x: x['modified'], reverse=True)
        return report_files[:limit]
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
    else:
        st.info("🚀 **生产模式** - 系统将调用真实的ArXiv API和LLM服务")

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