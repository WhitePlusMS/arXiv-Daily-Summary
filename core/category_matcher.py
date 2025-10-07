"""ArXiv分类匹配器

基于用户研究方向描述，通过LLM分批评估匹配度，找出最符合的ArXiv分类。
"""

import os
import re
import json
import time
from typing import List, Dict, Optional, Tuple, Any
from openai import OpenAI
from loguru import logger
from datetime import datetime
import re
import time


class MultiUserDataManager:
    """多用户数据管理器，用于存储和管理多个用户的分类匹配结果"""
    
    def __init__(self, output_file: str = None):
        """初始化数据管理器
        
        Args:
            output_file: 输出JSON文件路径，如果为None则使用默认路径
        """
        if output_file is None:
            # 获取项目根目录路径
            project_root = os.path.dirname(os.path.dirname(__file__))
            self.output_file = os.path.join(project_root, 'data', 'users', 'user_categories.json')
        else:
            self.output_file = output_file
        self.users_data = {}  # 存储本次新增的用户数据
        self.existing_records = []  # 存储现有的记录
        
    def add_user_result(self, username: str, top_matches: List[Tuple[str, str, int]], user_input: str):
        """添加用户匹配结果
        
        Args:
            username: 用户名
            top_matches: 前N个匹配结果列表
            user_input: 用户输入的研究方向描述
        """
        # 提取前5个分类ID
        category_ids = [match[0] for match in top_matches[:5]]
        category_ids_str = ",".join(category_ids)
        
        user_record = {
            "username": username,
            "category_id": category_ids_str,
            "user_input": user_input
        }
        
        # 使用用户名和输入作为唯一键
        key = f"{username}_{hash(user_input)}"
        self.users_data[key] = user_record
        logger.info(f"添加用户记录: {username} -> {category_ids_str}")
    
    def save_to_json(self):
        """保存数据到JSON文件（追加模式）"""
        # 先加载现有数据
        existing_data = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                logger.info(f"加载了现有的 {len(existing_data)} 条记录")
            except Exception as e:
                logger.warning(f"加载现有文件失败: {e}，将创建新文件")
                existing_data = []
        
        # 转换新数据为列表格式
        new_users_list = list(self.users_data.values())
        
        # 合并数据（追加新数据到现有数据后面）
        all_users_list = existing_data + new_users_list
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(all_users_list, f, ensure_ascii=False, indent=2)
        
        logger.success(f"数据已保存到: {self.output_file}")
        print(f"\n=== 数据保存完成 ===")
        print(f"文件路径: {os.path.abspath(self.output_file)}")
        print(f"原有记录: {len(existing_data)} 条")
        print(f"新增记录: {len(new_users_list)} 条")
        print(f"总记录数: {len(all_users_list)} 条")
    
    def load_from_json(self):
        """从JSON文件加载现有数据（仅用于检查重复）"""
        self.existing_records = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    self.existing_records = json.load(f)
                logger.info(f"检测到现有文件，包含 {len(self.existing_records)} 条记录")
            except Exception as e:
                logger.warning(f"加载文件失败: {e}")
                self.existing_records = []
        else:
            logger.info("输出文件不存在，将创建新文件")
            self.existing_records = []


