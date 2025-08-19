import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Any

from tqdm import tqdm
# 加载.env文件（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from api_provider import OpenAIProvider
from arxiv_client import ArxivClient
import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Any
from tqdm import tqdm
from dotenv import load_dotenv
from api_provider import OpenAIProvider
from arxiv_client import ArxivClient



class PaperRecommender:
    """
    论文推荐系统主类
    
    从ArXiv获取论文，使用LLM评估相关性，并提供格式化的推荐。
    """
    
    def __init__(
        self,
        categories: List[str],
        max_entries: int,
        max_paper_num: int,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        description: str = "",
        num_workers: int = 4,
        temperature: float = 0.7,
        save_dir: Optional[str] = None,
    ):
        self.max_paper_num = max_paper_num
        self.save_dir = save_dir
        self.num_workers = num_workers
        self.temperature = temperature
        self.description = description
        
        # Initialize components
        self.arxiv_client = ArxivClient()
        self.llm_provider = self._initialize_llm_provider(model, base_url, api_key)
        
        # Fetch papers
        self.papers = self._fetch_papers_from_categories(categories, max_entries)
        
        # Thread safety
        self._lock = threading.Lock()
    
    def _initialize_llm_provider(
        self, model: str, base_url: Optional[str], api_key: Optional[str]
    ) -> OpenAIProvider:
        """根据配置初始化相应的LLM提供商。"""
        if not base_url or not api_key:
            raise ValueError(f"base_url and api_key are required")
        return OpenAIProvider(model, base_url, api_key)
    
    def _fetch_papers_from_categories(
        self, categories: List[str], max_entries: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """从所有指定类别获取论文。"""
        papers = {}
        
        for category in categories:
            category_papers = self.arxiv_client.fetch_papers(category, max_entries)
            papers[category] = category_papers
            
            print(f"Fetched {len(category_papers)} papers from {category}")
            
            # Rate limiting to avoid being blocked
            time.sleep(random.randint(5, 15))
        
        return papers
    
    def _evaluate_paper_relevance(self, title: str, abstract: str) -> Dict[str, Any]:
        """使用LLM评估论文相关性。"""
        if not self.llm_provider:
            raise ConnectionError("客户端未成功初始化，无法执行LLM调用。")
        prompt = self._build_evaluation_prompt(title, abstract)
        response = self.llm_provider.generate_response(prompt, self.temperature)
        return response
    
    def _build_evaluation_prompt(self, title: str, abstract: str) -> str:
        """Build prompt for paper evaluation."""
        return f"""
你是一个有帮助的 AI 研究助手，可以帮助我构建每日论文推荐系统。
以下是我最近研究领域的描述：
{self.description}

以下是我从昨天的 arXiv 爬取的论文，我为你提供了标题和摘要：
标题: {title}
摘要: {abstract}

请对这篇论文进行深入分析，并严格按照以下JSON格式返回你的评估结果。你的分析必须包含以下几个部分：

1.  **相关性评分 (score)**: 根据我的研究兴趣（见下文），为这篇论文打分，范围从0到10，其中10表示最相关。请使用浮点数以便更精确地表达相关性程度。
2.  **结构化分析 (summary_text)**: 提供一个结构化的分析，必须包含以下四个部分的字符串字段：
    *   `research_background`: 这项研究试图解决什么核心问题？它在哪个领域背景下展开？
    *   `method_and_innovation`: 作者提出了什么新的方法、模型或技术？其核心创新点是什么？
    *   `experiment_and_performance`: 通过实验得出了哪些关键结果？与现有方法相比，性能如何？
    *   `conclusion_and_significance`: 这项研究得出了什么结论？它对学术界或工业界有什么潜在的意义或影响？

请严格按照以下 JSON 格式返回你的回答，不要添加任何额外的解释或文本：
{{
    "score": <0-10的浮点数评分>,
    "summary_text": {{
        "research_background": "<详细的研究背景和问题分析>",
        "method_and_innovation": "<详细的主要方法和创新点分析>",
        "experiment_and_performance": "<详细的实验结果和性能分析>",
        "conclusion_and_significance": "<详细的结论和意义分析>"
    }}
}}
""".strip()
    
    _printed_paper_content = False

    def _process_single_paper(
        self, paper: Dict[str, Any], current_time: str, max_retries: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Process a single paper with retry mechanism."""
        for attempt in range(max_retries):
            try:
                if not PaperRecommender._printed_paper_content:
                    print("--- Single Paper Content ---")
                    import json
                    print(json.dumps(paper, indent=2, ensure_ascii=False))
                    print("--------------------------")
                    PaperRecommender._printed_paper_content = True

                evaluation = self._evaluate_paper_relevance(
                    paper["title"], paper["abstract"]
                )
                
                # Parse LLM response
                evaluation = evaluation.strip("```").strip("json")
                evaluation = evaluation.replace('\\', '\\\\')
                evaluation_data = json.loads(evaluation)

                processed_paper = {
                    "paper_title": paper["title"],
                    "paper_id": paper["arXiv_id"],
                    "summary_text": evaluation_data["summary_text"],
                    "score": float(evaluation_data["score"]),
                    "created_at": current_time,
                    "prompt_type": "structured_analysis",
                }
                
                return processed_paper
                
            except Exception as error:
                if attempt < max_retries - 1:
                    print(f"Error processing paper {paper['arXiv_id']}: {error}")
                    print(f"Retrying... (attempt {attempt + 2}/{max_retries})")
                    time.sleep(1)
                else:
                    print(f"Failed to process paper {paper['arXiv_id']} after {max_retries} attempts")
                    return None
    
    def generate_recommendations(self, current_time: str) -> List[Dict[str, Any]]:
        """Generate paper recommendations based on relevance scores."""
        # Deduplicate papers across categories
        unique_papers = {}
        for category_papers in self.papers.values():
            for paper in category_papers:
                unique_papers[paper["arXiv_id"]] = paper
        
        print(f"Found {len(unique_papers)} unique papers across all categories")
        
        # Process papers in parallel
        recommendations = []
        with ThreadPoolExecutor(self.num_workers) as executor:
            futures = [
                executor.submit(self._process_single_paper, paper, current_time)
                for paper in unique_papers.values()
            ]
            
            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Processing papers",
                unit="paper",
            ):
                result = future.result()
                if result:
                    recommendations.append(result)
        
        # Sort by relevance score and limit results
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        recommendations = recommendations[: self.max_paper_num]

        # print("--- Final Recommendations ---")
        # import json
        # print(json.dumps(recommendations, indent=2, ensure_ascii=False))
        # print("---------------------------")
        
        return recommendations

    def _format_as_html(self, recommendations: List[Dict[str, Any]]) -> Optional[str]:
        """Format recommendations as an HTML string."""
        from email_formatter import EmailFormatter
        formatter = EmailFormatter()

        if not recommendations:
            return formatter.get_empty_content()

        paper_blocks = []
        for rec in recommendations:
            rating = formatter.generate_star_rating(rec['score'])
            summary = rec['summary_text']['research_background'] # Using research_background as a short summary
            pdf_url = f"https://arxiv.org/pdf/{rec['paper_id']}"
            paper_block = formatter.create_paper_block(
                title=rec['paper_title'],
                rating=rating,
                arxiv_id=rec['paper_id'],
                summary=summary,
                pdf_url=pdf_url
            )
            paper_blocks.append(paper_block)
        
        content = "<br>".join(paper_blocks)
        return formatter.wrap_content(content)
    

    def summarize(self, recommendations: List[Dict[str, Any]]) -> str:
        """使用LLM生成推荐论文的摘要报告。"""
        papers_data = []
        for rec in recommendations:
            papers_data.append({
                "paper_title": rec["paper_title"],
                "paper_id": rec["paper_id"],
                "created_at": rec["created_at"],
                "prompt_type": rec["prompt_type"],
                "score": rec["score"],
                "summary_text": rec["summary_text"]
            })

        overview = json.dumps(papers_data, indent=4, ensure_ascii=False)

        prompt = f"""
你是一个顶尖的AI研究分析师，负责为我撰写每日的ArXiv论文洞察报告。

**我的研究领域:**
{self.description}

**今日推荐论文列表 (JSON格式):**
我为你提供了今天筛选出的论文列表（JSON格式），每篇论文都包含了标题、ID、分数以及一个包含四部分的结构化分析（`summary_text`）。
```json
{overview}
```

**你的任务:**
请基于以上JSON数据，生成一份全面、深刻的Markdown格式研究报告。报告必须包含以下部分：

1.  **总体概述 (Overall Summary)**
    *   一句话总结今天所有论文中最核心的研究焦点。
    *   列出2-3个今天论文中反映出的主要研究趋势或热点方向。

2.  **分主题详细分析 (Thematic Analysis)**
    *   将所有论文智能地划分到2-4个核心研究主题下。
    *   在每个主题下，按相关性评分从高到低列出相关论文。
    *   对于每个主题下的每篇论文，**必须严格使用**以下Markdown模板进行渲染，并填充JSON数据中的相应字段。

        ---
        ### {{ paper_title }} (评分: {{ score }})
        
        **论文ID:** {{ paper_id }}  
        **总结时间:** {{ created_at }}  
        **总结类型:** {{ prompt_type }}
        
        #### 研究背景和问题
        {{ summary_text.research_background }}
        
        #### 主要方法和创新点
        {{ summary_text.method_and_innovation }}
        
        #### 实验结果和性能
        {{ summary_text.experiment_and_performance }}
        
        #### 结论和意义
        {{ summary_text.conclusion_and_significance }}
        ---

3.  **未来研究方向 (Future Directions)**
    *   基于今天的论文，提出1-2个具有前瞻性的、值得关注的未来研究方向。

**核心要求:**
*   **内容去重**: 在最终报告中，如果发现不同论文的`summary_text`内容完全一致，请只保留评分最高的那一篇。
*   **格式严格**: 严格按照指定的Markdown模板渲染每一篇论文的展示，不要有任何偏差。
*   **语言**: 使用中文。
*   **输出**: 直接返回完整的Markdown内容，无需任何额外解释或引言。
        """

        response = (
            self.llm_provider.generate_response(prompt, self.temperature)
            .strip("```")
            .strip("markdown")
            .strip()
        )
        return response

    def _generate_summary_report(self, recommendations: List[Dict[str, Any]], current_time_str: str):
        """生成并保存摘要报告。"""
        if not self.save_dir:
            return

        summary_html = self.summarize(recommendations)
        
        os.makedirs(self.save_dir, exist_ok=True)
        
        current_time = datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S')
        save_path = os.path.join(
            self.save_dir, f"{current_time.strftime('%Y-%m-%d')}_summary.md"
        )
        
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(summary_html)
        
        print(f"Summary report saved to {save_path}")

    def run(self, current_time: str) -> Optional[str]:
        """推荐主流程：生成推荐并输出摘要报告。"""
        # Check if papers were fetched successfully
        if not any(self.papers.values()):
            print("Failed to fetch papers from ArXiv after multiple retries. Please check your network connection or try again later.")
            return None

        recommendations = self.generate_recommendations(current_time)
        
        if recommendations:
            print(f"Generated {len(recommendations)} recommendations")
            self._generate_summary_report(recommendations, current_time)
        else:
            print("No recommendations generated.")

        return self._format_as_html(recommendations)


if __name__ == "__main__":
    # 从环境变量读取通义千问配置
    test_model = os.getenv("QWEN_MODEL")
    test_base_url = os.getenv("DASHSCOPE_BASE_URL")
    test_api_key = os.getenv("DASHSCOPE_API_KEY")

    # 初始化论文推荐系统
    recommender = PaperRecommender(
        categories=["cs.CV"],
        max_entries=5,
        max_paper_num=5,
        model=test_model,
        base_url=test_base_url,
        api_key=test_api_key,
        description="""
            I am working on the research area of computer vision and natural language processing. 
            Specifically, I am interested in the following fields:
            1. Object detection
            2. AIGC (AI Generated Content)
            3. Multimodal Large Language Models

            I'm not interested in the following fields:
            1. 3D Vision
            2. Robotics
            3. Low-level Vision
        """,
    )
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    recommender.run(current_time)

