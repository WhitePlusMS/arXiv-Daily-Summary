"""
Email Formatter

Provides functionality to format paper recommendations into HTML emails.
"""

import datetime
import math
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from typing import List

import os
from dotenv import load_dotenv
from loguru import logger


class EmailFormatter:
    """Formats paper recommendations into HTML email content."""
    
    def __init__(self):
        self._email_template = self._load_email_template()
        self._empty_template = self._load_empty_template()
    
    def _load_email_template(self) -> str:
        """Load the base HTML email template."""
        return """
<!DOCTYPE HTML>
<html>
<head>
  <style>
    .star-wrapper {
      font-size: 1.3em;
      line-height: 1;
      display: inline-flex;
      align-items: center;
    }
    .half-star {
      display: inline-block;
      width: 0.5em;
      overflow: hidden;
      white-space: nowrap;
      vertical-align: middle;
    }
    .full-star {
      vertical-align: middle;
    }
  </style>
</head>
<body>
<div>__CONTENT__</div>
<br><br>
<div>To unsubscribe, remove your email in your Github Action setting.</div>
</body>
</html>
        """.strip()
    
    def _load_empty_template(self) -> str:
        """Load template for when no papers are available."""
        return """
<table border="0" cellpadding="0" cellspacing="0" width="100%" 
       style="font-family: Arial, sans-serif; border: 1px solid #ddd; 
              border-radius: 8px; padding: 16px; background-color: #f9f9f9;">
  <tr>
    <td style="font-size: 20px; font-weight: bold; color: #333;">
        No Papers Today. Take a Rest!
    </td>
  </tr>
</table>
        """.strip()
    
    def get_empty_content(self) -> str:
        """Get content for when no papers are available."""
        return self._email_template.replace("__CONTENT__", self._empty_template)
    
    def wrap_content(self, content: str) -> str:
        """Wrap content in email template."""
        return self._email_template.replace("__CONTENT__", content)
    
    def generate_star_rating(self, score: float) -> str:
        """
        Generate HTML star rating based on relevance score.
        
        Args:
            score: Relevance score from 0-10
            
        Returns:
            HTML string with star rating
        """
        full_star = '<span class="full-star">⭐</span>'
        half_star = '<span class="half-star">⭐</span>'
        
        low_threshold = 2
        high_threshold = 8
        
        if score <= low_threshold:
            return ""
        elif score >= high_threshold:
            return '<div class="star-wrapper">' + full_star * 5 + '</div>'
        else:
            interval = (high_threshold - low_threshold) / 10
            star_count = math.ceil((score - low_threshold) / interval)
            full_stars = star_count // 2
            half_stars = star_count % 2
            
            return (
                '<div class="star-wrapper">'
                + full_star * full_stars
                + half_star * half_stars
                + '</div>'
            )
    
    def create_paper_block(
        self, title: str, rating: str, arxiv_id: str, summary: str, pdf_url: str
    ) -> str:
        """
        Create HTML block for a single paper.
        
        Args:
            title: Paper title
            rating: HTML star rating
            arxiv_id: ArXiv paper ID
            summary: Paper summary
            pdf_url: PDF download URL
            
        Returns:
            HTML string for paper block
        """
        return f"""
<table border="0" cellpadding="0" cellspacing="0" width="100%" 
       style="font-family: Arial, sans-serif; border: 1px solid #ddd; 
              border-radius: 8px; padding: 16px; background-color: #f9f9f9;">
    <tr>
        <td style="font-size: 20px; font-weight: bold; color: #333;">
            {title}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>Relevance:</strong> {rating}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>arXiv ID:</strong> {arxiv_id}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>TLDR:</strong> {summary}
        </td>
    </tr>
    <tr>
        <td style="padding: 8px 0;">
            <a href="{pdf_url}" 
               style="display: inline-block; text-decoration: none; 
                      font-size: 14px; font-weight: bold; color: #fff; 
                      background-color: #d9534f; padding: 8px 16px; 
                      border-radius: 4px;">PDF</a>
        </td>
    </tr>
</table>
        """.strip()
    
    def format_summary_html(self, summary_html: str) -> str:
        """
        Format summary HTML with additional styling.
        
        Args:
            summary_html: Raw summary HTML from LLM
            
        Returns:
            Formatted HTML with styling
        """
        style = """
<style>
    h2 {
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 12px;
        margin: 25px 0 20px 0;
        font-size: 28px;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    p {
        color: #34495e;
        line-height: 1.8;
        margin: 15px 0;
        font-size: 16px;
    }
    ol {
        color: #34495e;
        line-height: 1.8;
        font-size: 16px;
    }
    li {
        margin: 15px 0;
        font-size: 16px;
    }
    .paper-title {
        color: #2980b9;
        font-weight: bold;
        font-size: 20px;
    }
    .relevance {
        color: #e74c3c;
        font-style: italic;
        font-size: 18px;
        font-weight: bold;
    }
    .abstract, .analysis {
        margin-left: 25px;
        color: #2c3e50;
        font-size: 16px;
        line-height: 1.8;
    }
</style>
        """.strip()
        
        return summary_html.replace("</head>", f"{style}</head>")
    
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
        """
        发送格式化内容的邮件。
        
        参数:
            sender: 发件人邮箱地址
            receiver: 收件人邮箱地址（多个用逗号分隔）
            password: 发件人邮箱密码
            smtp_server: SMTP服务器地址
            smtp_port: SMTP服务器端口
            html_content: 要发送的HTML内容
            subject_prefix: 邮件主题前缀
        """
        # Create email message
        msg = MIMEText(html_content, "html", "utf-8")
        
        # Handle multiple receivers
        receivers = [addr.strip() for addr in receiver.split(",")]

        # Set From, To, and Subject headers
        msg["From"] = Header(sender)
        msg["To"] = Header(", ".join(receivers))
        today = datetime.datetime.now().strftime("%Y/%m/%d")
        msg["Subject"] = Header(f"{subject_prefix} {today}", "utf-8")
        
        # Send email
        server = None
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            elif use_tls:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            else: # Fallback to plain SMTP if neither is specified
                server = smtplib.SMTP(smtp_server, smtp_port)

            server.login(sender, password)
            server.sendmail(sender, receivers, msg.as_string())
            logger.info("Email sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            # Re-raise the exception so the caller can handle it
            raise
        finally:
            if server:
                server.quit()

# if __name__ == '__main__':
#     load_dotenv()

#     # 从环境变量加载邮件配置
#     smtp_host = os.getenv("SMTP_HOST")
#     smtp_port = int(os.getenv("SMTP_PORT", 465))
#     smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
#     smtp_use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
#     smtp_username = os.getenv("SMTP_USERNAME")
#     smtp_password = os.getenv("SMTP_PASSWORD")
#     smtp_from_email = os.getenv("SMTP_FROM_EMAIL")
#     smtp_to_email = os.getenv("SMTP_TO_EMAIL")

#     # 创建邮件格式化器
#     formatter = EmailFormatter()

#     # 创建一个简单的HTML内容用于测试
#     test_html_content = """
#     <h1>测试邮件</h1>
#     <p>这是一封来自ArXiv每日文章摘要系统的测试邮件。</p>
#     """
    
#     html_body = formatter.wrap_content(test_html_content)

#     # 发送邮件
#     try:
#         formatter.send_email(
#             sender=smtp_from_email,
#             receiver=smtp_to_email,
#             password=smtp_password,
#             smtp_server=smtp_host,
#             smtp_port=smtp_port,
#             html_content=html_body,
#             subject_prefix="[测试]ArXiv Daily Digest",
#             use_ssl=smtp_use_ssl,
#             use_tls=smtp_use_tls
#         )
#         print(f"测试邮件已成功发送至 {smtp_to_email}")
#     except Exception as e:
#         print(f"发送测试邮件时出错: {e}")