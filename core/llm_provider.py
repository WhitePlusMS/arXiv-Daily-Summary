"""LLM提供商模块

为论文分析和总结提供OpenAI兼容API集成，支持通义千问、SiliconFlow、OLLAMA等。
同时包含LLM提供商的抽象基类定义。
"""

import time
import json
import traceback
import os
from openai import OpenAI
from typing import Optional, Dict, Any, List
from loguru import logger


class LLMProvider:
    """用于LLM交互的通用API提供商，支持通义千问、SiliconFlow等OpenAI兼容API。
    负责所有LLM提示词构建和交互逻辑。"""
    
    def __init__(self, model: str, base_url: str, api_key: str, description: str = "", username: str = "TEST", 
                 temperature: float = 0.7, top_p: float = 0.9, max_tokens: int = 4000):
        """初始化LLM提供商。
        
        Args:
            model: 模型名称
            base_url: API基础URL
            api_key: API密钥
            description: 研究兴趣描述
            username: 用户名，用于生成报告时的署名
            temperature: 默认温度参数
            top_p: 默认top_p参数
            max_tokens: 默认最大token数
        """
        logger.info(f"LLMProvider初始化开始")
        self._model_name = model
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self.description = description
        self.username = username
        self.default_temperature = temperature
        self.default_top_p = top_p
        self.default_max_tokens = max_tokens
        logger.success(f"LLMProvider初始化完成 - 模型: {model}, URL: {base_url}, 用户: {username}, 温度: {temperature}, top_p: {top_p}, max_tokens: {max_tokens}")
    
    @property
    def model_name(self) -> str:
        """获取模型名称。
        
        Returns:
            模型名称字符串
        """
        return self._model_name
    
    def _build_messages(self, prompt: str) -> list:
        """构建OpenAI API的消息结构。
        
        Args:
            prompt: 用户提示文本
            
        Returns:
            消息列表
        """
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    
    def _call_api_with_retry(
        self, messages: list, temperature: float = None, top_p: float = None, 
        max_tokens: int = None, max_retries: int = 2, wait_time: int = 1
    ) -> str:
        """使用重试机制调用OpenAI API。
        
        Args:
            messages: 消息列表
            temperature: 生成温度，如果为None则使用默认值
            top_p: top_p参数，如果为None则使用默认值
            max_tokens: 最大token数，如果为None则使用默认值
            max_retries: 最大重试次数
            wait_time: 重试等待时间（秒）
            
        Returns:
            API响应内容
            
        Raises:
            Exception: API调用失败时抛出异常
        """
        # 使用默认值如果参数为None
        if temperature is None:
            temperature = self.default_temperature
        if top_p is None:
            top_p = self.default_top_p
        if max_tokens is None:
            max_tokens = self.default_max_tokens
            
        logger.debug(f"API调用开始 - 模型: {self._model_name}, 温度: {temperature}, top_p: {top_p}, max_tokens: {max_tokens}, 最大重试: {max_retries}")
        logger.debug(f"API配置 - 客户端: {self._client}, 基础URL: {self._client.base_url}")
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"第 {attempt + 1} 次API调用尝试")
                response = self._client.chat.completions.create(
                    model=self._model_name,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                )
                logger.debug(f"API调用成功 - 尝试次数: {attempt + 1}")
                return response.choices[0].message.content
                
            except Exception as error:
                error_str = str(error).lower()
                error_type = type(error).__name__
                
                # 详细记录错误信息
                logger.error(f"API调用错误详情:")
                logger.error(f"  - 错误类型: {error_type}")
                logger.error(f"  - 错误消息: {error}")
                logger.error(f"  - 模型名称: {self._model_name}")
                logger.error(f"  - 基础URL: {self._client.base_url}")
                logger.error(f"  - 尝试次数: {attempt + 1}/{max_retries}")
                
                # 根据错误类型决定重试策略
                if any(keyword in error_str for keyword in ['rate_limit', '429', 'quota', 'limit']):
                    # API限流错误，使用指数退避
                    wait_time = (attempt + 1) * 3
                    logger.warning(f"API限流 ({attempt + 1}/{max_retries}) - {error}")
                elif any(keyword in error_str for keyword in ['timeout', 'connection', 'network']):
                    # 网络错误，线性退避
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"网络错误 ({attempt + 1}/{max_retries}) - {error}")
                elif any(keyword in error_str for keyword in ['unauthorized', '401', 'api_key', 'authentication']):
                    # 认证错误，不重试
                    logger.error(f"API认证错误，请检查API密钥配置: {error}")
                    raise
                elif any(keyword in error_str for keyword in ['not found', '404', 'model']):
                    # 模型不存在错误，不重试
                    logger.error(f"模型不存在或不可用，请检查模型名称: {error}")
                    raise
                else:
                    # 其他错误，记录详细信息后抛出
                    logger.error(f"API调用不可恢复错误: {error}")
                    logger.error(f"完整错误堆栈: {traceback.format_exc()}")
                    raise
                    
                if attempt < max_retries - 1:
                    logger.debug(f"等待 {wait_time} 秒后重试")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API调用彻底失败 - 所有 {max_retries} 次尝试均失败")
                    raise
    
    def generate_response(self, prompt: str, temperature: float = None, top_p: float = None, max_tokens: int = None) -> str:
        """使用OpenAI API生成响应。
        
        Args:
            prompt: 用户提示文本
            temperature: 生成温度，控制输出的随机性，如果为None则使用默认值
            top_p: top_p参数，如果为None则使用默认值
            max_tokens: 最大token数，如果为None则使用默认值
            
        Returns:
            生成的响应文本
        """
        messages = self._build_messages(prompt)
        return self._call_api_with_retry(messages, temperature, top_p, max_tokens)
    
    def build_paper_evaluation_prompt(self, paper: Dict[str, Any], description: str) -> str:
        """构建论文评估提示词。
        
        Args:
            paper: 论文信息字典
            description: 研究兴趣描述
            
        Returns:
            论文评估提示词
        """
        return f"""
你是一个学术论文评估专家。请根据以下研究兴趣描述，评估这篇论文的相关性。

研究兴趣描述：
{description}

论文信息：
标题：{paper['title']}
摘要：{paper['abstract']}
作者：{', '.join(paper['authors'])}
发布日期：{paper['published']}

请按照以下JSON格式返回评估结果：
{{
    "relevance_score": <0-10的数字，表示相关性评分>,
}}

请确保返回的是有效的JSON格式，不要包含任何其他文字。
        """.strip()