class CategoryMatcher:
    """ArXiv分类匹配器，用于将用户研究方向匹配到最相关的ArXiv分类"""
    
    def __init__(self, model: str, base_url: str, api_key: str):
        """初始化分类匹配器
        
        Args:
            model: LLM模型名称
            base_url: API基础URL
            api_key: API密钥
        """
        self.model = model
        self.base_url = base_url
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.categories = self._load_categories()
        self.enhanced_categories = self._load_enhanced_categories()
        # Token统计
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0
        logger.info(f"分类匹配器初始化完成 - 加载了 {len(self.categories)} 个分类")
    
    def warmup(self, attempts: int = 2):
        """预热OLLAMA模型，避免冷启动问题
        
        Args:
            attempts: 预热尝试次数
        """
        # 检查是否为OLLAMA模型（通过base_url判断）
        is_ollama = 'localhost' in self.base_url.lower() or 'ollama' in self.base_url.lower()
        
        if not is_ollama:
            logger.info("检测到API模型，跳过预热过程")
            return
        
        logger.info(f"检测到OLLAMA模型，开始预热，尝试 {attempts} 次...")
        
        for i in range(attempts):
            try:
                # 发送简单的预热请求
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a scoring assistant. You MUST respond with only a single integer between 0-100. No explanations, no text, just the number."},
                        {"role": "user", "content": "Output only a number 0-100. No text. Test warmup:"}
                    ],
                    max_tokens=3,
                    temperature=0.0
                )
                
                output = response.choices[0].message.content.strip()
                logger.info(f"预热第{i+1}次成功，输出: '{output}'")
                
                # 短暂延迟
                if i < attempts - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.warning(f"预热第{i+1}次失败: {e}")
                # 继续尝试，不中断预热过程
                continue
        
        logger.info("OLLAMA模型预热完成")
    
    def _load_categories(self) -> List[Dict[str, str]]:
        """加载ArXiv分类数据
        
        Returns:
            包含所有子分类的列表，每个元素包含id, name, description
        """
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(__file__))
        categories_file = os.path.join(
            project_root,
            'data', 
            'users',
            'arxiv_categories.json'
        )
        
        with open(categories_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取所有子分类
        all_subcategories = []
        for main_category in data['arxiv_categories']['categories']:
            for subcategory in main_category['subcategories']:
                all_subcategories.append({
                    'id': subcategory['id'],
                    'name': subcategory['name'],
                    'description': subcategory['description']
                })
        
        return all_subcategories
    
    def _load_enhanced_categories(self) -> List[Dict[str, str]]:
        """加载增强版ArXiv分类数据（包含分类画像信息）
        
        Returns:
            包含所有分类及其画像信息的列表
        """
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(__file__))
        enhanced_categories_file = os.path.join(
            project_root,
            'data', 
            'users',
            'arxiv_categories_enhanced.json'
        )
        
        try:
            with open(enhanced_categories_file, 'r', encoding='utf-8') as f:
                enhanced_categories = json.load(f)
            
            logger.info(f"加载了 {len(enhanced_categories)} 个增强版分类")
            return enhanced_categories
            
        except FileNotFoundError:
            logger.warning("增强版分类文件不存在，将使用基础分类数据")
            return self.categories
        except Exception as e:
            logger.error(f"加载增强版分类数据失败: {e}，将使用基础分类数据")
            return self.categories
    
    def _print_token_usage(self):
        """输出token使用统计和费用计算"""
        print("\n=== Token使用统计 ===")
        print(f"输入Token: {self.total_input_tokens:,}")
        print(f"输出Token: {self.total_output_tokens:,}")
        print(f"总Token: {self.total_tokens:,}")
        
        # 计算费用（基于通义千问的定价）
        # 通义千问Plus: 输入0.008元/千token，输出0.02元/千token
        input_cost = (self.total_input_tokens / 1000) * 0.008
        output_cost = (self.total_output_tokens / 1000) * 0.02
        total_cost = input_cost + output_cost
        
        print(f"\n=== 费用计算 (通义千问Plus定价) ===")
        print(f"输入费用: ¥{input_cost:.4f}")
        print(f"输出费用: ¥{output_cost:.4f}")
        print(f"总费用: ¥{total_cost:.4f}")
    
    def _build_evaluation_prompt(self, user_description: str, category: Dict[str, Any]) -> str:
        """构建评估提示词
        
        Args:
            user_description: 用户研究描述
            category: 单个分类信息
            
        Returns:
            评估提示词
        """
        return self.generate_prompt(user_description, category)
    
    def _build_enhanced_evaluation_prompt(self, user_description: str, category: Dict[str, Any]) -> str:
        """构建增强版评估提示词，利用分类画像信息
        
        Args:
            user_description: 用户研究描述
            category: 包含profile信息的分类数据
            
        Returns:
            增强版评估提示词
        """
        return self.generate_enhanced_prompt(user_description, category)

    def generate_prompt(self, user_description, category):
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

    def generate_enhanced_prompt(self, user_description, category):
        """生成增强版提示词，利用分类画像信息提供更精准的匹配评估
        
        Args:
            user_description: 用户研究描述
            category: 包含profile信息的分类数据
            
        Returns:
            增强版评估提示词
        """
        # 构建分类画像信息
        profile_info = ""
        if 'profile' in category:
            profile = category['profile']
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

    def _call_llm(self, prompt: str) -> int:
        """调用LLM获取评分，带重试与稳健解析
        
        Args:
            prompt: 提示词
            
        Returns:
            0-100的评分
        """
        max_retries = 3
        backoff_base = 1.5
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a scoring assistant. You MUST respond with only a single integer between 0-100. NEVER use <think> tags or any thinking process. NEVER provide explanations. Output format: just the number, nothing else."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    max_tokens=10
                )

                # 统计token使用量（兼容无usage场景）
                try:
                    if hasattr(response, 'usage') and response.usage:
                        self.total_input_tokens += getattr(response.usage, 'prompt_tokens', 0) or 0
                        self.total_output_tokens += getattr(response.usage, 'completion_tokens', 0) or 0
                        self.total_tokens += getattr(response.usage, 'total_tokens', 0) or 0
                except Exception:
                    pass

                # 提取数字评分（稳健解析）
                content = (response.choices[0].message.content or "").strip()
                # 直接尝试转换
                try:
                    score = int(content)
                    return max(0, min(100, score))
                except Exception:
                    # 使用正则在任意文本中抓取0-100的整数（选择最后一个更可能是最终答案）
                    matches = re.findall(r"\b(100|[1-9]?\d)\b", content)
                    if matches:
                        score = int(matches[-1])
                        return max(0, min(100, score))
                    # 未能解析则抛出错误以触发重试
                    raise ValueError(f"无法从模型输出中解析整数评分，输出内容片段: {content[:80]}")

            except Exception as e:
                last_error = e
                logger.warning(f"LLM调用失败(第{attempt+1}次): {e}")
                # 指数退避等待，给Ollama冷启动/模型加载留时间
                if attempt < max_retries - 1:
                    sleep_s = backoff_base * (2 ** attempt)
                    time.sleep(sleep_s)
                else:
                    # 最后一次失败，返回0分避免中断全流程
                    logger.warning("LLM多次调用失败，返回0作为该分类评分")
                    return 0
        # 理论上不会到达这里
        logger.warning(f"LLM调用异常(返回兜底0): {last_error}")
        return 0
    
    def save_detailed_scores(self, username: str, user_description: str, all_results: List[Tuple[str, str, int]]):
        """保存用户的全部分类详细评分到单独的JSON文件
        
        Args:
            username: 用户名
            user_description: 用户研究方向描述
            all_results: 全部分类的评分结果
        """
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(__file__))
        detailed_scores_dir = os.path.join(project_root, 'data', 'users', 'detailed_scores')
        
        # 确保目录存在
        os.makedirs(detailed_scores_dir, exist_ok=True)
        
        # 生成文件名（包含时间戳避免冲突）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{username}_{timestamp}_detailed_scores.json"
        filepath = os.path.join(detailed_scores_dir, filename)
        
        # 构建详细数据结构
        detailed_data = {
            "metadata": {
                "username": username,
                "timestamp": datetime.now().isoformat(),
                "user_description": user_description,
                "total_categories": len(all_results),
                "token_usage": {
                    "input_tokens": getattr(self, 'total_input_tokens', 0),
                    "output_tokens": getattr(self, 'total_output_tokens', 0),
                    "total_tokens": getattr(self, 'total_tokens', 0)
                }
            },
            "detailed_scores": [
                {
                    "rank": i + 1,
                    "category_id": result[0],
                    "category_name": result[1],
                    "score": result[2]
                }
                for i, result in enumerate(all_results)
            ]
        }
        
        # 保存到文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(detailed_data, f, ensure_ascii=False, indent=2)
            logger.success(f"详细评分已保存到: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存详细评分失败: {e}")
            return None
    
    def match_categories(self, user_description: str, top_n: int = 5, save_detailed: bool = True, username: str = None) -> List[Tuple[str, str, int]]:
        """匹配用户研究方向到ArXiv分类
        
        Args:
            user_description: 用户研究方向描述
            top_n: 返回前N个最匹配的分类
            save_detailed: 是否保存全部分类的详细评分
            username: 用户名（用于保存详细评分）
            
        Returns:
            包含(category_id, category_name, score)的列表，按评分降序排列
        """
        logger.info(f"开始匹配分类 - 用户描述长度: {len(user_description)} 字符")
        
        results = []
        
        for i, category in enumerate(self.categories):
            logger.debug(f"评估分类 {i+1}/{len(self.categories)}: {category['id']}")
            
            prompt = self._build_evaluation_prompt(user_description, category)
            score = self._call_llm(prompt)
            
            results.append((category['id'], category['name'], score))
            
            # 简单的进度显示
            if (i + 1) % 10 == 0:
                logger.info(f"已评估 {i+1}/{len(self.categories)} 个分类")
        
        # 按评分降序排序
        results.sort(key=lambda x: x[2], reverse=True)
        
        # 保存详细评分（如果启用且提供了用户名）
        if save_detailed and username:
            self.save_detailed_scores(username, user_description, results)
        
        # 输出token统计和费用计算
        self._print_token_usage()
        
        logger.success(f"分类匹配完成 - 返回前 {top_n} 个结果")
        return results[:top_n]
    
    def match_categories_enhanced(self, user_description: str, top_n: int = 5, save_detailed: bool = True, username: str = None) -> List[Tuple[str, str, int]]:
        """使用增强版提示词匹配用户研究方向到ArXiv分类
        
        Args:
            user_description: 用户研究方向描述
            top_n: 返回前N个最匹配的分类
            save_detailed: 是否保存全部分类的详细评分
            username: 用户名（用于保存详细评分）
            
        Returns:
            包含(category_id, category_name, score)的列表，按评分降序排列
        """
        logger.info(f"开始增强版分类匹配 - 用户描述长度: {len(user_description)} 字符")
        
        results = []
        
        for i, category in enumerate(self.enhanced_categories):
            logger.debug(f"评估增强版分类 {i+1}/{len(self.enhanced_categories)}: {category['id']}")
            
            prompt = self._build_enhanced_evaluation_prompt(user_description, category)
            score = self._call_llm(prompt)
            
            category_name = category.get('name_cn', category.get('name', ''))
            results.append((category['id'], category_name, score))
            
            # 简单的进度显示
            if (i + 1) % 10 == 0:
                logger.info(f"已评估 {i+1}/{len(self.enhanced_categories)} 个增强版分类")
        
        # 按评分降序排序
        results.sort(key=lambda x: x[2], reverse=True)
        
        # 保存详细评分（如果启用且提供了用户名）
        if save_detailed and username:
            self.save_detailed_scores(f"{username}_enhanced", user_description, results)
        
        # 输出token统计和费用计算
        self._print_token_usage()
        
        logger.success(f"增强版分类匹配完成 - 返回前 {top_n} 个结果")
        return results[:top_n]


