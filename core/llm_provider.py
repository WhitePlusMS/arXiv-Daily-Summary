"""LLM提供商模块

为论文分析和总结提供OpenAI兼容API集成，支持通义千问、SiliconFlow等。
同时包含LLM提供商的抽象基类定义。
"""

import time
import json
import traceback
import os
from openai import OpenAI
import threading
from typing import Optional, Dict, Any, List, Union
from loguru import logger
from core.env_config import get_int, get_float, get_str
from core.prompt_manager import get_prompt_manager


class LLMProvider:
    """用于LLM交互的通用API提供商，支持通义千问、SiliconFlow等OpenAI兼容API。
    负责所有LLM提示词构建和交互逻辑。"""
    
    def __init__(self, model: str, base_url: str, api_key: str, description: str = "", username: str = "TEST", 
                 temperature: float = 0.7, top_p: float = 0.9, max_tokens: int = 4000,
                 # 兼容Qwen/OpenAI的扩展默认参数
                 top_k: Optional[int] = None,
                 repetition_penalty: Optional[float] = None,
                 seed: Optional[int] = None,
                 stop: Optional[Union[str, List[str]]] = None,
                 tool_choice: Optional[str] = None,
                 response_format: Optional[Union[str, Dict[str, Any]]] = None,
                 enable_thinking: Optional[bool] = None,
                 logprobs: Optional[bool] = None,
                 top_logprobs: Optional[int] = None,
                 presence_penalty: Optional[float] = None,
                 frequency_penalty: Optional[float] = None,
                 enable_search: Optional[bool] = None,
                 thinking_budget: Optional[int] = None,
                 incremental_output: Optional[bool] = None,
                 ):
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
        
        # 运行时安全检查：API Key 缺失预警
        if not api_key:
            # 检查是否开启了 DEBUG_MODE (通过环境变量兜底检查)
            is_debug = os.getenv("DEBUG_MODE", "false").lower() == "true"
            if not is_debug:
                logger.warning(f"LLMProvider 初始化警告: 模型 {model} 未提供 API Key 且未开启 DEBUG_MODE。API 调用将失败。")

        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self.description = description
        self.username = username
        self.default_temperature = temperature
        self.default_top_p = top_p
        self.default_max_tokens = max_tokens
        # 扩展默认参数
        self.default_top_k = top_k
        self.default_repetition_penalty = repetition_penalty
        self.default_seed = seed
        self.default_stop = stop
        self.default_tool_choice = tool_choice
        self.default_response_format = response_format
        self.default_enable_thinking = enable_thinking
        self.default_logprobs = logprobs
        self.default_top_logprobs = top_logprobs
        self.default_presence_penalty = presence_penalty
        self.default_frequency_penalty = frequency_penalty
        self.default_enable_search = enable_search
        self.default_thinking_budget = thinking_budget
        self.default_incremental_output = incremental_output
        # 统一提示词管理器
        try:
            self.prompt_manager = get_prompt_manager()
        except Exception:
            self.prompt_manager = None
        # Token用量统计（作为单一真源）
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0
        # 用量统计锁，保证并发下的原子累加与一致读取
        self._usage_lock = threading.Lock()
        # 并发限流（统一入口，类级共享信号量，跨实例统一限流）
        max_concurrency = get_int('LLM_MAX_CONCURRENCY', 2)
        if max_concurrency < 1:
            max_concurrency = 1
        self._max_concurrency = max_concurrency
        if not hasattr(LLMProvider, "_global_rate_limiter") or LLMProvider._global_rate_limiter is None:
            LLMProvider._global_rate_limiter = threading.BoundedSemaphore(self._max_concurrency)
        self._rate_limiter = LLMProvider._global_rate_limiter
        logger.success(
            f"LLMProvider初始化完成 - 模型: {model}, URL: {base_url}, 用户: {username}, "
            f"温度: {temperature}, top_p: {top_p}, max_tokens: {max_tokens}, "
            f"top_k: {top_k}, repetition_penalty: {repetition_penalty}, seed: {seed}, "
            f"stop: {stop}, tool_choice: {tool_choice}, response_format: {response_format}, "
            f"enable_thinking: {enable_thinking}, logprobs: {logprobs}, top_logprobs: {top_logprobs}"
        )
    
    @property
    def model_name(self) -> str:
        """获取模型名称。
        
        Returns:
            模型名称字符串
        """
        return self._model_name
    
    def chat_with_retry(
        self,
        messages: list,
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None,
        # 扩展参数（每次调用可覆盖默认值）
        top_k: Optional[int] = None,
        repetition_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        response_format: Optional[Union[str, Dict[str, Any]]] = None,
        enable_thinking: Optional[bool] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        enable_search: Optional[bool] = None,
        thinking_budget: Optional[int] = None,
        incremental_output: Optional[bool] = None,
        max_retries: int = 2,
        wait_time: int = 1,
        return_raw: bool = False,
    ) -> str:
        """公共聊天接口，支持重试与可选原始响应返回。
        
        Args:
            messages: OpenAI兼容消息列表
            temperature: 生成温度，如果为None则使用默认值
            top_p: top_p参数，如果为None则使用默认值
            max_tokens: 最大token数，如果为None则使用默认值
            top_k: top_k参数
            repetition_penalty: 重复惩罚参数
            seed: 随机种子
            stop: 停止序列
            tools: 工具列表
            tool_choice: 工具选择策略
            response_format: 响应格式
            enable_thinking: 是否启用思考模式
            logprobs: 是否返回对数概率
            top_logprobs: top对数概率数量
            presence_penalty: 存在惩罚
            frequency_penalty: 频率惩罚
            enable_search: 是否启用搜索
            thinking_budget: 思考预算
            incremental_output: 是否增量输出
            max_retries: 最大重试次数
            wait_time: 重试等待时间（秒）
            return_raw: 是否返回原始响应对象
            
        Returns:
            字符串内容或原始响应对象（取决于 return_raw）
            
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
        # 扩展参数默认值注入
        if top_k is None:
            top_k = self.default_top_k
        if repetition_penalty is None:
            repetition_penalty = self.default_repetition_penalty
        if seed is None:
            seed = self.default_seed
        if stop is None:
            stop = self.default_stop
        if tool_choice is None:
            tool_choice = self.default_tool_choice
        if response_format is None:
            response_format = self.default_response_format
        if enable_thinking is None:
            enable_thinking = self.default_enable_thinking
        if logprobs is None:
            logprobs = self.default_logprobs
        if top_logprobs is None:
            top_logprobs = self.default_top_logprobs
        if presence_penalty is None:
            presence_penalty = self.default_presence_penalty
        if frequency_penalty is None:
            frequency_penalty = self.default_frequency_penalty
        if enable_search is None:
            enable_search = self.default_enable_search
        if thinking_budget is None:
            thinking_budget = self.default_thinking_budget
        if incremental_output is None:
            incremental_output = self.default_incremental_output
            
        # 当温度为0时，top_p不应设置（让API使用默认行为），否则按默认策略填充
        if temperature == 0:
            top_p_effective = None
        else:
            top_p_effective = top_p if top_p is not None else self.default_top_p

        logger.debug(
            f"API调用开始 - 模型: {self._model_name}, 温度: {temperature}, top_p: {top_p_effective}, max_tokens: {max_tokens}, "
            f"top_k: {top_k}, repetition_penalty: {repetition_penalty}, seed: {seed}, stop: {stop}, "
            f"tool_choice: {tool_choice}, response_format: {response_format}, enable_thinking: {enable_thinking}, "
            f"logprobs: {logprobs}, top_logprobs: {top_logprobs}, presence_penalty: {presence_penalty}, frequency_penalty: {frequency_penalty}, "
            f"enable_search: {enable_search}, thinking_budget: {thinking_budget}, incremental_output: {incremental_output}, 最大重试: {max_retries}"
        )
        # logger.debug(f"API配置 - 客户端: {self._client}, 基础URL: {self._client.base_url}")
        
        for attempt in range(max_retries):
            try:
                # 全局并发限流
                self._rate_limiter.acquire()
                # logger.debug(f"第 {attempt + 1} 次API调用尝试")
                # 组织标准参数
                request_kwargs: Dict[str, Any] = {
                    "model": self._model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                # 仅当 top_p 有效时才传递给API（温度为0则不设置）
                if top_p_effective is not None:
                    request_kwargs["top_p"] = top_p_effective
                if stop is not None:
                    request_kwargs["stop"] = stop
                if tools is not None:
                    request_kwargs["tools"] = tools
                if tool_choice is not None:
                    request_kwargs["tool_choice"] = tool_choice
                if response_format is not None:
                    request_kwargs["response_format"] = response_format
                if logprobs is not None:
                    request_kwargs["logprobs"] = logprobs
                if top_logprobs is not None:
                    request_kwargs["top_logprobs"] = top_logprobs
                if seed is not None:
                    request_kwargs["seed"] = seed
                if presence_penalty is not None:
                    request_kwargs["presence_penalty"] = presence_penalty
                if frequency_penalty is not None:
                    request_kwargs["frequency_penalty"] = frequency_penalty

                # 组织额外体（Qwen/DashScope特有）
                extra_body: Dict[str, Any] = {}
                if top_k is not None:
                    extra_body["top_k"] = top_k
                if repetition_penalty is not None:
                    extra_body["repetition_penalty"] = repetition_penalty
                if enable_thinking is not None:
                    extra_body["enable_thinking"] = enable_thinking
                if enable_search is not None:
                    extra_body["enable_search"] = enable_search
                if thinking_budget is not None:
                    extra_body["thinking_budget"] = thinking_budget
                if incremental_output is not None:
                    extra_body["incremental_output"] = incremental_output

                if extra_body:
                    request_kwargs["extra_body"] = extra_body

                response = self._client.chat.completions.create(**request_kwargs)
                logger.debug(f"API调用成功 - 尝试次数: {attempt + 1}")
                # 更新token统计（兼容无usage场景）
                try:
                    usage = getattr(response, 'usage', None)
                    if usage:
                        with self._usage_lock:
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

    def generate_response(self, prompt: str, temperature: float = 0, top_p: float = None, max_tokens: int = None) -> str:
        """使用OpenAI API生成响应。
        
        Args:
            prompt: 用户提示文本
            temperature: 生成温度，控制输出的随机性，默认值为0
            top_p: top_p参数，如果为None则使用默认值
            max_tokens: 最大token数，如果为None则使用默认值
            
        Returns:
            生成的响应文本
        """
        messages = [
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
        return self.chat_with_retry(messages, temperature, top_p, max_tokens)


    # =========================
    # 统一提示词构建方法（集中管理）
    # =========================

    @staticmethod
    def build_scoring_warmup_messages() -> List[Dict[str, str]]:
        """保留占位的评分预热消息（不再针对本地引擎）。"""
        system_msg = LLMProvider.build_scoring_system_message(strict=True)
        return [
            {
                "role": "system",
                "content": system_msg,
            },
            {
                "role": "user",
                "content": "Output only a number 0-100. No text.",
            },
        ]

    @staticmethod
    def build_scoring_system_message(strict: bool = True) -> str:
        """分类评分的系统消息（集中模板）。"""
        try:
            pm = get_prompt_manager()
            tpl = pm.get_template("scoring_system_message")
            if tpl:
                return tpl
        except Exception:
            pass
        return (
            "You are a scoring assistant. You MUST respond with only a single integer between 0-100. NEVER use <think> tags or any thinking process. NEVER provide explanations. Output format: just the number, nothing else."
        )

    def build_category_evaluation_prompt(self, user_description: str, category: Dict[str, Any]) -> str:
        """构建分类评估提示词"""
        category_name = category.get("name_cn") or category.get("name") or ""
        category_desc = category.get("description_cn") or category.get("description") or ""
        profile_info = ""
        if "profile" in category and isinstance(category.get("profile"), dict):
            profile = category["profile"]
            summary = profile.get("profile_summary", "暂无")
            topics = "\n".join([f"    • {t}" for t in profile.get("core_topics", [])])
            methods = "\n".join([f"    • {m}" for m in profile.get("common_methodologies", [])])
            connections = "\n".join([f"    • {c}" for c in profile.get("interdisciplinary_connections", [])])
            terms = ", ".join(profile.get("key_terminologies", []))
            profile_info = (
                f"**领域概述**: {summary}\n\n"
                f"**核心研究主题**:\n{topics}\n\n"
                f"**常用研究方法**:\n{methods}\n\n"
                f"**跨学科连接**:\n{connections}\n\n"
                f"**关键术语**:\n{terms}"
            )
        return self.prompt_manager.render(
            "category_evaluation",
            {
                "user_description": user_description,
                "category_name": category_name,
                "category_description": category_desc,
                "category_profile": profile_info,
            },
        )

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
        """返回累计token用量（线程安全快照）。"""
        with self._usage_lock:
            return {
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens,
                "total_tokens": self.total_tokens,
            }

    def compute_cost_yuan(self, input_price_per_1k: float = None, output_price_per_1k: float = None) -> Dict[str, float]:
        """根据定价计算费用（人民币）。缺省按通义千问Plus：输入0.008/千token，输出0.02/千token。"""
        default_in = get_float('PRICE_INPUT_PER_1K', 0.008)
        default_out = get_float('PRICE_OUTPUT_PER_1K', 0.02)
        input_price = input_price_per_1k if input_price_per_1k is not None else default_in
        output_price = output_price_per_1k if output_price_per_1k is not None else default_out
        stats = self.get_usage_stats()
        input_cost = (stats["input_tokens"] / 1000.0) * input_price
        output_cost = (stats["output_tokens"] / 1000.0) * output_price
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
        """构建研究内容描述优化提示词（集中模板渲染）。"""
        return self.prompt_manager.render(
            "research_description_optimization",
            {"user_description": user_description},
        )

    def build_paper_evaluation_prompt(self, paper: Dict[str, Any], description: Dict[str, str]) -> str:
        """根据用户的研究兴趣（包含正面和负面偏好）动态构建一个优化的LLM提示词。

        Args:
            paper: 包含 'title' 和 'abstract' 的论文信息字典。
            description: 包含用户偏好的字典。
                         - "positive_query": 必需，用户的主要研究兴趣 (A)。
                         - "negative_query": 可选，用户"不太想要"的研究方向 (B)。

        Returns:
            一个为LLM准备好的、用于生成0-10分相关性评分的字符串提示词。
        """
        
        # 1. 提取输入
        positive_query = description.get("positive_query", "")
        negative_query = description.get("negative_query")  # 如果不存在，这将是 None
        
        paper_title = paper.get('title', 'N/A')
        paper_abstract = paper.get('abstract', 'N/A')
        
        # 2. 根据是否有负面偏好选择不同的提示词模板
        if not negative_query:
            # 场景一：用户只有正面兴趣（单兴趣场景）
            prompt_id = "paper_evaluation_single_interest"
            variables = {
                "positive_query": positive_query,
                "paper_title": paper_title,
                "paper_abstract": paper_abstract,
            }
        else:
            # 场景二：用户有正面和负面兴趣（双兴趣场景）
            prompt_id = "paper_evaluation_dual_interest"
            variables = {
                "positive_query": positive_query,
                "negative_query": negative_query,
                "paper_title": paper_title,
                "paper_abstract": paper_abstract,
            }
        
        # 3. 使用 PromptManager 渲染模板
        if not self.prompt_manager:
            logger.error("PromptManager 未初始化，无法构建提示词")
            raise RuntimeError("PromptManager 未初始化")
        
        try:
            return self.prompt_manager.render(prompt_id, variables)
        except KeyError as e:
            logger.error(f"提示词模板不存在或变量缺失: {prompt_id}, 错误: {e}")
            raise
        except Exception as e:
            logger.error(f"渲染提示词模板失败: {prompt_id}, 错误: {e}")
            raise
#     请按照以下JSON格式返回评估结果：
# {{
#     "relevance_score": <0-10的数字，表示相关性评分>,
#     "research_background": "<简要描述论文的研究背景和问题>",
#     "methodology_innovation": "<描述论文的方法创新点>",
#     "experimental_results": "<总结论文的实验结果>",
#     "conclusion_significance": "<评价论文结论的意义和影响>",
#     "tldr": "<用一段话总结论文的核心贡献>"
# }}

    def evaluate_paper_relevance(self, paper: Dict[str, Any], description: Union[str, Dict[str, str]], temperature: float = 0) -> Dict[str, Any]:
        """评估单篇论文的相关性。
        
        Args:
            paper: 论文信息字典
            description: 研究兴趣描述，可以是字符串（向后兼容）或字典格式
                         - 字符串格式：直接作为 positive_query
                         - 字典格式：{"positive_query": ..., "negative_query": ...}
            temperature: 生成温度（为None时使用provider默认值）
            
        Returns:
            评估结果字典
        """
        title_short = paper['title'][:50] + '...' if len(paper['title']) > 50 else paper['title']
        logger.debug(f"论文相关性评估开始 - {title_short}")
        
        # 向后兼容：如果 description 是字符串，转换为字典格式
        if isinstance(description, str):
            description = {"positive_query": description, "negative_query": ""}
        
        prompt = self.build_paper_evaluation_prompt(paper, description)
        
        try:
            # 评分参数固定：温度为0、最大tokens固定，避免受外部配置影响
            response = self.generate_response(prompt, temperature=temperature, max_tokens=50)
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
        
        # 构建论文信息文本
        papers_info = []
        for i, paper in enumerate(papers, 1):
            info = (
                f"{i}. **{paper['title']}**\n"
                f"   - 相关性评分: {paper['relevance_score']}/10\n"
                f"   - 原始摘要: {paper['abstract']}\n"
                f"   - ArXiv ID: {paper['arXiv_id']}\n"
                f"   - 发布日期: {paper['published']}\n"
            ).strip()
            papers_info.append(info)
        papers_text = "\n\n".join(papers_info)

        return self.prompt_manager.render(
            "summary_report",
            {
                "description": self.description,
                "username": self.username,
                "current_time": current_time,
                "papers_text": papers_text,
            },
        )



    def generate_summary_report(self, papers: List[Dict[str, Any]], current_time: str, temperature: float = None, max_papers: Optional[int] = None) -> str:
        """生成论文推荐的Markdown总结报告。
        
        Args:
            papers: 论文列表（已排序）
            current_time: 当前时间
            temperature: 生成温度（为None时使用provider默认值）
            max_papers: 最大论文数量限制（用户配置的 num_detailed_papers + num_brief_papers），如果为None则不限制
            
        Returns:
            Markdown格式的总结报告
        """
        if not papers:
            logger.warning("总结报告跳过 - 无推荐论文")
            return "今日无推荐论文。"
        
        logger.info(f"总结报告生成开始 - 原始论文: {len(papers)} 篇, 用户配置最大数量: {max_papers}")
        
        # 动态选择最佳论文数量，确保提示词长度不超过30000字符，同时遵守用户配置的最大论文数量
        optimal_papers = self._select_optimal_papers_for_prompt(papers, current_time, max_length=30000, max_papers=max_papers)
        
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

    def _select_optimal_papers_for_prompt(self, papers: List[Dict[str, Any]], current_time: str, max_length: int = 15000, max_papers: Optional[int] = None) -> List[Dict[str, Any]]:
        """根据提示词长度限制动态选择最佳论文数量。
        
        Args:
            papers: 已排序的论文列表（按相关性从高到低）
            current_time: 当前时间
            max_length: 提示词最大长度限制
            max_papers: 最大论文数量限制（用户配置），如果为None则不限制
            
        Returns:
            优化后的论文列表
        """
        if not papers:
            return papers
        
        # 首先应用用户配置的最大论文数量限制
        if max_papers is not None and max_papers > 0:
            papers = papers[:max_papers]
            logger.debug(f"应用用户配置限制 - 最大论文数: {max_papers}, 限制后: {len(papers)} 篇")
        
        logger.debug(f"论文数量优化开始 - 最大长度限制: {max_length} 字符, 当前论文数: {len(papers)} 篇")
        
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
        max_tokens_text = get_int('FULLTEXT_MAX_TOKENS', 4000)
        max_chars_fallback = get_int('FULLTEXT_MAX_CHARS', 20000)
        full_text = self._truncate_by_tokens(full_text, max_tokens_text, max_chars_fallback)

        return self.prompt_manager.render(
            "detailed_analysis",
            {
                "description": self.description,
                "title": paper.get('title', ''),
                "authors": ", ".join(paper.get('authors', [])),
                "arXiv_id": paper.get('arXiv_id', ''),
                "pdf_url": paper.get('pdf_url', ''),
                "full_text": full_text,
                "relevance_score": paper.get('relevance_score', ''),
            },
        )

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
            
            # 清洗LLM输出
            analysis = analysis.strip()
            
            # 简单清洗：如果LLM还是输出了标题（以## 开头），尝试去除第一行
            # 但更稳健的方式是直接拼接，假设Prompt生效。
            # 为了防止LLM复述标题，我们可以检查analysis是否以标题开头
            title = paper.get('title', '').strip()
            if analysis.startswith(f"## {title}"):
                lines = analysis.split('\n')
                # 移除第一行标题
                analysis = "\n".join(lines[1:]).strip()
                # 继续移除可能的元数据行，直到遇到第一个 ### 标题
                # 这里简单处理，假设Prompt有效。如果无效，会有重复信息，但不会丢失。
            
            # 构建标准头部（保证元数据准确，来源于前置步骤）
            authors = ", ".join(paper.get('authors', []))
            pdf_url = paper.get('pdf_url', '')
            abstract_url = paper.get('abstract_url', '')
            alphaxiv_url = abstract_url.replace("arxiv.org", "www.alphaxiv.org") if abstract_url else ""
            relevance_score = paper.get('relevance_score', 0)
            arxiv_id = paper.get('arXiv_id', '')
            
            header = (
                f"## {title}\n"
                f"- **相关性评分**: ({relevance_score}/10)\n"
                f"- **ArXiv ID**: {arxiv_id}\n"
                f"- **作者**: {authors}\n"
                f"- **论文链接**: <a href=\"{pdf_url}\" class=\"link-btn pdf-link\" target=\"_blank\">PDF</a> <a href=\"{abstract_url}\" class=\"link-btn arxiv-link\" target=\"_blank\">arXiv</a> <a href=\"{alphaxiv_url}\" class=\"link-btn alphaxiv-link\" target=\"_blank\">alphaXiv</a>\n\n"
            )
            
            full_content = header + analysis
            
            logger.debug(f"详细分析生成完成 - {title_short}")
            return full_content
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
        return self.prompt_manager.render(
            "brief_analysis",
            {
                "title": paper.get('title', ''),
                "abstract": paper.get('abstract', ''),
            },
        )

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
    from core.env_config import get_str

    # 从集中化配置读取通义千问配置
    test_model = get_str("QWEN_MODEL", "")
    test_base_url = get_str("DASHSCOPE_BASE_URL", "")
    test_api_key = get_str("DASHSCOPE_API_KEY", "")

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
    # 统一使用通义千问轻量模型配置
    model = get_str('QWEN_MODEL_LIGHT', 'qwen3-30b-a3b-instruct-2507')
    base_url = get_str('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    api_key = get_str('DASHSCOPE_API_KEY', '')
    temperature = get_float('QWEN_MODEL_LIGHT_TEMPERATURE', 0.5)
    top_p = get_float('QWEN_MODEL_LIGHT_TOP_P', 0.8)
    max_tokens = get_int('QWEN_MODEL_LIGHT_MAX_TOKENS', 2000)
    
    logger.info(f"创建通义千问轻量模型提供者 - 模型: {model}")
    
    return LLMProvider(
        model=model,
        base_url=base_url,
        api_key=api_key,
        description=description,
        username=username,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )


if __name__ == "__main__":
    main()