#     请按照以下JSON格式返回评估结果：
# {{
#     "relevance_score": <0-10的数字，表示相关性评分>,
#     "research_background": "<简要描述论文的研究背景和问题>",
#     "methodology_innovation": "<描述论文的方法创新点>",
#     "experimental_results": "<总结论文的实验结果>",
#     "conclusion_significance": "<评价论文结论的意义和影响>",
#     "tldr": "<用一段话总结论文的核心贡献>"
# }}

    def evaluate_paper_relevance(self, paper: Dict[str, Any], description: str, temperature: float = None) -> Dict[str, Any]:
        """评估单篇论文的相关性。
        
        Args:
            paper: 论文信息字典
            description: 研究兴趣描述
            temperature: 生成温度（为None时使用provider默认值）
            
        Returns:
            评估结果字典
        """
        title_short = paper['title'][:50] + '...' if len(paper['title']) > 50 else paper['title']
        logger.debug(f"论文相关性评估开始 - {title_short}")
        
        prompt = self.build_paper_evaluation_prompt(paper, description)
        
        try:
            response = self.generate_response(prompt, temperature)
            # 尝试解析JSON响应
            evaluation = json.loads(response)
            
            # 确保相关性评分字段存在
            if "relevance_score" not in evaluation:
                evaluation["relevance_score"] = 0
            
            # 确保相关性评分是数字
            if not isinstance(evaluation["relevance_score"], (int, float)):
                evaluation["relevance_score"] = 0
            
            logger.debug(f"论文评估完成 - {title_short} (评分: {evaluation['relevance_score']})")
            return evaluation
            
        except json.JSONDecodeError:
            logger.error(f"JSON解析失败 - {title_short}")
            return {
                "relevance_score": 0
            }
        except Exception as e:
            logger.error(f"论文评估异常 - {title_short}: {e}")
            return {
                "relevance_score": 0
            }
    
    def build_summary_report_prompt(self, papers: List[Dict[str, Any]], current_time: str) -> str:
        """构建总结报告提示词。
        
        Args:
            papers: 论文列表
            current_time: 当前时间
            description: 研究兴趣描述
            
        Returns:
            总结报告提示词
        """
        if not papers:
            return ""
        
        # 构建论文信息
        papers_info = []
        for i, paper in enumerate(papers, 1):
            paper_info = f"""
{i}. **{paper['title']}**
   - 相关性评分: {paper['relevance_score']}/10
   - 原始摘要: {paper['abstract']}
   - ArXiv ID: {paper['arXiv_id']}
   - 发布日期: {paper['published']}

            """.strip()
            papers_info.append(paper_info)
        
        papers_text = "\n\n".join(papers_info)
        
        return f"""
你是一位顶尖的AI研究科学家和资深学术导师。你的任务是基于我提供的研究兴趣和最新的ArXiv论文列表，为我生成一份高度结构化、富有洞察力且极具实用价值的中文研究分析报告。

请深入分析每篇论文的核心贡献，识别论文之间的内在联系、技术演进趋势和潜在的研究机会。

我的研究兴趣: {self.description}

推荐论文列表：
{papers_text}

请严格按照以下Markdown模板格式生成报告，确保每一部分都提供深刻且具体的分析：

# ArXiv 研究洞察报告

> BY:{self.username}
> ({current_time})

##  摘要
[在此处提供一个高度浓缩的执行摘要。用2-3句话总结今天所有论文中最核心的发现、最重要的技术趋势，以及与我的研究兴趣最直接的关联。]

## 🔍 主题深度剖析
[将论文精准地划分到2-3个核心研究主题。对于每个主题，进行深入分析：]

### 主题一：[主题名称，例如：多模态大模型的鲁棒性与泛化]
* **核心问题 (Problem Domain):** 该主题下的论文主要致力于解决什么关键科学或工程问题？
* **代表性论文 (Key Papers):** [列出该主题下的1-3篇关键论文的标题]
* **方法论创新 (Methodological Innovations):**
    * **[论文A名称]:** [简述其核心方法、模型架构或算法的创新之处。]
    * **[论文B名称]:** [简述其核心方法、模型架构或算法的创新之处。]
* **研究启示 (Insights & Implications):** 这些成果的研究成果对该领域意味着什么？它们验证了什么假设，或者推翻了什么传统认知？

### 主题二：[主题名称，例如：Agent的自主学习与进化]
* **核心问题 (Problem Domain):** 该主题下的论文主要致力于解决什么关键科学或工程问题？
* **代表性论文 (Key Papers):** [列出该主题下的1-3篇关键论文的标题]
* **方法论创新 (Methodological Innovations):**
    * **[论文A名称]:** [简述其核心方法、模型架构或算法的创新之处。]
* **研究启示 (Insights & Implications):** 这些成果的研究成果对该领域意味着什么？它们验证了什么假设，或者推翻了什么传统认知？


## 📈 宏观趋势与前瞻
[综合所有论文，从更高维度进行分析：]
* **技术趋势 (Tech Trends):** 当前研究最热门的技术方向是什么？（例如：从模型微调转向自主学习、对特定领域（如金融）的深入应用等）
* **潜在机会 (Opportunities):** 基于现有研究，哪些问题尚未被解决？存在哪些新的研究空白或交叉领域机会？
* **值得关注的工具/数据集 (Noteworthy Tools/Datasets):** 本次推荐中是否出现了新的、有潜力的基准测试、数据集或开源工具？


## 💡 个性化建议与行动指南
[本部分将分析与我的研究兴趣紧密结合，提供可操作的建议：]
* **关联性解读 (Relevance Analysis):** 具体说明今天的哪些论文/技术（例如 `SEAgent` 的自主学习框架，或 `FinMMR` 的评测方法）与我的研究方向直接相关。
* **可借鉴点 (Actionable Takeaways):** 我可以从这些论文中借鉴哪些具体的技术、实验设计或分析思路来改进我自己的研究项目？
* **优先阅读建议 (Reading Priority):** 基于相关性和创新性，建议我优先精读哪1-2篇论文？为什么？

---

**请确保最终报告：**
1.  完全使用流畅、专业的中文撰写。
2.  分析深入，避免简单复述摘要。
3.  逻辑清晰，结构严谨，观点独到。
4.  对我个人的研究具有明确的指导价值。
5.  请注意，我的研究兴趣可能是用英文描述的，请在分析时充分理解并将其与论文内容关联。
        """.strip()



    def generate_summary_report(self, papers: List[Dict[str, Any]], current_time: str, temperature: float = None) -> str:
        """生成论文推荐的Markdown总结报告。
        
        Args:
            papers: 论文列表（已排序）
            current_time: 当前时间
            temperature: 生成温度（为None时使用provider默认值）
            
        Returns:
            Markdown格式的总结报告
        """
        if not papers:
            logger.warning("总结报告跳过 - 无推荐论文")
            return "今日无推荐论文。"
        
        logger.info(f"总结报告生成开始 - 原始论文: {len(papers)} 篇")
        
        # 动态选择最佳论文数量，确保提示词长度不超过15000字符
        optimal_papers = self._select_optimal_papers_for_prompt(papers, current_time, max_length=30000)
        
        logger.debug(f"论文数量优化完成 - 最终选择: {len(optimal_papers)} 篇")
        
        prompt = self.build_summary_report_prompt(optimal_papers, current_time)
        logger.debug(f"提示词长度: {len(prompt)} 字符")
        
        try:
            logger.debug("LLM总结生成开始")
            start_time = time.time()
            summary = self.generate_response(prompt, temperature)
            end_time = time.time()
            logger.success(f"总结报告生成完成 - 耗时: {end_time - start_time:.2f}秒, 长度: {len(summary)} 字符")
            return summary
        except Exception as e:
            logger.error(f"总结报告生成失败: {e}")
            return "生成总结失败。"

    def _select_optimal_papers_for_prompt(self, papers: List[Dict[str, Any]], current_time: str, max_length: int = 15000) -> List[Dict[str, Any]]:
        """根据提示词长度限制动态选择最佳论文数量。
        
        Args:
            papers: 已排序的论文列表（按相关性从高到低）
            current_time: 当前时间
            max_length: 提示词最大长度限制
            
        Returns:
            优化后的论文列表
        """
        if not papers:
            return papers
        
        logger.debug(f"论文数量优化开始 - 最大长度限制: {max_length} 字符")
        
        # 从1篇论文开始逐步增加，找到最佳数量
        optimal_papers = []
        
        for i in range(1, len(papers) + 1):
            candidate_papers = papers[:i]
            test_prompt = self.build_summary_report_prompt(candidate_papers, current_time)
            
            if len(test_prompt) <= max_length:
                optimal_papers = candidate_papers
                logger.debug(f"论文数量测试通过 - {i} 篇 (长度: {len(test_prompt)} 字符)")
            else:
                logger.debug(f"论文数量达到上限 - {i} 篇超出限制 (长度: {len(test_prompt)} 字符)")
                break
        
        # 如果没有找到合适的论文数量（连1篇都超长），至少返回第1篇
        if not optimal_papers and papers:
            optimal_papers = papers[:1]
            logger.warning("强制选择1篇论文 - 即使可能超出长度限制")
        
        return optimal_papers


    def build_detailed_analysis_prompt(self, paper: Dict[str, Any]) -> str:
        """构建单篇论文的详细分析提示词.
        
        Args:
            paper: 包含全文的论文信息字典
            
        Returns:
            详细分析提示词
        """
        # Truncate full_text to avoid API errors
        full_text = paper.get('full_text', '')
        if len(full_text) > 15000:
            full_text = full_text[:15000] + "... (truncated)"

        return f"""
你是一位顶尖的AI研究科学家和资深学术导师。你的任务是基于我提供的研究兴趣和一篇完整的ArXiv论文，为我生成一份高度结构化、富有洞察力的中文研究分析报告。

请深入分析这篇论文的核心贡献，并严格按照以下Markdown模板格式生成报告，确保每一部分都提供深刻且具体的分析：

**我的研究兴趣:** {self.description}

---

**论文标题:** {paper['title']}
**作者:** {', '.join(paper['authors'])}
**ArXiv ID:** {paper['arXiv_id']}
**论文链接:** {paper['pdf_url']}

---

**论文全文:**
```text
{full_text}
```

---

**请严格按照以下Markdown格式生成详细分析报告:**

## 1. {paper['title']}
- **相关性评分**: ⭐⭐⭐⭐⭐ ({paper['relevance_score']}/10)
- **ArXiv ID**: {paper['arXiv_id']}
- **作者**: {', '.join(paper['authors'])}
- **论文链接**: <a href="{paper['pdf_url']}" class="link-btn pdf-link" target="_blank">PDF</a> <a href="{paper['abstract_url']}" class="link-btn arxiv-link" target="_blank">ArXiv</a>
- **研究背景**: [在这里详细阐述论文的研究背景、旨在解决的关键问题及其重要性。]
- **方法创新**: [在这里深入分析论文提出的核心方法、模型架构或算法的创新之处。请具体说明其与现有方法的不同和优势。]
- **实验结果**: [在这里总结论文的关键实验设置和主要结果。请描述实验如何验证了方法的有效性，并提及关键的性能指标或发现。]
- **结论意义**: [在这里评价论文结论的科学意义、潜在应用价值和对领域的长远影响。]
- **核心贡献**: [在这里用一段话高度概括论文最核心、最精炼的贡献。]



**请确保最终报告：**
1.  完全使用流畅、专业的中文撰写。
2.  分析深入，避免简单复述原文。
3.  逻辑清晰，结构严谨，观点独到。
4.  对我个人的研究具有明确的指导价值。
5.  请注意，我的研究兴趣可能是用英文描述的，请在分析时充分理解并将其与论文内容关联。
        """.strip()

    def generate_detailed_paper_analysis(self, paper: Dict[str, Any], temperature: float = None) -> str:
        """为单篇论文生成详细的分析报告.
        
        Args:
            paper: 包含全文的论文信息字典
            temperature: 生成温度（为None时使用provider默认值）
            
        Returns:
            Markdown格式的详细分析报告
        """
        title_short = paper['title'][:30] + '...' if len(paper['title']) > 30 else paper['title']
        logger.debug(f"详细分析生成开始 - {title_short}")
        
        # 检查全文是否存在
        if not paper.get("full_text") or len(paper["full_text"]) < 100:
            logger.warning(f"详细分析跳过 - 全文不可用: {title_short}")
            return f"## {paper['title']}\n- **分析失败**: 无法获取有效的论文全文内容。\n"

        prompt = self.build_detailed_analysis_prompt(paper)
        logger.debug(f"详细分析提示词长度: {len(prompt)} 字符")

        try:
            analysis = self.generate_response(prompt, temperature)
            logger.debug(f"详细分析生成完成 - {title_short}")
            return analysis
        except Exception as e:
            logger.error(f"详细分析生成失败 - {title_short}: {e}")
            return f"## {paper['title']}\n- **分析失败**: LLM调用出错: {e}\n"

    def build_brief_analysis_prompt(self, paper: Dict[str, Any]) -> str:
        """构建简要分析的提示词。
        
        Args:
            paper: 论文信息字典
            
        Returns:
            简要分析提示词
        """
        return f"""
你是一位AI研究助手。请基于以下论文的摘要，生成一个简洁的中文TLDR总结。

论文标题：{paper['title']}
论文摘要：{paper['abstract']}

请用1-2句话总结这篇论文的核心贡献和主要发现，使用流畅的中文。
""".strip()

    def generate_brief_analysis(self, paper: Dict[str, Any], temperature: float = None) -> str:
        """为单篇论文生成简要分析（TLDR）。
        
        Args:
            paper: 论文信息字典
            temperature: 生成温度（为None时使用provider默认值）
            
        Returns:
            简要分析的TLDR文本
        """
        title_short = paper['title'][:30] + '...' if len(paper['title']) > 30 else paper['title']
        logger.debug(f"简要分析生成开始 - {title_short}")
        
        prompt = self.build_brief_analysis_prompt(paper)
        
        try:
            tldr = self.generate_response(prompt, temperature)
            logger.debug(f"简要分析生成完成 - {title_short}")
            return tldr.strip()
        except Exception as e:
            logger.error(f"简要分析生成失败 - {title_short}: {e}")
            return "生成摘要失败"


