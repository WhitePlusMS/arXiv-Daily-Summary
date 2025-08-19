"""
ArXiv客户端

提供使用arXiv官方API获取论文的功能。
"""

import requests
from typing import List, Dict, Any
import feedparser
import fitz  # PyMuPDF
import io

import time

class ArxivClient:
    """用于与ArXiv交互获取研究论文的客户端（通过官方API）。"""

    def __init__(self, base_url: str = "http://export.arxiv.org/api/query", retries: int = 3, delay: int = 5):
        self.base_url = base_url
        self.retries = retries
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArXiv-Daily-Recommender/1.0'
        })

    def _fetch_pdf_text(self, pdf_url: str) -> str:
        """从给定的URL获取PDF并提取其文本内容。"""
        if not pdf_url:
            return "PDF URL not available."
        try:
            pdf_response = self.session.get(pdf_url, timeout=30)
            pdf_response.raise_for_status()
            pdf_bytes = io.BytesIO(pdf_response.content)
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                text = "".join(page.get_text() for page in doc)
            return text.strip()
        except requests.RequestException as e:
            return f"Failed to download PDF: {e}"
        except Exception as e:
            return f"Failed to process PDF: {e}"

    def _parse_api_entry(self, entry) -> Dict[str, Any]:
        """解析arXiv API返回的单篇论文条目。"""
        try:
            arxiv_id = entry.id.split('/abs/')[-1]
            pdf_url = ""
            for link in entry.links:
                if link.rel == "alternate":
                    abs_url = link.href
                elif link.title == "pdf":
                    pdf_url = link.href
            title = entry.title.strip().replace('\n', ' ')
            abstract = entry.summary.strip().replace('\n', ' ')
            comments = entry.get("arxiv_comment", "No comments available")
            authors = [author.name for author in entry.authors] if hasattr(entry, "authors") else []
            published = entry.published
            full_text = self._fetch_pdf_text(pdf_url)
            return {
                "title": title,
                "arXiv_id": arxiv_id,
                "abstract": abstract,
                "comments": comments,
                "pdf_url": pdf_url,
                "abstract_url": abs_url,
                "authors": authors,
                "published": published,
                "full_text": full_text,
            }
        except Exception as error:
            return {
                "title": "Parse error",
                "arXiv_id": "unknown",
                "abstract": f"Failed to parse paper: {error}",
                "comments": "",
                "pdf_url": "",
                "abstract_url": "",
                "authors": [],
                "published": "",
                "full_text": "",
            }

    def fetch_papers(self, category: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        通过arXiv官方API从特定类别获取论文。

        参数:
            category: ArXiv类别 (例如: 'cs.CV', 'cs.LG')
            max_results: 要获取的最大论文数

        返回:
            论文字典列表
        """
        query = f"cat:{category}"
        url = f"{self.base_url}?search_query={query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        for attempt in range(self.retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                feed = feedparser.parse(response.text)
                papers = []
                for entry in feed.entries:
                    paper = self._parse_api_entry(entry)
                    papers.append(paper)
                return papers
            except requests.RequestException as error:
                print(f"Error fetching papers from {category} (attempt {attempt + 1}/{self.retries}): {error}")
                if attempt < self.retries - 1:
                    time.sleep(self.delay)
                else:
                    return []
            except Exception as error:
                print(f"Unexpected error fetching papers: {error}")
                return []
        return []

    def get_paper_count(self, category: str) -> int:
        """通过API获取类别中可用的论文数量。"""
        query = f"cat:{category}"
        url = f"{self.base_url}?search_query={query}&start=0&max_results=0"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            # arXiv API在feed.feed.opensearch_totalresults中返回总数
            return int(getattr(feed.feed, "opensearch_totalresults", 0))
        except Exception:
            return 0

if __name__ == "__main__":
    import tiktoken
    client = ArxivClient()
    papers = client.fetch_papers("cs.CV", 1)
    if papers:
        paper = papers[0]
        full_text = paper.get("full_text", "")
        if full_text and not full_text.startswith("Failed to"):
            # 使用tiktoken计算token数量，这里以gpt-3.5-turbo模型为例
            try:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                num_tokens = len(encoding.encode(full_text))
                print(f"Paper Title: {paper['title']}")
                print(f"The full text has approximately {num_tokens} tokens.")
            except Exception as e:
                print(f"Could not calculate tokens: {e}")
        else:
            print(f"Could not retrieve or process full text for: {paper['title']}")
            print(f"Reason: {full_text}")
    else:
        print("No papers fetched.")