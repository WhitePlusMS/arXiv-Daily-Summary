import requests
from typing import List, Dict, Any, Union, Optional
import feedparser
import fitz  # PyMuPDF
import io
import time
import json
from loguru import logger
from datetime import datetime, timedelta
import pytz
import xml.etree.ElementTree as ET

class ArxivFetcher:
    def __init__(self, base_url: str = "http://export.arxiv.org/api/query", retries: int = 3, delay: int = 5):
        logger.info(f"ArxivFetcher初始化开始")
        self.base_url = base_url
        self.retries = retries
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArXiv-Daily-Recommender/2.0'
        })
        logger.success(f"ArxivFetcher初始化完成 - URL: {base_url}, 重试: {retries}次, 延迟: {delay}秒")

    def fetch_pdf_text(self, pdf_url: str) -> str:
        if not pdf_url:
            logger.warning("PDF获取跳过 - URL为空")
            return "PDF URL不可用。"
        
        logger.debug(f"PDF获取开始 - {pdf_url}")
        try:
            pdf_response = self.session.get(pdf_url, timeout=30)
            pdf_response.raise_for_status()
            pdf_bytes = io.BytesIO(pdf_response.content)
            logger.debug(f"PDF下载完成 - 大小: {len(pdf_response.content)} 字节")
            
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

    def _parse_api_entry(self, entry) -> Dict[str, Any]:
        try:
            arxiv_id = entry.id.split('/abs/')[-1]
            
            pdf_url = ""
            abs_url = ""
            for link in entry.links:
                if link.rel == "alternate":
                    abs_url = link.href
                elif getattr(link, "title", "") == "pdf":
                    pdf_url = link.href
            
            title = entry.title.strip().replace('\n', ' ')
            abstract = entry.summary.strip().replace('\n', ' ')
            comments = entry.get("arxiv_comment", "无评论信息")
            authors = [author.name for author in entry.authors] if hasattr(entry, "authors") else []
            published = entry.published
            
            title_short = title[:50] + '...' if len(title) > 50 else title
            logger.debug(f"论文解析完成 - {arxiv_id}: {title_short}")
            return {
                "title": title,
                "arXiv_id": arxiv_id,
                "abstract": abstract,
                "comments": comments,
                "pdf_url": pdf_url,
                "abstract_url": abs_url,
                "authors": authors,
                "published": published,
                "full_text": "",
            }
        except Exception as error:
            logger.error(f"论文解析失败: {error}")
            return {
                "title": "解析错误",
                "arXiv_id": "unknown",
                "abstract": f"解析论文失败: {error}",
                "comments": "",
                "pdf_url": "",
                "abstract_url": "",
                "authors": [],
                "published": "",
                "full_text": "",
            }

    def fetch_papers(self, category: str, max_results: int = 100) -> List[Dict[str, Any]]:
        logger.info(f"论文获取开始 - 分类: {category}, 最大数量: {max_results}")
        query = f"cat:{category}"
        url = f"{self.base_url}?search_query={query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        logger.debug(f"API请求URL: {url}")
        
        for attempt in range(self.retries):
            try:
                logger.debug(f"尝试获取论文 ({attempt + 1}/{self.retries})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                feed = feedparser.parse(response.text)
                papers = [self._parse_api_entry(entry) for entry in feed.entries]
                logger.success(f"论文获取完成 - {category}: {len(papers)} 篇")
                return papers
            except requests.RequestException as error:
                logger.warning(f"论文获取失败 ({attempt + 1}/{self.retries}) - {category}: {error}")
                if attempt < self.retries - 1:
                    logger.debug(f"等待 {self.delay} 秒后重试")
                    time.sleep(self.delay)
                else:
                    logger.error(f"论文获取彻底失败 - {category}: 所有 {self.retries} 次尝试均失败")
                    return []
        return []

    def fetch_papers_paged(self, category: str, date: str, per_page: int = 200, max_pages: int = 5) -> List[Dict[str, Any]]:
        """分页 + 日期过滤（按北京时区）"""
        logger.info(f"分页获取开始 - 分类: {category}, 日期: {date}, 每页: {per_page}, 最大页数: {max_pages}")
        
        # 将输入日期转换为北京时区的开始和结束时间
        beijing_tz = pytz.timezone('Asia/Shanghai')
        utc_tz = pytz.UTC
        
        # 北京时区的日期开始时间（00:00:00）
        beijing_start = beijing_tz.localize(datetime.strptime(date, "%Y-%m-%d"))
        # 北京时区的日期结束时间（23:59:59）
        beijing_end = beijing_start + timedelta(days=1) - timedelta(seconds=1)
        
        # 转换为UTC时间用于arXiv API查询
        utc_start = beijing_start.astimezone(utc_tz)
        utc_end = beijing_end.astimezone(utc_tz)
        
        # 格式化为arXiv API需要的格式
        start_date_str = utc_start.strftime("%Y%m%d%H%M")
        end_date_str = utc_end.strftime("%Y%m%d%H%M")
        
        logger.debug(f"时区转换完成 - 北京: {beijing_start.strftime('%Y-%m-%d %H:%M')} ~ {beijing_end.strftime('%Y-%m-%d %H:%M')}")
        logger.debug(f"API查询范围 - UTC: {start_date_str} ~ {end_date_str}")
        
        all_papers = []
        for page in range(max_pages):
            start = page * per_page
            query = f"cat:{category}+AND+submittedDate:[{start_date_str}+TO+{end_date_str}]"
            url = f"{self.base_url}?search_query={query}&start={start}&max_results={per_page}&sortBy=submittedDate&sortOrder=ascending"
            logger.debug(f"获取第 {page+1} 页 - 起始位置: {start}")
            logger.debug(f"查询条件: {query}")
            
            # 使用指数退避重试机制处理每一页的请求
            page_papers = self._fetch_page_with_retry(url, page + 1)
            if page_papers is None:
                logger.warning(f"第 {page+1} 页获取失败，跳过该页继续处理")
                continue
            
            if not page_papers:
                logger.info(f"分页结束 - 第 {page+1} 页无更多条目")
                break
                
            all_papers.extend(page_papers)
            logger.debug(f"第 {page+1} 页完成 - 获取: {len(page_papers)} 篇")
            
            if len(page_papers) < per_page:
                logger.info(f"分页结束 - 第 {page+1} 页返回数量少于请求数")
                break
            
            if page < max_pages - 1:  # 不是最后一页才等待
                logger.debug(f"等待 {self.delay} 秒后获取下一页")
                time.sleep(self.delay)
            
        logger.success(f"分页获取完成 - {category}: 总计 {len(all_papers)} 篇论文")
        return all_papers
    
    def _fetch_page_with_retry(self, url: str, page_num: int, max_retries: int = 5) -> Optional[List[Dict[str, Any]]]:
        """使用指数退避重试机制获取单页数据"""
        for attempt in range(max_retries):
            try:
                # 指数退避延迟：1, 2, 4, 8, 16秒
                if attempt > 0:
                    delay = min(2 ** (attempt - 1), 30)  # 最大延迟30秒
                    logger.info(f"第 {page_num} 页重试 ({attempt + 1}/{max_retries}) - 等待 {delay} 秒")
                    time.sleep(delay)
                
                logger.debug(f"第 {page_num} 页请求尝试 ({attempt + 1}/{max_retries}) - URL: {url}")
                resp = self.session.get(url, timeout=30)
                
                # 详细的状态码检查和错误处理
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    page_papers = [self._parse_api_entry(e) for e in feed.entries]
                    logger.debug(f"第 {page_num} 页请求成功 - 状态码: {resp.status_code}, 获取: {len(page_papers)} 篇")
                    return page_papers
                elif resp.status_code in [502, 503, 504]:  # 服务器临时性错误
                    logger.warning(f"第 {page_num} 页服务器临时错误 - 状态码: {resp.status_code}, 尝试重试")
                    continue
                elif resp.status_code == 429:  # 请求过于频繁
                    logger.warning(f"第 {page_num} 页请求频率限制 - 状态码: {resp.status_code}, 延长等待时间")
                    time.sleep(10)  # 额外等待10秒
                    continue
                else:
                    logger.error(f"第 {page_num} 页请求失败 - 状态码: {resp.status_code}, 响应: {resp.text[:200]}")
                    resp.raise_for_status()
                    
            except requests.exceptions.Timeout as e:
                logger.warning(f"第 {page_num} 页请求超时 ({attempt + 1}/{max_retries}): {e}")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"第 {page_num} 页连接错误 ({attempt + 1}/{max_retries}): {e}")
            except requests.exceptions.HTTPError as e:
                logger.error(f"第 {page_num} 页HTTP错误 ({attempt + 1}/{max_retries}): {e}")
                # 对于4xx错误，不进行重试
                if 400 <= resp.status_code < 500 and resp.status_code not in [429]:
                    logger.error(f"第 {page_num} 页客户端错误，停止重试 - 状态码: {resp.status_code}")
                    break
            except Exception as e:
                logger.error(f"第 {page_num} 页未知错误 ({attempt + 1}/{max_retries}): {e}")
        
        logger.error(f"第 {page_num} 页获取彻底失败 - 所有 {max_retries} 次尝试均失败")
        return None

def save_to_json(data, filename):
    logger.debug(f"JSON保存开始 - {filename}")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"JSON保存完成 - {filename}")
    except Exception as e:
        logger.error(f"JSON保存失败 - {filename}: {e}")
        raise


def main2(date: str):
    logger.info(f"main2函数启动 - 日期分页获取: {date}")
    fetcher = ArxivFetcher()
    papers = fetcher.fetch_papers_paged("cs.CV", date, per_page=3, max_pages=1)
    save_to_json(papers, "papers_main2.json")
    logger.success("main2函数执行完成")





if __name__ == "__main__":
    date = '2024-08-06'
    main2(date)

