"""邮件发送模块

将SMTP邮件发送逻辑与输出管理解耦，便于替换实现与独立测试。
"""

import datetime
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from typing import Optional
from loguru import logger


class EmailSender:
    """简单的邮件发送器，支持HTML内容发送与SSL/TLS配置。"""

    def send_html(
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
    ) -> None:
        """发送HTML邮件。

        Args:
            sender: 发件人邮箱地址
            receiver: 收件人邮箱地址（多个用逗号分隔）
            password: 发件人邮箱密码或授权码
            smtp_server: SMTP服务器地址
            smtp_port: SMTP服务器端口
            html_content: HTML内容
            subject_prefix: 邮件主题前缀
            use_ssl: 是否使用SSL
            use_tls: 是否使用TLS
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
        server: Optional[smtplib.SMTP] = None
        try:
            if use_ssl:
                logger.debug(f"使用SSL连接 - {smtp_server}:{smtp_port}")
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
            elif use_tls:
                logger.debug(f"使用TLS连接 - {smtp_server}:{smtp_port}")
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.starttls()
            else:
                logger.debug(f"使用普通SMTP连接 - {smtp_server}:{smtp_port}")
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)

            logger.debug("SMTP连接建立成功，开始登录...")
            server.login(sender, password)
            logger.debug("SMTP登录成功，开始发送邮件...")
            server.sendmail(sender, receivers, msg.as_string())
            logger.success(f"邮件发送完成 - 收件人: {', '.join(receivers)}")

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP认证失败: {e}")
            raise
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP连接失败: {e}")
            raise
        except (ConnectionError, OSError, TimeoutError) as e:
            logger.error(f"网络连接错误: {e}")
            raise
        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {e}")
            raise
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            raise
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass