"""ArXiv分类匹配器

基于用户研究方向描述，通过LLM分批评估匹配度，找出最符合的ArXiv分类。
"""

import os
import re
import json
import time
from typing import List, Dict, Optional, Tuple, Any
from core.llm_provider import LLMProvider
from core.common_utils import write_json
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
        
        # 使用统一的JSON写入工具函数，参数与原实现一致
        write_json(self.output_file, all_users_list, ensure_ascii=False, indent=2)
        
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
        # 统一由 LLMProvider 管理OpenAI兼容客户端与重试逻辑
        self.llm = LLMProvider(model=model, base_url=base_url, api_key=api_key, username="TEST")
        self.categories = self._load_categories()
        self.enhanced_categories = self._load_enhanced_categories()
        # Token统计迁移至 LLMProvider（单一真源）
        logger.info(f"分类匹配器初始化完成 - 加载了 {len(self.categories)} 个分类")
    
    # 预热逻辑已移除：统一使用云端 API，无需本地引擎预热
    
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
        """加载分类评估数据（包含分类画像信息）
        
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
            
            logger.info(f"加载了 {len(enhanced_categories)} 个分类（含画像）")
            return enhanced_categories
            
        except FileNotFoundError:
            logger.warning("分类评估数据文件不存在，将使用原始分类数据")
            return self.categories
        except Exception as e:
            logger.error(f"加载分类评估数据失败: {e}，将使用原始分类数据")
            return self.categories
    
    def _print_token_usage(self):
        """输出token使用统计和费用计算（委托LLMProvider统一实现）。"""
        try:
            self.llm.log_usage_and_cost()
        except Exception:
            pass
    


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
                # 委托到统一的 LLMProvider 调用与重试逻辑（保留系统指令与温度/长度设置）
                response = self.llm.chat_with_retry(
                    messages=[
                        {"role": "system", "content": LLMProvider.build_scoring_system_message(strict=True)},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    max_tokens=10,
                    max_retries=max_retries,
                    wait_time=1,
                    return_raw=True,
                )

                # Token统计由 LLMProvider 统一处理

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
                # 指数退避等待，适应云端API限流与瞬时波动
                if attempt < max_retries - 1:
                    # 使用统一的退避休眠封装，保持时间公式一致
                    from core.common_utils import backoff_sleep
                    backoff_sleep(attempt, backoff_base, factor=2)
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
            "token_usage": self.llm.get_usage_stats()
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
            # 使用统一的JSON写入工具函数，参数与原实现一致
            write_json(filepath, detailed_data, ensure_ascii=False, indent=2)
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
        logger.info(f"开始分类匹配 - 用户描述长度: {len(user_description)} 字符")
        
        results = []
        
        for i, category in enumerate[Dict[str, str]](self.enhanced_categories):
            logger.debug(f"评估分类 {i+1}/{len(self.enhanced_categories)}: {category['id']}")
            
            prompt = self.llm.build_category_evaluation_prompt(user_description, category)
            score = self._call_llm(prompt)
            
            category_name = category.get('name_cn', category.get('name', ''))
            results.append((category['id'], category_name, score))
            
            # 简单的进度显示
            if (i + 1) % 10 == 0:
                logger.info(f"已评估 {i+1}/{len(self.enhanced_categories)} 个分类")
        
        # 按评分降序排序
        results.sort(key=lambda x: x[2], reverse=True)
        
        # 保存详细评分（如果启用且提供了用户名）
        if save_detailed and username:
            self.save_detailed_scores(username, user_description, results)
        
        # 输出token统计和费用计算
        self._print_token_usage()
        
        logger.success(f"分类匹配完成 - 返回前 {top_n} 个结果")
        return results[:top_n]


def main():
    """演示函数 - 支持多用户数据存储和JSON输出"""
    # 从集中化配置读取
    from core.env_config import get_str
    
    model = get_str("QWEN_MODEL_LIGHT", "qwen-plus")
    base_url = get_str("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = get_str("DASHSCOPE_API_KEY", "")
    
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