def main():
    """独立测试函数。"""""
    import os
    from dotenv import load_dotenv

    # 加载.env文件中的环境变量
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

    # 从环境变量读取通义千问配置
    test_model = os.getenv("QWEN_MODEL")
    test_base_url = os.getenv("DASHSCOPE_BASE_URL")
    test_api_key = os.getenv("DASHSCOPE_API_KEY")

    # 检查环境变量是否都已设置
    if not all([test_model, test_base_url, test_api_key]):
        logger.error("错误：请确保 .env 文件中已配置 QWEN_MODEL, DASHSCOPE_BASE_URL, 和 DASHSCOPE_API_KEY")
        return
    
    logger.debug("正在使用以下配置进行测试：")
    logger.debug(f"  - 模型: {test_model}")
    logger.debug(f"  - API 地址: {test_base_url}")

    try:
        # 初始化提供商
        provider = LLMProvider(
            model=test_model,
            base_url=test_base_url,
            api_key=test_api_key
        )

        # 测试生成响应
        prompt = "你好，请介绍一下你自己。"
        logger.debug(f"\n发送提示: '{prompt}'")
        response = provider.generate_response(prompt)
        logger.success(f"\n收到响应:\n{response}")
        
        # 测试不同温度设置
        logger.debug("\n测试不同温度设置...")
        creative_prompt = "请创作一首关于人工智能的短诗。"
        
        logger.debug(f"\n低温度 (0.1) 响应:")
        low_temp_response = provider.generate_response(creative_prompt, temperature=0.1)
        logger.success(low_temp_response)
        
        logger.debug(f"\n高温度 (0.9) 响应:")
        high_temp_response = provider.generate_response(creative_prompt, temperature=0.9)
        logger.success(high_temp_response)

    except Exception as e:
        logger.error(f"\n测试过程中发生错误: {e}")