def main():
    """演示函数 - 支持多用户数据存储和JSON输出"""
    # 从环境变量读取配置（需要先设置.env文件）
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))
    
    model = os.getenv("QWEN_MODEL_LIGHT", "qwen-plus")
    base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        print("错误：请在.env文件中设置DASHSCOPE_API_KEY")
        return
    
    # 初始化匹配器和数据管理器
    matcher = CategoryMatcher(model, base_url, api_key)
    data_manager = MultiUserDataManager("../data/users/user_categories.json")
    
    # 加载现有数据
    data_manager.load_from_json()
    
    # 示例多用户数据
    test_users = [
        {
            "username": "TEST",
            "user_input": """# 个人研究兴趣
我正在从事RAG领域的研究。具体来说，我对以下领域感兴趣：
1. RAG（检索增强生成）
2. LLM（大语言模型）
3. 多模态大语言模型
我对以下领域不感兴趣：
1. 除了RAG、LLM和多模态大语言模型，我对其他领域的研究也不感兴趣。"""
        }
    ]
    
    print("=== 开始处理多用户分类匹配 ===")
    
    for user_data in test_users:
        username = user_data["username"]
        user_input = user_data["user_input"]
        
        print(f"\n处理用户: {username}")
        print(f"研究方向: {user_input[:50]}...")
        print("开始匹配分类...")
        
        # 匹配分类
        top_matches = matcher.match_categories(user_input, top_n=5)
        
        print(f"\n=== {username} 的匹配结果 ===")
        for i, (category_id, category_name, score) in enumerate(top_matches, 1):
            print(f"{i}. {category_id} - {category_name} (评分: {score})")
        
        # 将匹配结果添加到数据管理器
        data_manager.add_user_result(
            username=username,
            top_matches=top_matches,
            user_input=user_input
        )
        
        print(f"\n{username} 处理完成！")
        print("-" * 50)
    
    # 保存所有数据到JSON文件
    data_manager.save_to_json()
    
    print("\n=== 所有用户处理完成！ ===")
    print(f"结果已保存到: {os.path.abspath('../data/users/user_categories.json')}")


if __name__ == "__main__":
    main()