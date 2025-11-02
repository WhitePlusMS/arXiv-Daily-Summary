"""PDF 文本解析模块

负责下载论文 PDF 并提取纯文本内容，解耦 ArxivFetcher 的职责。
"""

import io
from typing import Optional

import fitz  # PyMuPDF
import requests
from loguru import logger


class PDFTextExtractor:
    """下载并解析 PDF 文本的工具类。"""

    def __init__(self, user_agent: str = 'ArXiv-Daily-Recommender/2.0', timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent
        })

    def extract_pdf_text(self, pdf_url: Optional[str]) -> str:
        """下载并提取 PDF 文本。

        Args:
            pdf_url: PDF 的 URL

        Returns:
            提取的纯文本；失败时返回中文错误提示以兼容原有逻辑。
        """
        if not pdf_url:
            logger.warning("PDF获取跳过 - URL为空")
            return "PDF URL不可用。"

        logger.debug(f"PDF获取开始 - {pdf_url}")
        try:
            response = self.session.get(pdf_url, timeout=self.timeout)
            response.raise_for_status()
            pdf_bytes = io.BytesIO(response.content)
            logger.debug(f"PDF下载完成 - 大小: {len(response.content)} 字节")

            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                text = "".join(page.get_text() for page in doc)
            logger.debug(f"PDF文本提取完成 - 长度: {len(text)} 字符")
            return text.strip()
        except requests.RequestException as e:
            logger.error(f"PDF下载失败 - {pdf_url}: {e}")
            return f"下载PDF失败: {e}"
        except Exception as e:
            logger.error(f"PDF处理失败 - {pdf_url}: {e}")
            return f"处理PDF失败: {e}"