def create_light_llm_provider(description: str = "", username: str = "TEST") -> LLMProvider:
    """根据环境变量配置创建轻量模型LLM提供者。
    
    Args:
        description: 研究兴趣描述
        username: 用户名
        
    Returns:
        配置好的LLM提供者实例
    """
    # 获取轻量模型提供商类型
    provider_type = os.getenv('LIGHT_MODEL_PROVIDER', 'qwen').lower()
    
    if provider_type == 'ollama':
        # OLLAMA配置
        model = os.getenv('OLLAMA_MODEL_LIGHT', 'llama3.2:3b')
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1')
        api_key = 'ollama'  # OLLAMA通常不需要真实的API密钥
        temperature = float(os.getenv('OLLAMA_MODEL_LIGHT_TEMPERATURE', '0.7'))
        top_p = float(os.getenv('OLLAMA_MODEL_LIGHT_TOP_P', '0.9'))
        max_tokens = int(os.getenv('OLLAMA_MODEL_LIGHT_MAX_TOKENS', '2000'))
        
        logger.info(f"创建OLLAMA轻量模型提供者 - 模型: {model}, URL: {base_url}")
    else:
        # 通义千问配置（默认）
        model = os.getenv('QWEN_MODEL_LIGHT', 'qwen3-30b-a3b-instruct-2507')
        base_url = os.getenv('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        api_key = os.getenv('DASHSCOPE_API_KEY', '')
        temperature = float(os.getenv('QWEN_MODEL_LIGHT_TEMPERATURE', '0.5'))
        top_p = float(os.getenv('QWEN_MODEL_LIGHT_TOP_P', '0.8'))
        max_tokens = int(os.getenv('QWEN_MODEL_LIGHT_MAX_TOKENS', '2000'))
        
        logger.info(f"创建通义千问轻量模型提供者 - 模型: {model}")
    
    return LLMProvider(
        model=model,
        base_url=base_url,
        api_key=api_key,
        description=description,
        username=username,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens
    )


if __name__ == "__main__":
    main()