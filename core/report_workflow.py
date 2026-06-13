"""报告保存与邮件发送编排。"""

from typing import Any, Callable, Dict, Optional, Tuple

from loguru import logger

from core.common_utils import format_timezone_date, sanitize_username
from core.output_manager import OutputManager


class ReportWorkflow:
    """负责推荐报告的 Markdown/HTML 保存和邮件发送。"""

    def __init__(
        self,
        config: Dict[str, Any],
        output_manager: OutputManager,
        username_resolver: Callable[[], str],
    ):
        self.config = config
        self.output_manager = output_manager
        self.username_resolver = username_resolver

    def save_reports(
        self,
        report_result: Dict[str, Any],
        current_time: str,
        target_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """保存报告并按配置发送邮件。"""
        try:
            summary_content = report_result["summary"]
            detailed_analysis = report_result["detailed_analysis"]
            brief_analysis = report_result.get("brief_analysis", "")
            papers = report_result.get("papers", [])
            markdown_content = summary_content + detailed_analysis + brief_analysis
            logger.debug("报告内容生成完成")

            logger.info("报告保存和发送开始")
            self._save_markdown_if_configured(markdown_content, target_date)
            html_filepath, html_content = self._save_html_report_if_configured_separated(
                summary_content,
                detailed_analysis,
                brief_analysis,
                current_time,
                papers,
                target_date,
            )
            self._send_email_if_configured(html_content)

            return {
                "markdown_saved": self.config["save_markdown"],
                "html_saved": html_content is not None,
                "html_content": html_content,
                "html_filepath": html_filepath,
                "email_sent": self.config["send_email"],
            }
        except Exception as e:
            logger.error(f"报告保存异常: {e}")
            return {
                "markdown_saved": False,
                "html_saved": False,
                "html_content": None,
                "email_sent": False,
            }

    def _send_email_if_configured(self, html_content: Optional[str]) -> None:
        """如果配置了邮件，则发送 HTML 报告。"""
        logger.debug("检查邮件发送配置")
        if not self.config["send_email"]:
            logger.debug("邮件发送已禁用")
            return

        if not all([
            self.config["sender_email"],
            self.config["receiver_email"],
            self.config["email_password"],
            self.config["smtp_server"],
        ]):
            logger.warning("邮件配置不完整，跳过发送")
            return

        if not html_content:
            logger.warning("HTML内容为空，跳过邮件发送")
            return

        logger.info(
            f"邮件发送开始 - 发送方: {self.config['sender_email']}, 接收方: {self.config['receiver_email']}"
        )
        try:
            self.output_manager.email_sender.send_html(
                sender=self.config["sender_email"],
                receiver=self.config["receiver_email"],
                password=self.config["email_password"],
                smtp_server=self.config["smtp_server"],
                smtp_port=self.config["smtp_port"],
                html_content=html_content,
                subject_prefix=self.config["subject_prefix"],
                use_ssl=self.config["use_ssl"],
                use_tls=self.config["use_tls"],
            )
            logger.success("邮件发送成功")
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            logger.warning("邮件发送失败，但报告已成功生成并保存到本地")

    def _save_markdown_if_configured(
        self,
        markdown_content: str,
        target_date: Optional[str] = None,
    ) -> Optional[str]:
        """按配置保存 Markdown 报告。"""
        if not self.config["save_markdown"]:
            logger.debug("Markdown保存已禁用")
            return None

        logger.debug("Markdown报告保存开始")
        try:
            date_str = target_date if target_date else format_timezone_date()
            username = self.username_resolver()
            safe_username = sanitize_username(username)
            filename = f"{date_str}_{safe_username}_ARXIV_summary.md"
            logger.debug(f"生成文件名: {filename}")

            filepath = self.output_manager.save_markdown_report(
                content=markdown_content,
                save_dir=self.config["save_directory"],
                filename=filename,
                username=username,
                target_date=target_date,
            )
            if not filepath:
                logger.error("Markdown报告保存失败")
            return filepath
        except Exception as e:
            logger.error(f"Markdown报告保存异常: {e}")
            return None

    def _save_html_report_if_configured_separated(
        self,
        summary_content: str,
        detailed_analysis: str,
        brief_analysis: str,
        current_time: str,
        papers: Optional[list] = None,
        target_date: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """按配置保存分离内容的 HTML 报告。"""
        if not self.config["save_markdown"]:
            logger.debug("HTML报告保存已禁用")
            return None, None

        logger.debug("HTML报告生成开始")
        try:
            date_str = target_date if target_date else format_timezone_date()
            username = self.username_resolver()
            safe_username = sanitize_username(username)
            filename = f"{date_str}_{safe_username}_ARXIV_summary.html"
            logger.debug(f"生成HTML文件名: {filename}")

            filepath, html_content = self.output_manager.save_markdown_report_as_html_separated(
                summary_content=summary_content,
                detailed_analysis=detailed_analysis,
                brief_analysis=brief_analysis,
                save_dir=self.config["save_directory"],
                current_time=current_time,
                username=username,
                filename=filename,
                papers=papers,
                target_date=target_date,
            )
            if not filepath:
                logger.error("HTML报告保存失败")
                return None, None
            return filepath, html_content
        except Exception as e:
            logger.error(f"HTML报告保存异常: {e}")
            return None, None
