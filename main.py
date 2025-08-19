"""
ArXiv每日论文推荐系统 - 命令行接口

该模块提供论文推荐系统的命令行接口，用于运行整个推荐流程。
"""

import os
import sys
from dotenv import load_dotenv

from paper_recommender import PaperRecommender
from email_formatter import EmailFormatter
from time_updater_mcp import get_time_via_llm_tool


def load_description_from_file(description_path: str) -> str:
    """从文件加载研究描述。"""
    try:
        with open(description_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"描述文件未找到: {description_path}")
        sys.exit(1)
    except Exception as error:
        print(f"读取描述文件时出错: {error}")
        sys.exit(1)

import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """主入口点。"""
    logging.info("程序开始执行。")
    load_dotenv()
    logging.info("环境变量已加载。")

    try:
        # 从环境变量加载配置
        api_key = os.getenv("QWEN_API_KEY")
        base_url = os.getenv("QWEN_BASE_URL")
        model = os.getenv("QWEN_MODEL")
        categories = os.getenv("CATEGORIES", "cs.CV").split(',')
        max_entries = int(os.getenv("MAX_ENTRIES", 5))
        max_paper_num = int(os.getenv("MAX_PAPER_NUM", 5))
        temperature = float(os.getenv("TEMPERATURE", 0.7))
        num_workers = int(os.getenv("NUM_WORKERS", 4))
        save_dir = os.getenv("SAVE_DIR", "./arxiv_history")
        description_path = os.getenv("DESCRIPTION_PATH", "personal_research_interests.md")
        save_to_markdown = os.getenv("SAVE_TO_MARKDOWN", "true").lower() == "true"

        # 加载邮件配置
        send_email = os.getenv("SEND_EMAIL", "false").lower() == "true"
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", 465))
        smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
        smtp_use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from_email = os.getenv("SMTP_FROM_EMAIL")
        smtp_to_email = os.getenv("SMTP_TO_EMAIL")

        # 加载研究描述
        logging.info("正在加载研究描述...")
        description = load_description_from_file(description_path)
        logging.info("研究描述加载成功。")

        # 设置保存目录
        if save_to_markdown:
            os.makedirs(save_dir, exist_ok=True)
        else:
            save_dir = None

        # 初始化推荐器
        logging.info("正在初始化论文推荐器...")
        recommender = PaperRecommender(
            categories=categories,
            max_entries=max_entries,
            max_paper_num=max_paper_num,
            model=model,
            base_url=base_url,
            api_key=api_key,
            description=description,
            num_workers=num_workers,
            temperature=temperature,
            save_dir=save_dir,
        )
        logging.info("论文推荐器初始化成功。")

        # 获取当前时间
        logging.info("正在通过LLM获取当前时间...")
        current_time = get_time_via_llm_tool()
        if not current_time or "失败" in current_time:
            logging.warning("通过LLM获取时间失败，将使用本地时间。")
            from datetime import datetime
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.info(f"获取到时间: {current_time}")

        # 运行推荐流程
        logging.info("开始运行论文推荐流程...")
        summary_html = recommender.run(current_time)
        logging.info("论文推荐流程结束。")

        # 发送邮件
        logging.info("检查是否需要发送邮件...")
        if send_email and summary_html:
            logging.info("检测到需要发送邮件，正在准备发送...")
            email_formatter = EmailFormatter()
            email_formatter.send_email(
                sender=smtp_from_email,
                receiver=smtp_to_email,
                password=smtp_password,
                smtp_server=smtp_host,
                smtp_port=smtp_port,
                html_content=summary_html,
                subject_prefix="ArXiv Daily Digest",
                use_ssl=smtp_use_ssl,
                use_tls=smtp_use_tls
            )
            logging.info("邮件发送成功。")
        elif not send_email:
            logging.info("邮件发送功能未开启。")
        else:
            logging.warning("没有生成推荐内容，跳过邮件发送。")

        if save_to_markdown and save_dir:
            logging.info(f"推荐报告已保存到目录: {save_dir}")

    except KeyboardInterrupt:
        logging.info("用户取消了操作")
        sys.exit(0)
    except Exception as error:
        logging.error(f"程序执行过程中发生未捕获的错误: {error}", exc_info=True)
        sys.exit(1)
    finally:
        logging.info("程序执行完毕。")


if __name__ == "__main__":
    main()