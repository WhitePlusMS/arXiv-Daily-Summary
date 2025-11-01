"""输出管理模块

提供论文推荐结果的输出管理功能，包括HTML邮件格式化、Markdown报告生成和邮件发送。
整合了原email_formatter的功能，并使用新的模板渲染系统。
"""

import datetime
import math
import smtplib
import os
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from typing import List, Dict, Any, Optional
from pathlib import Path

from loguru import logger
from .template_renderer import TemplateRenderer
from .common_utils import sanitize_username
import re


class OutputManager:
    """输出管理器，负责格式化和发送论文推荐结果。"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """初始化输出管理器。
        
        Args:
            template_dir: 模板目录路径，如果为None则使用默认路径
        """
        logger.info("OutputManager初始化开始")
        # 如果没有指定模板目录，使用项目根目录下的templates
        if template_dir is None:
            from pathlib import Path
            current_dir = Path(__file__).parent
            template_dir = str(current_dir.parent / "templates")
        self.template_renderer = TemplateRenderer(template_dir)
        logger.success("OutputManager初始化完成")

    def _sanitize_username_for_filename(self, username: str) -> str:
        """将用户名转换为安全的文件名片段（用于文件名）。"""
        # 委托给统一的工具函数，保持与原逻辑完全一致
        return sanitize_username(username)
    
    def save_markdown_report(
        self, 
        content: str, 
        save_dir: str, 
        filename: Optional[str] = None,
        username: str = "TEST",
        target_date: Optional[str] = None,
    ) -> Optional[str]:
        """保存Markdown报告到文件。
        
        Args:
            content: Markdown内容
            save_dir: 保存目录
            filename: 文件名，如果为None则使用日期生成
            username: 用于文件名的用户名（可选，默认"TEST"）
            target_date: 查询目标日期（用于文件名日期）
            
        Returns:
            保存的文件路径，失败时返回None
        """
        try:
            # 确保保存目录存在
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            if filename is None:
                date_str = target_date if target_date else datetime.datetime.now().strftime("%Y-%m-%d")
                safe_username = self._sanitize_username_for_filename(username)
                filename = f"{date_str}_{safe_username}_ARXIV_summary.md"
            
            filepath = Path(save_dir) / filename
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.debug(f"Markdown报告保存完成 - {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Markdown报告保存失败: {e}")
            return None
    
    def save_markdown_report_as_html(
        self, 
        markdown_content: str, 
        save_dir: str, 
        current_time: str,
        username: str = "TEST",
        filename: Optional[str] = None,
        target_date: Optional[str] = None,
    ) -> Optional[str]:
        """将Markdown研究报告转换为HTML格式并保存。
        
        Args:
            markdown_content: Markdown内容
            save_dir: 保存目录
            current_time: 当前时间
            username: 用户名，用于模板渲染
            filename: 文件名，如果为None则使用日期生成
            target_date: 查询目标日期（用于文件名与模板展示）
            
        Returns:
            保存的文件路径，失败时返回None
        """
        try:
            # 确保保存目录存在
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            if filename is None:
                date_str = target_date if target_date else datetime.datetime.now().strftime("%Y-%m-%d")
                safe_username = self._sanitize_username_for_filename(username)
                filename = f"{date_str}_{safe_username}_ARXIV_summary.html"
            
            filepath = Path(save_dir) / filename
            
            # 使用模板渲染HTML
            html_content = self.template_renderer.render_template(
                'markdown_report_email.j2',
                markdown_content=markdown_content,
                current_time=current_time,
                username=username,
                target_date=target_date,
            )
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.debug(f"HTML研究报告保存完成 - {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"HTML研究报告保存失败: {e}")
            return None
    
    def save_markdown_report_as_html_separated(self, summary_content: str, detailed_analysis: str, brief_analysis: str, save_dir: str, current_time: str, username: str = "TEST", filename: str = None, papers: list = None, target_date: Optional[str] = None):
        """将分离的Markdown内容保存为HTML格式的研究报告。
        
        Args:
            summary_content: 总结内容
            detailed_analysis: 详细分析内容
            brief_analysis: 简要分析内容
            save_dir: 保存目录
            current_time: 当前时间
            username: 用户名，用于模板渲染
            filename: 文件名，如果为None则使用日期生成
            papers: 论文数据列表，用于生成统计信息
            target_date: 查询目标日期（用于文件名与模板展示）
            
        Returns:
            tuple: (保存的文件路径, HTML内容)，失败时返回(None, None)
        """
        try:
            # 确保保存目录存在
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            if filename is None:
                date_str = target_date if target_date else datetime.datetime.now().strftime("%Y-%m-%d")
                safe_username = self._sanitize_username_for_filename(username)
                filename = f"{date_str}_{safe_username}_ARXIV_summary.html"
            
            filepath = Path(save_dir) / filename
            
            # 更稳健地清理细分块标题与分隔线（支持可变空白与不同标记）
            import re
            if detailed_analysis:
                # 去掉顶级标题行与多余分隔线
                detailed_analysis = re.sub(r"^\s*#\s*📚\s*详细论文列表\s*\n?", "", detailed_analysis, flags=re.MULTILINE)
                detailed_analysis = re.sub(r"\n?\s*---\s*\n?", "\n", detailed_analysis).strip()

            if brief_analysis:
                brief_analysis = re.sub(r"^\s*#\s*📝\s*简要论文列表\s*\n?", "", brief_analysis, flags=re.MULTILINE)
                brief_analysis = re.sub(r"\n?\s*---\s*\n?", "\n", brief_analysis).strip()
            
            # 生成统计数据
            category_stats = None
            total_papers = 0
            paper_titles = None
            
            if papers:
                # 统计各分类的论文数量
                category_counts = {}
                titles = []
                
                for paper in papers:
                    # 提取论文标题
                    if 'title' in paper:
                        titles.append(paper['title'])
                    
                    # 统计分类（优先使用明确字段，再回退）
                    category = None
                    # 1) primary_category 优先
                    primary = paper.get('primary_category')
                    if isinstance(primary, str) and primary:
                        category = primary
                    # 2) categories 列表次之
                    if not category:
                        categories = paper.get('categories')
                        if isinstance(categories, list) and categories:
                            category = categories[0]
                    # 3) 旧字段 category 再次回退
                    if not category and paper.get('category'):
                        category = paper.get('category')
                    # 4) 最后尝试 arXiv_id 推断（仅支持 cs.AI/xxxx 样式）
                    if not category and paper.get('arXiv_id'):
                        arxiv_id = paper['arXiv_id']
                        if '/' in arxiv_id:
                            category = arxiv_id.split('/')[0]
                    
                    if category:
                        category_counts[category] = category_counts.get(category, 0) + 1
                
                category_stats = category_counts if category_counts else None
                total_papers = len(papers)
                paper_titles = titles if titles else None
            
            # 使用模板渲染HTML，传递分离的内容和统计数据
            html_content = self.template_renderer.render_template(
                'markdown_report_email.j2',
                summary_content=summary_content,
                detailed_analysis=detailed_analysis,
                brief_analysis=brief_analysis,
                current_time=current_time,
                username=username,
                category_stats=category_stats,
                total_papers=total_papers,
                paper_titles=paper_titles,
                papers=papers,
                target_date=target_date,
            )
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.debug(f"HTML分离报告保存完成 - {filepath}")
            return str(filepath), html_content
            
        except Exception as e:
            logger.error(f"HTML分离报告保存失败: {e}")
            return None, None
    


    
    def send_email(
        self,
        sender: str,
        receiver: str,
        password: str,
        smtp_server: str,
        smtp_port: int,
        html_content: str,
        subject_prefix: str = "每日arXiv",
        use_ssl: bool = False,
        use_tls: bool = False,
    ):
        """发送格式化内容的邮件。
        
        Args:
            sender: 发件人邮箱地址
            receiver: 收件人邮箱地址（多个用逗号分隔）
            password: 发件人邮箱密码
            smtp_server: SMTP服务器地址
            smtp_port: SMTP服务器端口
            html_content: 要发送的HTML内容
            subject_prefix: 邮件主题前缀
            use_ssl: 是否使用SSL
            use_tls: 是否使用TLS
            
        Raises:
            Exception: 邮件发送失败时抛出异常
        """
        # 创建邮件消息
        msg = MIMEText(html_content, "html", "utf-8")
        
        # 处理多个收件人
        receivers = [addr.strip() for addr in receiver.split(",")]

        # 设置邮件头
        msg["From"] = Header(sender)
        msg["To"] = Header(", ".join(receivers))
        today = datetime.datetime.now().strftime("%Y/%m/%d")
        msg["Subject"] = Header(f"{subject_prefix} {today}", "utf-8")
        
        # 发送邮件
        logger.info(f"邮件发送开始 - 收件人: {len(receivers)} 个")
        server = None
        try:
            if use_ssl:
                logger.debug(f"使用SSL连接 - {smtp_server}:{smtp_port}")
                # 尝试较短的超时时间，避免长时间等待
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
            elif use_tls:
                logger.debug(f"使用TLS连接 - {smtp_server}:{smtp_port}")
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.starttls()
            else:  # 如果都没指定则使用普通SMTP
                logger.debug(f"使用普通SMTP连接 - {smtp_server}:{smtp_port}")
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)

            logger.debug("SMTP连接建立成功，开始登录...")
            server.login(sender, password)
            logger.debug("SMTP登录成功，开始发送邮件...")
            server.sendmail(sender, receivers, msg.as_string())
            logger.success(f"邮件发送完成 - 收件人: {', '.join(receivers)}")
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP认证失败: {e}")
            logger.error("请检查邮箱地址和授权码是否正确")
            raise
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP连接失败: {e}")
            logger.error("请检查SMTP服务器地址和端口是否正确")
            raise
        except (ConnectionError, OSError, TimeoutError) as e:
            logger.error(f"网络连接错误: {e}")
            logger.error("请检查网络连接或防火墙设置")
            raise
        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {e}")
            raise
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            # 重新抛出异常，让调用者处理
            raise
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass  # 忽略quit时的异常


def main():
    """独立测试函数。"""
    logger.info("OutputManager测试开始")
    
    # 创建测试数据
    test_papers = [
        {
            'title': 'Test Paper: Advanced Machine Learning Techniques',
            'arXiv_id': '2024.0001',
            'authors': ['Alice Smith', 'Bob Johnson', 'Carol Davis'],
            'published': '2024-01-01T10:00:00Z',
            'relevance_score': 8.5,
            'research_background': '本文研究了机器学习在计算机视觉领域的最新进展，特别关注深度学习模型的优化问题。',
            'methodology_innovation': '提出了一种新的注意力机制，能够显著提高模型的特征提取能力。',
            'experimental_results': '在多个基准数据集上取得了state-of-the-art的性能，准确率提升了3-5%。',
            'conclusion_significance': '该方法为计算机视觉任务提供了新的解决思路，具有重要的理论和实践价值。',
            'tldr': '提出了改进的注意力机制，在计算机视觉任务上取得显著性能提升。',
            'pdf_url': 'https://arxiv.org/pdf/2024.0001.pdf',
            'abstract_url': 'https://arxiv.org/abs/2024.0001'
        },
        {
            'title': 'Efficient Neural Network Architectures for Edge Computing',
            'arXiv_id': '2024.0002',
            'authors': ['David Wilson', 'Eva Brown'],
            'published': '2024-01-02T14:30:00Z',
            'relevance_score': 7.2,
            'research_background': '随着边缘计算的发展，需要设计更加高效的神经网络架构来适应资源受限的环境。',
            'methodology_innovation': '设计了一种轻量级的神经网络架构，通过动态剪枝和量化技术减少计算开销。',
            'experimental_results': '在保持精度的同时，模型大小减少了80%，推理速度提升了5倍。',
            'conclusion_significance': '为边缘设备上的AI应用提供了实用的解决方案。',
            'tldr': '设计了适用于边缘计算的轻量级神经网络架构，显著提升了效率。',
            'pdf_url': 'https://arxiv.org/pdf/2024.0002.pdf',
            'abstract_url': 'https://arxiv.org/abs/2024.0002'
        }
    ]
    
    try:
        # 初始化输出管理器
        output_manager = OutputManager()
        
        # 测试HTML报告保存功能
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info("开始HTML报告保存测试")
        test_markdown = "# 测试报告\n\n这是一个测试Markdown内容。"
        
        try:
            html_path = output_manager.save_markdown_report_as_html(
                markdown_content=test_markdown,
                save_dir="./test_output",
                current_time=current_time
            )
            logger.success(f"HTML报告测试完成 - {html_path}")
        except Exception as e:
            logger.error(f"HTML报告测试失败: {e}")
        
        # 测试Markdown报告保存功能
        logger.info("开始Markdown报告保存测试")
        try:
            md_path = output_manager.save_markdown_report(
                content=test_markdown,
                save_dir="./test_output",
                username="TEST",
            )
            logger.success(f"Markdown报告测试完成 - {md_path}")
        except Exception as e:
            logger.error(f"Markdown报告测试失败: {e}")
        
        logger.success("OutputManager测试完成")
        
    except Exception as e:
        logger.error(f"OutputManager测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()