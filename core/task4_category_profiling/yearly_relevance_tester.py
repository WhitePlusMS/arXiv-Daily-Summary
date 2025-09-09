import os
import sys
from datetime import datetime

# 动态添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from core.arxiv_fetcher import ArxivFetcher
from loguru import logger

def test_yearly_relevance(category: str, years: int = 10):
    """
    测试获取指定分类在过去几年中每年最相关的5篇论文。
    """
    logger.info(f"开始测试 - 分类: {category}, 年份: {years}")
    fetcher = ArxivFetcher()
    current_year = datetime.now().year

    for year in range(current_year - years + 1, current_year + 1):
        start_date = f"{year}0101"
        end_date = f"{year}1231"
        
        # 构建复杂的查询字符串
        query = f"cat:{category} AND submittedDate:[{start_date} TO {end_date}]"
        
        logger.info(f"正在查询年份: {year}, 查询语句: '{query}'")
        
        try:
            # 使用新的 fetch_papers_by_query 函数
            papers = fetcher.fetch_papers_by_query(
                search_query=query,
                max_results=5,
                sort_by="relevance"
            )
            
            if papers:
                logger.success(f"{year}年最相关的5篇论文:")
                for paper in papers:
                    logger.info(f"  - ID: {paper['arXiv_id']}, 标题: {paper['title']}")
            else:
                logger.warning(f"{year}年未找到相关论文。")
                
        except Exception as e:
            logger.error(f"查询 {year} 年的论文时出错: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    # 测试的分类
    TARGET_CATEGORY = "cs.AI" 
    test_yearly_relevance(TARGET_CATEGORY)