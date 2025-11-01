"""推荐引擎模块

提供论文推荐的核心功能，包括从ArXiv获取论文、使用LLM评估相关性、生成推荐报告等。
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .arxiv_fetcher import ArxivFetcher
from .llm_provider import LLMProvider, create_light_llm_provider


class RecommendationEngine:
    """论文推荐引擎，负责获取、评估和推荐ArXiv论文。"""

    def __init__(
        self,
        categories: List[str],
        max_entries: int,
        num_detailed_papers: int,
        num_brief_papers: int,
        model: str,
        base_url: str,
        api_key: str,
        description: str,
        username: str = "TEST",
        num_workers: int = 2,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 4000,
        arxiv_fetcher: Optional[ArxivFetcher] = None,
        llm_provider: Optional[LLMProvider] = None,
        light_llm_provider: Optional[LLMProvider] = None,
    ):
        """初始化推荐引擎。
        
        Args:
            categories: ArXiv分类列表
            max_entries: 每个分类获取的最大论文数
            num_detailed_papers: 详细分析的论文数
            num_brief_papers: 简要分析的论文数
            model: LLM模型名称
            base_url: LLM API基础URL
            api_key: LLM API密钥
            description: 研究兴趣描述
            username: 用户名，用于生成报告时的署名
            num_workers: 并行处理线程数
            temperature: LLM生成温度
            top_p: LLM top_p参数
            max_tokens: LLM最大token数
        """
        logger.info("推荐引擎初始化开始")
        self.categories = categories
        self.max_entries = max_entries
        self.num_detailed_papers = num_detailed_papers
        self.num_brief_papers = num_brief_papers
        self.description = description
        self.num_workers = num_workers
        
        # 初始化ArXiv获取器和LLM提供商（支持依赖注入，减少重复构造与耦合）
        logger.debug("初始化ArXiv获取器和LLM提供商")
        self.arxiv_fetcher = arxiv_fetcher or ArxivFetcher()

        # 主LLM提供者（用于详细分析和报告生成）
        self.llm_provider = llm_provider or LLMProvider(
            model=model,
            base_url=base_url,
            api_key=api_key,
            description=description,
            username=username,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

        # 轻量模型提供者（用于论文相关性评估）
        self.light_llm_provider = light_llm_provider or create_light_llm_provider(
            description=description,
            username=username,
        )
        
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        
        logger.success(f"推荐引擎初始化完成 - 分类: {categories}, 详细分析: {num_detailed_papers}, 简要分析: {num_brief_papers}")

    def _fetch_papers_from_categories(self, date: str = None) -> List[Dict[str, Any]]:
        """从所有指定分类中获取论文。
        
        Args:
            date: 指定日期，格式为YYYY-MM-DD，如果为None则获取最新论文
        """
        logger.info(f"论文获取开始 - {len(self.categories)} 个分类")
        all_papers = []
        
        def fetch_category_papers(category: str) -> List[Dict[str, Any]]:
            """获取单个分类的论文。"""
            logger.debug(f"获取分类 {category} 的论文")
            if date:
                # 使用基于日期的分页获取
                papers = self.arxiv_fetcher.fetch_papers_paged(
                    category.strip(), 
                    date, 
                    per_page=min(self.max_entries, 200), 
                    max_pages=5,
                    max_total=self.max_entries
                )
                logger.debug(f"分类 {category} ({date}): {len(papers)} 篇论文")
            else:
                # 使用原有的获取方式
                papers = self.arxiv_fetcher.fetch_papers(category.strip(), self.max_entries)
                logger.debug(f"分类 {category}: {len(papers)} 篇论文")
            return papers

        # 使用线程池并行获取不同分类的论文
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            future_to_category = {
                executor.submit(fetch_category_papers, category): category
                for category in self.categories
            }
            
            for future in as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    papers = future.result()
                    all_papers.extend(papers)
                except Exception as exc:
                    logger.error(f"分类 {category} 获取失败: {exc}")

        logger.success(f"论文获取完成 - 总计: {len(all_papers)} 篇")
        return all_papers

    def _process_single_paper(self, paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理单篇论文，包含重试机制。"""
        max_retries = 2  # 减少重试次数
        title_short = paper['title'][:50] + '...' if len(paper['title']) > 50 else paper['title']
        
        for attempt in range(max_retries):
            try:
                # 添加请求间隔，避免API限流
                time.sleep(0.1)  # 每篇论文评估前等待0.5秒
                
                # 直接调用轻量模型进行相关性评估（内联，去除额外间接层）
                evaluation = self.light_llm_provider.evaluate_paper_relevance(
                    paper, self.description, temperature=None
                )
                
                # 合并论文信息和评估结果
                result = {
                    **paper,
                    **evaluation
                }
                
                logger.debug(f"论文评估完成 - {title_short} (评分: {evaluation['relevance_score']})")
                return result
                
            except Exception as e:
                logger.warning(f"论文评估失败 ({attempt + 1}/{max_retries}) - {title_short}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"论文评估彻底失败，跳过 - {title_short}")
                    # 当API调用失败时，返回一个标记以便上层处理
                    return {"__api_failed": True, "title": paper['title']}
                
                # 指数退避重试
                wait_time = (attempt + 1) * 2
                logger.debug(f"等待 {wait_time} 秒后重试")
                time.sleep(wait_time)
        
        return None

    def get_recommendations(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取论文推荐列表。"""
        logger.info(f"相关性评估开始 - 待评估: {len(papers)} 篇")
        
        recommended_papers = []
        api_failure_count = 0
        max_failures = 5  # 最大允许失败次数
        
        # 使用线程池并行处理论文，降低并发数
        max_concurrent = min(self.num_workers, 2)  # 最多2个并发线程
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_paper = {
                executor.submit(self._process_single_paper, paper): paper
                for paper in papers
            }
            
            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                try:
                    result = future.result()
                    if result:
                        # 检查API失败标记
                        if result.get("__api_failed"):
                            api_failure_count += 1
                            if api_failure_count >= max_failures:
                                logger.error(f"检测到API调用失败达到上限({max_failures})，终止评估流程")
                                raise Exception("API调用失败，终止流程")
                        else:
                            recommended_papers.append(result)
                except Exception as exc:
                    title_short = paper['title'][:50] + '...' if len(paper['title']) > 50 else paper['title']
                    logger.error(f"论文处理异常 - {title_short}: {exc}")
                    if "API调用失败" in str(exc):
                        raise  # 重新抛出API失败异常

        # 过滤掉相关性评分低于6分的论文和API失败标记
        recommended_papers = [paper for paper in recommended_papers 
                          if paper.get('relevance_score', 0) >= 0 and not paper.get("__api_failed")]
        
        # 按相关性评分排序
        recommended_papers.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # 限制推荐数量（详细分析数 + 简要分析数）
        max_total_papers = self.num_detailed_papers + self.num_brief_papers
        recommended_papers = recommended_papers[:max_total_papers]
        
        if api_failure_count > 0:
            logger.warning(f"相关性评估完成 - 成功: {len(recommended_papers)} 篇, API失败: {api_failure_count} 篇")
        else:
            logger.success(f"相关性评估完成 - 推荐论文: {len(recommended_papers)} 篇")
        return recommended_papers



    # 移除未使用的 summarize 包装方法：直接使用 llm_provider.generate_summary_report

    def _process_single_paper_analysis(self, paper: Dict[str, Any]) -> str:
        """处理单篇论文的详细分析。"""
        title_short = paper['title'][:50] + '...' if len(paper['title']) > 50 else paper['title']
        try:
            logger.debug(f"获取PDF全文 - {title_short}")
            full_text = self.arxiv_fetcher.fetch_pdf_text(paper['pdf_url'])
            
            if "下载PDF失败" in full_text or "处理PDF失败" in full_text:
                logger.warning(f"PDF获取失败，跳过详细分析 - {title_short}")
                return f"\n## {paper['title']}\n- **分析失败**: {full_text}\n"

            paper_with_full_text = {**paper, "full_text": full_text}
            
            logger.debug(f"生成详细分析 - {title_short}")
            analysis = self.llm_provider.generate_detailed_paper_analysis(paper_with_full_text)
            logger.debug(f"详细分析完成 - {title_short}")
            return analysis
            
        except Exception as e:
            logger.error(f"详细分析异常 - {title_short}: {e}")
            return f"\n## {paper['title']}\n- **分析失败**: {e}\n"

    def _generate_detailed_analysis(self, papers: List[Dict[str, Any]]) -> str:
        """为评分最高的几篇论文生成详细分析。"""
        if not papers or self.num_detailed_papers == 0:
            logger.debug("跳过详细分析 - 无论文或配置为0")
            return ""

        logger.info(f"详细分析开始 - 前 {self.num_detailed_papers} 篇论文")
        
        detailed_papers = papers[:self.num_detailed_papers]
        analysis_results = ["\n\n---\n\n# 📚 详细论文列表\n"]

        # 使用线程池并行处理每篇论文
        with ThreadPoolExecutor(max_workers=min(self.num_workers, len(detailed_papers))) as executor:
            # 提交所有论文处理任务，保持顺序
            futures = [executor.submit(self._process_single_paper_analysis, paper) 
                      for paper in detailed_papers]
            
            # 按原始顺序收集结果，保持论文按相关性评分排序
            for i, future in enumerate(futures):
                paper = detailed_papers[i]
                title_short = paper['title'][:50] + '...' if len(paper['title']) > 50 else paper['title']
                try:
                    analysis = future.result()
                    analysis_results.append(analysis)
                    # 在每篇论文之间添加分隔线（除了最后一篇）
                    if i < len(futures) - 1:
                        analysis_results.append("\n---\n")
                    logger.debug(f"详细分析完成 - {title_short}")
                except Exception as e:
                    logger.error(f"详细分析任务失败 - {title_short}: {e}")
                    analysis_results.append(f"\n## {paper['title']}\n- **分析失败**: 任务执行异常: {e}\n")
                    # 在每篇论文之间添加分隔线（除了最后一篇）
                    if i < len(futures) - 1:
                        analysis_results.append("\n---\n")

        logger.success(f"详细分析完成 - {len(detailed_papers)} 篇")
        return "\n".join(analysis_results)

    def _generate_brief_analysis(self, papers: List[Dict[str, Any]]) -> str:
        """为第num_detailed_papers+1到第8篇论文生成简要分析（基于摘要的TLDR）。"""
        if not papers or len(papers) <= self.num_detailed_papers:
            return ""
        
        # 获取需要简要分析的论文（第num_detailed_papers+1到第num_detailed_papers+num_brief_papers篇）
        start_idx = self.num_detailed_papers
        end_idx = min(self.num_detailed_papers + self.num_brief_papers, len(papers))
        brief_papers = papers[start_idx:end_idx]
        
        if not brief_papers:
            return ""
        
        logger.info(f"简要分析开始 - 第 {start_idx+1} 到第 {end_idx} 篇论文")
        
        brief_results = ["\n\n---\n\n# 📝 简要论文列表\n"]
        
        for i, paper in enumerate(brief_papers, start=start_idx+1):
            try:
                # 使用LLM提供商生成简要总结
                tldr = self.llm_provider.generate_brief_analysis(paper, temperature=None)
                
                # 格式化输出
                brief_analysis = f"""
## {i}. {paper['title']}
- **相关性评分**: {'⭐' * min(int(paper['relevance_score']), 5)} ({paper['relevance_score']}/10)
- **ArXiv ID**: {paper['arXiv_id']}
- **作者**: {', '.join(paper['authors'])}
- **论文链接**: <a href="{paper['pdf_url']}" class="link-btn pdf-link" target="_blank">PDF</a> <a href="{paper['abstract_url']}" class="link-btn arxiv-link" target="_blank">ArXiv</a>
- **TLDR**: {tldr.strip()}
""".strip()
                
                brief_results.append(brief_analysis)
                
                # 在每篇论文之间添加分隔线（除了最后一篇）
                if i < end_idx:
                    brief_results.append("\n---\n")
                    
                title_short = paper['title'][:50] + '...' if len(paper['title']) > 50 else paper['title']
                logger.debug(f"简要分析完成 - {title_short}")
                
            except Exception as e:
                title_short = paper['title'][:50] + '...' if len(paper['title']) > 50 else paper['title']
                logger.error(f"简要分析失败 - {title_short}: {e}")
                brief_analysis = f"""
## {i}. {paper['title']}
- **相关性评分**: {'⭐' * min(int(paper['relevance_score']), 5)} ({paper['relevance_score']}/10)
- **ArXiv ID**: {paper['arXiv_id']}
- **作者**: {', '.join(paper['authors'])}
- **TLDR**: 生成摘要失败
- **论文链接**: <a href="{paper['pdf_url']}" class="link-btn pdf-link" target="_blank">PDF</a> <a href="{paper['abstract_url']}" class="link-btn arxiv-link" target="_blank">ArXiv</a>
""".strip()
                brief_results.append(brief_analysis)
                
                # 在每篇论文之间添加分隔线（除了最后一篇）
                if i < end_idx:
                    brief_results.append("\n---\n")
        
        logger.success(f"简要分析完成 - {len(brief_papers)} 篇")
        return "\n".join(brief_results)

    def run(self, current_time: str, date: str = None) -> Optional[Dict[str, str]]:
        """运行完整的推荐流程。
        
        Args:
            current_time: 当前时间字符串
            date: 指定日期，格式为YYYY-MM-DD，如果为None则获取最新论文
            
        Returns:
            包含summary和detailed_analysis的字典，如果没有推荐则返回None
        """
        logger.info("推荐引擎流程开始")
        
        # 1. 获取论文
        papers = self._fetch_papers_from_categories(date)
        if not papers:
            logger.warning("论文获取失败 - 未获取到任何论文，流程终止")
            return None

        # 2. 获取推荐
        recommended_papers = self.get_recommendations(papers)
        if not recommended_papers:
            logger.warning("推荐生成失败 - 未找到相关论文，流程终止")
            return None
        
        # 3. 使用多线程并发执行总结生成、详细分析和简要分析
        logger.info("内容生成开始 - 并发执行总结、详细分析和简要分析")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 提交三个任务到线程池（直接使用llm_provider生成总结报告，移除无用包装）
            summary_future = executor.submit(self.llm_provider.generate_summary_report, recommended_papers, current_time)
            analysis_future = executor.submit(self._generate_detailed_analysis, recommended_papers)
            brief_future = executor.submit(self._generate_brief_analysis, recommended_papers)
            
            # 等待三个任务完成并获取结果
            markdown_summary = summary_future.result()
            logger.debug("Markdown总结报告生成完成")
            
            detailed_analysis = analysis_future.result()
            logger.debug("详细分析生成完成")
            
            brief_analysis = brief_future.result()
            logger.debug("简要分析生成完成")
        
        # 4. 返回分离的内容而不是合并，同时包含papers数据
        result = {
            'summary': markdown_summary,
            'detailed_analysis': detailed_analysis,
            'brief_analysis': brief_analysis,
            'papers': recommended_papers  # 添加papers数据用于统计
        }
        
        logger.success("推荐引擎流程完成")
        return result


def main():
    """独立测试函数。"""
    import os
    from dotenv import load_dotenv
    
    # 加载环境变量
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    
    # 从环境变量获取配置
    api_key = os.getenv("DASHSCOPE_API_KEY")
    base_url = os.getenv("DASHSCOPE_BASE_URL")
    model = os.getenv("QWEN_MODEL")
    
    if not all([api_key, base_url, model]):
        logger.error("错误：请确保设置了DASHSCOPE_API_KEY、DASHSCOPE_BASE_URL和QWEN_MODEL环境变量")
        return
    
    # 读取研究兴趣描述
    description_path = os.getenv("USER_CATEGORIES_FILE", "data/users/user_categories.json")
    try:
        import json
        with open(description_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 获取第一个用户的user_input
        if isinstance(data, list) and len(data) > 0:
            first_user = data[0]
            if isinstance(first_user, dict) and 'user_input' in first_user:
                description = first_user['user_input']
            else:
                logger.error(f"JSON文件格式不正确，缺少user_input字段: {description_path}")
                return
        else:
            logger.error(f"JSON文件为空或格式不正确: {description_path}")
            return
    except FileNotFoundError:
        logger.error(f"未找到用户分类文件: {description_path}")
        return
    except json.JSONDecodeError as e:
        logger.error(f"JSON文件解析失败: {e}")
        return
    
    # 初始化推荐引擎
    categories = os.getenv("ARXIV_CATEGORIES", "cs.CL,cs.IR,cs.LG").split(',')
    max_entries = int(os.getenv("MAX_ENTRIES", "50"))
    num_detailed_papers = int(os.getenv("NUM_DETAILED_PAPERS", "3"))
    num_brief_papers = int(os.getenv("NUM_BRIEF_PAPERS", "7"))
    temperature = float(os.getenv("QWEN_MODEL_TEMPERATURE", "0.7"))
    top_p = float(os.getenv("QWEN_MODEL_TOP_P", "0.9"))
    max_tokens = int(os.getenv("QWEN_MODEL_MAX_TOKENS", "4000"))
    
    engine = RecommendationEngine(
        categories=categories,
        max_entries=max_entries,
        num_detailed_papers=num_detailed_papers,
        num_brief_papers=num_brief_papers,
        model=model,
        base_url=base_url,
        api_key=api_key,
        description=description,
        num_workers=int(os.getenv("MAX_WORKERS", "2")),
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens
    )
    
    # 运行推荐流程
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result = engine.run(current_time)
    
    if result:
        logger.success("推荐流程执行成功")
        logger.debug(f"生成的HTML内容长度: {len(result)} 字符")
    else:
        logger.warning("推荐流程未生成内容")


if __name__ == "__main__":
    main()