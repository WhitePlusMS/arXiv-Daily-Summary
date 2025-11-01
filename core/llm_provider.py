"""LLM提供商模块

为论文分析和总结提供OpenAI兼容API集成，支持通义千问、SiliconFlow、OLLAMA等。
同时包含LLM提供商的抽象基类定义。
"""

import time
import json
import traceback
import os
from openai import OpenAI
import threading
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
        # Token用量统计（作为单一真源）
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0
        # 并发限流（统一入口，类级共享信号量，跨实例统一限流）
        try:
            max_concurrency = int(os.getenv('LLM_MAX_CONCURRENCY', '2'))
            if max_concurrency < 1:
                max_concurrency = 1
        except Exception:
            max_concurrency = 2
        self._max_concurrency = max_concurrency
        if not hasattr(LLMProvider, "_global_rate_limiter") or LLMProvider._global_rate_limiter is None:
            LLMProvider._global_rate_limiter = threading.BoundedSemaphore(self._max_concurrency)
        self._rate_limiter = LLMProvider._global_rate_limiter
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
        max_tokens: int = None, max_retries: int = 2, wait_time: int = 1, return_raw: bool = False
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
                # 全局并发限流
                self._rate_limiter.acquire()
                logger.debug(f"第 {attempt + 1} 次API调用尝试")
                response = self._client.chat.completions.create(
                    model=self._model_name,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                )
                logger.debug(f"API调用成功 - 尝试次数: {attempt + 1}")
                # 更新token统计（兼容无usage场景）
                try:
                    usage = getattr(response, 'usage', None)
                    if usage:
                        self.total_input_tokens += getattr(usage, 'prompt_tokens', 0) or 0
                        self.total_output_tokens += getattr(usage, 'completion_tokens', 0) or 0
                        self.total_tokens += getattr(usage, 'total_tokens', 0) or 0
                except Exception:
                    pass
                if return_raw:
                    return response
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
            finally:
                # 释放并发令牌
                try:
                    self._rate_limiter.release()
                except Exception:
                    pass

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

    def chat_with_retry(
        self,
        messages: list,
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None,
        max_retries: int = 2,
        wait_time: int = 1,
        return_raw: bool = False,
    ):
        """公共聊天接口，支持重试与可选原始响应返回。

        Args:
            messages: OpenAI兼容消息列表
            temperature: 采样温度
            top_p: top_p 参数
            max_tokens: 最大token数
            max_retries: 最大重试次数
            wait_time: 重试等待秒数
            return_raw: 是否返回原始响应对象

        Returns:
            字符串内容或原始响应对象（取决于 return_raw）
        """
        return self._call_api_with_retry(
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            max_retries=max_retries,
            wait_time=wait_time,
            return_raw=return_raw,
        )

    # =========================
    # 统一提示词构建方法（集中管理）
    # =========================

    @staticmethod
    def build_time_service_system_message() -> str:
        """用于时间工具调用后的最终系统消息，要求仅输出标准时间字符串。"""
        return (
            "你是一个只会返回标准时间格式的机器人。请根据工具返回的结果，直接输出格式为 YYYY-MM-DD HH:MM:SS 的时间字符串，不要包含任何其他文字、标点或解释。"
        )

    @staticmethod
    def build_scoring_warmup_messages() -> List[Dict[str, str]]:
        """用于 OLLAMA 预热的一组消息，确保仅返回整数评分。"""
        return [
            {
                "role": "system",
                "content": "You are a scoring assistant. You MUST respond with only a single integer between 0-100. No explanations, no text, just the number.",
            },
            {
                "role": "user",
                "content": "Output only a number 0-100. No text. Test warmup:",
            },
        ]

    @staticmethod
    def build_scoring_system_message(strict: bool = True) -> str:
        """分类评分的系统消息。
        strict=True 时，额外强调不允许思维链、不允许解释，仅输出数字。
        """
        if strict:
            return (
                "You are a scoring assistant. You MUST respond with only a single integer between 0-100. NEVER use <think> tags or any thinking process. NEVER provide explanations. Output format: just the number, nothing else."
            )
        return (
            "You are a scoring assistant. You MUST respond with only a single integer between 0-100. No explanations, no text, just the number."
        )

    def build_category_evaluation_prompt(self, user_description: str, category: Dict[str, Any]) -> str:
        """构建基础版分类评估提示词（CO-STAR 风格）。"""
        return f"""
# CO-STAR Prompt for Academic Category Matching

## (C) Context:
你正在为一个内部的"智能投稿助手"系统提供核心判断能力。该系统的用户是严谨的科研人员，他们需要根据你的评分来决定自己耗费心血的研究论文应该投往哪个ArXiv分类。ArXiv的分类体系复杂，存在广泛的交叉和重叠，一个研究方向往往与多个分类都有关联，但关联的性质和程度有细微差别。你的判断是这个决策过程中的关键一环。

## (S) Style & (T) Tone:
请扮演一位极其严谨、经验丰富的ArXiv高级审核员。你的判断风格必须是分析性的、批判性的，并且对细节极其敏感。你的工作语气是要求苛刻的，追求绝对的精确，不接受任何模棱两可或过于概括的评估。

## (A) Audience:
你的评估结果的最终受众是一位正在为自己的重要论文（可能是博士毕业论文或一项重大研究的成果）寻找最恰当分类的研究者。他们依赖你的精确评分来避免论文被错投或淹没在不相关的领域中。

## (O) Objective:
你的核心目标是，严格评估以下提供的"用户研究方向"与"ArXiv分类"之间的匹配程度，并输出一个**精确到个位数的整数评分（0-100）**。这个评分必须能反映两者之间哪怕最细微的关联度差异。
- **100分** 代表该研究是此分类的教科书式范例。
- **85-99分** 代表非常核心的匹配，是理想的投稿目标。
- **60-84分** 代表强相关，研究属于该分类的常见子领域或应用领域。
- **30-59分** 代表存在方法论或主题上的交叉，但并非核心。
- **1-29分** 代表仅有微弱或间接的联系。
- **0分** 代表完全不相关。

## (R) Response Format:
你的输出**必须且只能是**一个0到100之间的整数。
- **禁止**返回任何解释、理由、文字或单位。
- **必须**提供细粒度的分数，例如 78, 93, 62，而不是笼统的 70, 80, 90。
Output only a number 0-100. No text.
---
### [输入数据]

#### 用户研究方向:
{user_description}

#### ArXiv分类信息:
- ID: {category['id']}
- 名称: {category['name']}
- 描述: {category['description']}
---
### [输出]
""".strip()

    def build_category_evaluation_prompt_enhanced(self, user_description: str, category: Dict[str, Any]) -> str:
        """构建增强版分类评估提示词（含分类画像）。"""
        profile_info = ""
        if "profile" in category:
            profile = category["profile"]
            profile_info = f"""
#### 分类深度画像:
**领域概述**: {profile.get('profile_summary', '暂无')}

**核心研究主题**:
{chr(10).join([f'    • {topic}' for topic in profile.get('core_topics', [])])}

**常用研究方法**:
{chr(10).join([f'    • {method}' for method in profile.get('common_methodologies', [])])}

**跨学科连接**:
{chr(10).join([f'    • {connection}' for connection in profile.get('interdisciplinary_connections', [])])}

**关键术语**:
{', '.join(profile.get('key_terminologies', []))}
"""

        return f"""
## (C) Context:
你正在为一个高精度的"智能投稿助手"系统提供核心判断能力。该系统的用户是严谨的科研人员，他们需要根据你的评分来决定自己耗费心血的研究论文应该投往哪个ArXiv分类。现在你拥有了该分类的深度画像信息，包括核心研究主题、常用方法论、跨学科连接和关键术语，这使你能够进行更加精准和细致的匹配评估。
## (O) Objective:
基于提供的分类深度画像信息，严格评估"用户研究方向"与"ArXiv分类"之间的匹配程度，输出一个**精确到个位数的整数评分（0-100）**。
## (S) Style & (T) Tone:
请扮演一位拥有深度领域知识的ArXiv资深审核专家。你的判断风格必须是:
- **深度分析性**: 不仅看表面关键词匹配，更要理解研究的本质和方法论
- **多维度评估**: 从研究主题、方法论、跨学科性、术语使用等多个维度综合判断
- **精确量化**: 对细微差别敏感，能够区分85分和87分的差异
- **前瞻性思考**: 考虑研究的发展趋势和在该分类中的接受度
## (A) Audience:
你的评估结果将直接影响一位研究者的论文投稿决策。他们可能是:
- 正在撰写博士论文的研究生
- 准备投稿重要研究成果的学者
- 寻求最佳发表平台的跨学科研究者
他们依赖你的精确评分来最大化论文的影响力和可见度。
**评分标准**:
- **95-100分**: 研究完美契合分类的核心主题和方法论，是该分类的典型代表
- **85-94分**: 研究高度匹配分类的主要研究方向，使用相关方法论和术语
- **70-84分**: 研究与分类有强相关性，涉及相关主题或方法，但可能不是核心
- **50-69分**: 研究与分类存在明显交集，在跨学科连接或方法论上有重叠
- **25-49分**: 研究与分类有一定关联，可能使用相关术语或涉及边缘主题
- **10-24分**: 研究与分类仅有微弱联系，关联性较为间接
- **1-9分**: 研究与分类几乎无关，仅在极个别方面可能有联系
- **0分**: 研究与分类完全不相关
## (R) Response Format:
你的输出**必须且只能是**一个0到100之间的整数。
- **严格禁止**返回任何解释、理由、文字、符号或单位
- **必须**提供精确的个位数评分，体现细微差别
- **示例**: 73, 89, 56（而非70, 90, 60）
Output only a number 0-100. No text.
---
### [输入数据]

#### 用户研究方向:
{user_description}

#### ArXiv分类基础信息:
- **分类ID**: {category['id']}
- **分类名称**: {category.get('name_cn', category.get('name', ''))}
- **官方描述**: {category.get('description_cn', category.get('description', ''))}
{profile_info}
---
### [输出]
""".strip()

    @staticmethod
    def build_category_translation_prompt(text: str) -> str:
        """构建英文到中文的专业翻译提示词。"""
        return f"""
你是一个精通中英文的专业翻译。请将以下英文文本翻译成简洁、专业、流畅的简体中文。
请只返回翻译后的文本，不要包含任何额外的解释或说明。

英文原文:
"{text}"

翻译后的中文:
"""

    @staticmethod
    def build_category_profile_prompt(category: Dict[str, Any], papers: List[Dict[str, Any]]) -> str:
        """为分类画像生成构建统一提示词。"""
        papers_info = []
        for p in papers:
            papers_info.append(f"- 标题: {p['title']}\n- 摘要: {p['abstract']}")
        papers_text = "\n\n".join(papers_info)

        return f"""
你是一个专业的科研领域分析师。请基于以下信息，为一个 ArXiv 科研分类生成一个详细的画像。

**分类信息:**
- 分类ID: {category['id']}
- 分类名称: {category.get('name_cn', category.get('name', ''))}
- 官方描述: {category.get('description_cn', category.get('description', ''))}

**该分类下的代表性论文（标题和摘要）:**
{papers_text}

**你的任务是，总结以上所有信息，生成一个结构化的、详细的分类画像。请严格按照以下JSON格式输出，不要添加任何额外的解释或说明文字：**

{{
  "profile_summary": "用一段话总结该分类的核心研究内容和目标。",
  "core_topics": [
    "根据论文内容，列出3-5个最核心的研究主题或子领域"
  ],
  "common_methodologies": [
    "根据论文内容，列出3-5种该领域常用的研究方法、技术或模型"
  ],
  "interdisciplinary_connections": [
    "分析并列出该分类与其他2-3个科研领域最可能的交叉点"
  ],
  "key_terminologies": [
    "根据论文内容，提取并列出10个最关键的专业术语"
  ]
}}
"""

    # =========================
    # Token感知截断与统计输出
    # =========================
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """粗略估算tokens数量（低风险近似，避免额外依赖）。
        经验法：英文约4字符1token，中文约2字符1token，混合取3字符1token近似。
        """
        if not text:
            return 0
        # 简单近似：长度/3
        return max(1, int(len(text) / 3))

    @staticmethod
    def _truncate_by_tokens(text: str, max_tokens: int, max_chars_fallback: int) -> str:
        """按估算token数截断文本，字符阈值为第二道防线。"""
        if not text:
            return text
        est = LLMProvider._estimate_tokens(text)
        if est <= max_tokens and len(text) <= max_chars_fallback:
            return text
        # 估算允许字符数，保守取每token约3字符
        allowed_chars_by_tokens = max_tokens * 3
        allowed_chars = min(allowed_chars_by_tokens, max_chars_fallback)
        truncated = text[:allowed_chars].rstrip()
        return truncated + "... (truncated)"

    def get_usage_stats(self) -> Dict[str, int]:
        """返回累计token用量。"""
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
        }

    def compute_cost_yuan(self, input_price_per_1k: float = None, output_price_per_1k: float = None) -> Dict[str, float]:
        """根据定价计算费用（人民币）。缺省按通义千问Plus：输入0.008/千token，输出0.02/千token。"""
        try:
            default_in = float(os.getenv('PRICE_INPUT_PER_1K', '0.008'))
        except Exception:
            default_in = 0.008
        try:
            default_out = float(os.getenv('PRICE_OUTPUT_PER_1K', '0.02'))
        except Exception:
            default_out = 0.02
        input_price = input_price_per_1k if input_price_per_1k is not None else default_in
        output_price = output_price_per_1k if output_price_per_1k is not None else default_out
        input_cost = (self.total_input_tokens / 1000.0) * input_price
        output_cost = (self.total_output_tokens / 1000.0) * output_price
        total_cost = input_cost + output_cost
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }

    def log_usage_and_cost(self):
        """通过logger输出当前token用量与费用估算。"""
        stats = self.get_usage_stats()
        cost = self.compute_cost_yuan()
        logger.info("=== Token使用统计 ===")
        logger.info(f"输入Token: {stats['input_tokens']:,}")
        logger.info(f"输出Token: {stats['output_tokens']:,}")
        logger.info(f"总Token: {stats['total_tokens']:,}")
        logger.info("=== 费用估算 (单位: 元) ===")
        logger.info(f"输入费用: ¥{cost['input_cost']:.4f}")
        logger.info(f"输出费用: ¥{cost['output_cost']:.4f}")
        logger.info(f"总费用: ¥{cost['total_cost']:.4f}")
    
    def build_research_description_optimization_prompt(self, user_description: str) -> str:
        """构建研究内容描述优化提示词（基于COSTAR原则）。
        
        Args:
            user_description: 用户输入的简短研究描述
            
        Returns:
            优化提示词
        """
        return f"""
# Context (背景)
你是一位资深的学术研究顾问和科研写作专家，专门帮助研究人员完善和优化他们的研究兴趣描述。你具有丰富的跨学科研究经验，能够准确理解各个领域的研究方向和术语。

# Objective (目标)
请将用户提供的简短研究描述扩展为一个详细、专业、结构化的研究兴趣说明。这个优化后的描述将用于ArXiv论文分类匹配系统，帮助用户找到最相关的研究论文。

# Style (风格)
- 使用学术性但易懂的语言
- 保持专业和客观的语调
- 结构清晰，层次分明
- 包含具体的技术术语和关键词

# Tone (语调)
专业、准确、详细但不冗长，体现研究者的专业水平

# Audience (受众)
学术论文推荐系统和其他研究人员

# Response (响应格式)
请直接输出优化后的研究兴趣描述，按照以下结构：

### 核心研究领域
[明确指出主要的研究领域和方向]

### 具体研究兴趣
[详细列出具体的研究子领域、技术方向或问题]

### 应用场景和目标
[描述研究的应用领域和预期目标]

### 相关关键词
[提供一系列相关的学术关键词，用逗号分隔]

### 不感兴趣的领域
[列出用户不感兴趣的研究领域，用逗号分隔]

用户输入：{user_description}

**要求：**
1. 保持用户原始意图不变，只进行扩展和完善
2. 添加相关的学术术语和技术细节
3. 确保描述足够具体，能够准确匹配相关论文
4. 如果用户描述过于简单，请合理推断可能的研究方向
5. 总长度控制在500字之内
6. 使用中文回复
7. 直接输出优化后的内容，不要包含任何标题或说明文字
        """.strip()

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
    
    def optimize_research_description(self, user_description: str, temperature: float = None) -> str:
        """优化用户的研究内容描述。
        
        Args:
            user_description: 用户输入的简短研究描述
            temperature: 生成温度（为None时使用provider默认值）
            
        Returns:
            优化后的研究描述
        """
        logger.debug(f"研究描述优化开始 - 原始长度: {len(user_description)} 字符")
        
        prompt = self.build_research_description_optimization_prompt(user_description)
        
        try:
            response = self.generate_response(prompt, temperature)
            logger.debug(f"研究描述优化完成 - 优化后长度: {len(response)} 字符")
            return response
            
        except Exception as e:
            logger.error(f"研究描述优化异常: {e}")
            return f"优化失败，返回原始描述：\n\n{user_description}"
    
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
        # Token感知截断：优先按token估算，再用字符长度兜底
        full_text = paper.get('full_text', '')
        from core.common_utils import get_env_int
        max_tokens_text = get_env_int('FULLTEXT_MAX_TOKENS', 4000)
        max_chars_fallback = get_env_int('FULLTEXT_MAX_CHARS', 15000)
        full_text = self._truncate_by_tokens(full_text, max_tokens_text, max_chars_fallback)

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
- **相关性评分**:  ({paper['relevance_score']}/10)
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