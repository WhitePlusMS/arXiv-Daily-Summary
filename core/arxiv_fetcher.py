import requests
from typing import List, Dict, Any, Union, Optional
import feedparser
import time
import json
from loguru import logger
from datetime import datetime, timedelta
import pytz
import xml.etree.ElementTree as ET
import urllib.parse
from core.common_utils import run_with_retries, write_json, make_on_retry_logger
from core.env_config import get_int, get_str

class ArxivFetcher:
    def __init__(self, base_url: Optional[str] = None, retries: Optional[int] = None, delay: Optional[int] = None):
        """初始化ArXiv获取器
        
        Args:
            base_url: ArXiv API基础URL，如果为None则从环境变量ARXIV_BASE_URL读取，默认值为"http://export.arxiv.org/api/query"
            retries: 重试次数，如果为None则从环境变量ARXIV_RETRIES读取，默认值为3
            delay: 请求延迟（秒），如果为None则从环境变量ARXIV_DELAY读取，默认值为5
        """
        logger.info(f"ArxivFetcher初始化开始")
        
        # 从环境变量读取配置，如果参数传入则优先使用参数值
        self.base_url = base_url or get_str('ARXIV_BASE_URL', 'http://export.arxiv.org/api/query')
        self.retries = retries if retries is not None else get_int('ARXIV_RETRIES', 3)
        self.delay = delay if delay is not None else get_int('ARXIV_DELAY', 5)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArXiv-Daily-Recommender/2.0'
        })
        logger.success(f"ArxivFetcher初始化完成 - URL: {self.base_url}, 重试: {self.retries}次, 延迟: {self.delay}秒")

    

    def _parse_api_entry(self, entry, category: str = None) -> Dict[str, Any]:
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

            # 解析分类标签（不影响现有输出字段）
            categories = []
            primary_category = None
            try:
                if hasattr(entry, "tags") and entry.tags:
                    for tag in entry.tags:
                        term = getattr(tag, "term", None) or (tag.get("term") if isinstance(tag, dict) else None)
                        if term:
                            categories.append(term)
                    if categories:
                        primary_category = categories[0]
            except Exception:
                # 保持稳健：标签解析失败时忽略，不影响现有行为
                categories = []
                primary_category = None
            
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
                "category": category,  # 添加分类信息
                "categories": categories,  # 新增：全部分类标签（仅扩展，未更改现有逻辑）
                "primary_category": primary_category,  # 新增：主分类（首个标签）
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
                "category": category,
                "categories": [],
                "primary_category": None,
            }

    def fetch_papers(self, category: str, max_results: int = 100, sort_by: str = "lastUpdatedDate") -> List[Dict[str, Any]]:
        logger.info(f"论文获取开始 - 分类: {category}, 最大数量: {max_results}, 排序方式: {sort_by}")
        query = f"cat:{category}"
        url = f"{self.base_url}?search_query={query}&start=0&max_results={max_results}&sortBy={sort_by}&sortOrder=descending"
        logger.debug(f"API请求URL: {url}")
        
        def _do_request():
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            papers = [self._parse_api_entry(entry, category) for entry in feed.entries]
            return papers

        _on_retry = make_on_retry_logger("论文获取", category, self.retries, self.delay)

        try:
            papers = run_with_retries(_do_request, self.retries, self.delay, _on_retry)
            logger.success(f"论文获取完成 - {category}: {len(papers)} 篇")
            return papers
        except Exception:
            logger.error(f"论文获取彻底失败 - {category}: 所有 {self.retries} 次尝试均失败")
            return []

    def fetch_papers_by_query(self, search_query: str, max_results: int = 100, sort_by: str = "relevance") -> List[Dict[str, Any]]:
        """
        根据给定的复杂搜索查询从ArXiv API获取论文。

        :param search_query: 完整的ArXiv搜索查询字符串 (例如, "cat:cs.AI AND submittedDate:[20230101 TO 20231231]")
        :param max_results: 返回的最大结果数
        :param sort_by: 排序方式 ('relevance', 'lastUpdatedDate', 'submittedDate')
        :return: 论文信息字典的列表
        """
        logger.info(f"复杂查询开始 - 查询: '{search_query}', 最大数量: {max_results}, 排序方式: {sort_by}")
        
        encoded_query = urllib.parse.quote(search_query)
        
        url = f"{self.base_url}?search_query={encoded_query}&start=0&max_results={max_results}&sortBy={sort_by}&sortOrder=descending"
        logger.debug(f"API请求URL: {url}")

        def _do_request():
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            papers = [self._parse_api_entry(entry, None) for entry in feed.entries]
            return papers

        # 使用统一的 on_retry 回调模板，保持日志语义与内容完全一致
        _on_retry = make_on_retry_logger("复杂查询", f"'{search_query}'", self.retries, self.delay)

        try:
            papers = run_with_retries(_do_request, self.retries, self.delay, _on_retry)
            logger.success(f"复杂查询完成 - '{search_query}': {len(papers)} 篇")
            return papers
        except Exception:
            logger.error(f"复杂查询彻底失败 - '{search_query}': 所有 {self.retries} 次尝试均失败")
            return []

    def fetch_papers_paged(self, category: str, date: str, per_page: int = 200, max_pages: int = 5, max_total: Optional[int] = None) -> List[Dict[str, Any]]:
        """分页 + 日期过滤（按北京时区）
        
        Args:
            category: arXiv 分类
            date: 目标日期（YYYY-MM-DD，按北京时区过滤）
            per_page: 每页请求数量
            max_pages: 最大分页页数
            max_total: 期望的最大返回数量（达到该数量后提前停止分页）
        """
        logger.info(f"分页获取开始 - 分类: {category}, 日期: {date}, 每页: {per_page}, 最大页数: {max_pages}, 目标总量: {max_total}")
        
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
        consecutive_failures = 0  # 连续失败计数
        max_consecutive_failures = 2  # 最大连续失败次数，超过则提前停止
        
        for page in range(max_pages):
            # 如果已达到或超过目标数量，提前结束
            if max_total is not None and len(all_papers) >= max_total:
                logger.info(f"分页提前结束 - 已满足目标总量: {len(all_papers)}/{max_total}")
                break
            
            # 本页实际请求数量不超过剩余所需
            if max_total is not None:
                remaining = max_total - len(all_papers)
                req_per_page = max(1, min(per_page, remaining))
            else:
                req_per_page = per_page
            
            start = page * per_page
            query = f"cat:{category}+AND+lastUpdatedDate:[{start_date_str}+TO+{end_date_str}]"
            url = f"{self.base_url}?search_query={query}&start={start}&max_results={req_per_page}&sortBy=lastUpdatedDate&sortOrder=ascending"
            logger.debug(f"获取第 {page+1} 页 - 起始位置: {start}，本页请求数量: {req_per_page}")
            logger.debug(f"查询条件: {query}")
            
            # 使用指数退避重试机制处理每一页的请求（使用实例配置的重试次数）
            page_papers = self._fetch_page_with_retry(url, page + 1, category, max_retries=self.retries)
            if page_papers is None:
                consecutive_failures += 1
                logger.warning(f"第 {page+1} 页获取失败，连续失败次数: {consecutive_failures}/{max_consecutive_failures}")
                
                # 如果第一页就失败，或者连续失败次数超过阈值，提前停止
                if page == 0 or consecutive_failures >= max_consecutive_failures:
                    logger.error(f"分页获取提前终止 - 连续 {consecutive_failures} 页失败，已获取: {len(all_papers)} 篇")
                    break
                continue
            
            # 成功获取到数据，重置连续失败计数
            consecutive_failures = 0
            
            if not page_papers:
                logger.info(f"分页结束 - 第 {page+1} 页无更多条目")
                break
                
            all_papers.extend(page_papers)
            logger.debug(f"第 {page+1} 页完成 - 获取: {len(page_papers)} 篇，累计: {len(all_papers)} 篇")

            # 达到目标数量后立即结束（不再 sleep）
            if max_total is not None and len(all_papers) >= max_total:
                logger.info(f"分页提前结束 - 已满足目标总量: {len(all_papers)}/{max_total}")
                break

            # 如果本页返回数量少于请求数量，说明后续无更多条目
            if len(page_papers) < req_per_page:
                logger.info(f"分页结束 - 第 {page+1} 页返回数量少于请求数")
                break

            if page < max_pages - 1:  # 不是最后一页才等待
                logger.debug(f"等待 {self.delay} 秒后获取下一页")
                time.sleep(self.delay)
            
        # 若超过目标数量，裁剪至目标数量
        if max_total is not None and len(all_papers) > max_total:
            all_papers = all_papers[:max_total]
        
        logger.success(f"分页获取完成 - {category}: 总计 {len(all_papers)} 篇论文")
        return all_papers
    
    def _fetch_page_with_retry(self, url: str, page_num: int, category: str = None, max_retries: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """使用指数退避重试机制获取单页数据
        
        Args:
            url: 请求URL
            page_num: 页码
            category: 分类（可选）
            max_retries: 最大重试次数，如果为None则使用实例的retries属性
        """
        # 如果没有传入max_retries，使用实例的retries属性
        if max_retries is None:
            max_retries = self.retries
        for attempt in range(max_retries):
            try:
                # 指数退避延迟：1, 2, 4秒（减少等待时间）
                if attempt > 0:
                    delay = min(2 ** (attempt - 1), 10)  # 最大延迟10秒
                    logger.info(f"第 {page_num} 页重试 ({attempt + 1}/{max_retries}) - 等待 {delay} 秒")
                    time.sleep(delay)
                
                logger.debug(f"第 {page_num} 页请求尝试 ({attempt + 1}/{max_retries}) - URL: {url}")
                resp = self.session.get(url, timeout=30)
                
                # 详细的状态码检查和错误处理
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    page_papers = [self._parse_api_entry(e, category) for e in feed.entries]
                    logger.debug(f"第 {page_num} 页请求成功 - 状态码: {resp.status_code}, 获取: {len(page_papers)} 篇")
                    return page_papers
                elif resp.status_code in [502, 503, 504]:  # 服务器临时性错误
                    logger.warning(f"第 {page_num} 页服务器临时错误 - 状态码: {resp.status_code}, 尝试重试")
                    continue
                elif resp.status_code == 429:  # 请求过于频繁
                    # 对于429错误，增加等待时间，但如果是最后一次尝试则直接返回None
                    wait_time = 20 if attempt < max_retries - 1 else 0
                    logger.warning(f"第 {page_num} 页请求频率限制 - 状态码: {resp.status_code}, 等待 {wait_time} 秒")
                    if wait_time > 0:
                        time.sleep(wait_time)
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
                # 对于4xx错误，不进行重试（从响应对象获取状态码）
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    if 400 <= status_code < 500 and status_code not in [429]:
                        logger.error(f"第 {page_num} 页客户端错误，停止重试 - 状态码: {status_code}")
                        break
            except Exception as e:
                logger.error(f"第 {page_num} 页未知错误 ({attempt + 1}/{max_retries}): {e}")
        
        logger.error(f"第 {page_num} 页获取彻底失败 - 所有 {max_retries} 次尝试均失败")
        return None

def save_to_json(data, filename):
    logger.debug(f"JSON保存开始 - {filename}")
    try:
        # 使用统一的JSON写入工具函数，参数与原实现一致
        write_json(filename, data, ensure_ascii=False, indent=2)
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

