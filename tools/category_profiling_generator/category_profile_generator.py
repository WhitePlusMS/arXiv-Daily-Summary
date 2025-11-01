"""
ArXiv 分类画像生成器

该脚本用于为每个 ArXiv 分类创建一个详细的“画像”。它通过以下步骤实现：
1. 读取现有的 ArXiv 分类信息。
2. 为每个分类从 ArXiv API 获取最新的、有代表性的论文。
3. 使用大型语言模型（LLM）总结这些论文的标题和摘要。
4. 生成一个包含核心主题、常用方法、交叉领域和关键词的“分类画像”。
5. 将这些增强后的信息保存到一个新的 JSON 文件中，以供后续的匹配任务使用。
"""

import sys
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.arxiv_fetcher import ArxivFetcher
from core.llm_provider import LLMProvider

# 加载环境变量
load_dotenv(project_root / '.env', override=True)

def generate_category_profile(llm_provider: LLMProvider, category: dict, papers: list) -> tuple[dict | None, dict | None]:
    """使用 LLM 为单个分类生成画像，并返回 token 使用情况"""
    
    # 准备论文信息
    papers_info = []
    for p in papers:
        papers_info.append(f"- 标题: {p['title']}\n- 摘要: {p['abstract']}")
    
    papers_text = "\n\n".join(papers_info)
    
    # 构建 Prompt（集中管理）
    prompt = LLMProvider.build_category_profile_prompt(category, papers)
    
    print(f"\n正在为分类 {category['id']} 调用 LLM 生成画像...")
    
    try:
        response = llm_provider._client.chat.completions.create(
            model=llm_provider.model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}, # 强制JSON输出
            temperature=0.2,
        )
        profile_json_str = response.choices[0].message.content
        
        # 验证并解析JSON
        profile_data = json.loads(profile_json_str)

        # 提取并返回 token 使用情况
        usage_data = response.usage
        token_info = {
            "prompt_tokens": usage_data.prompt_tokens,
            "completion_tokens": usage_data.completion_tokens,
            "total_tokens": usage_data.total_tokens
        }
        print(f"成功为 {category['id']} 生成画像。Token 使用: {token_info['total_tokens']}")
        return profile_data, token_info
        
    except Exception as e:
        print(f"为 {category['id']} 生成画像时出错: {e}")
        return None, None

def save_enhanced_categories(categories: list, output_path: Path):
    """将带有画像的分类数据保存到JSON文件"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
        print(f"\n成功将增强版分类数据保存到: {output_path}")
    except Exception as e:
        print(f"\n保存文件时出错: {e}")

def load_categories(file_path: Path) -> list:
    """从 JSON 文件加载分类信息"""
    if not file_path.exists():
        print(f"错误：找不到分类文件 {file_path}")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 从JSON结构中提取所有子分类
    all_subcategories = []
    for main_cat in data.get("arxiv_categories", {}).get("categories", []):
        all_subcategories.extend(main_cat.get("subcategories", []))
        
    return all_subcategories

def main():
    """主函数，协调整个画像生成过程"""
    print("开始生成 ArXiv 分类画像...")
    
    # 定义文件路径
    categories_file = project_root / "data" / "users" / "arxiv_categories_cn.json"
    
    # 加载分类
    categories = load_categories(categories_file)
    if not categories:
        print("未能加载分类，程序终止。")
        return
        
    print(f"成功加载 {len(categories)} 个分类。")
    
    # 初始化
    fetcher = ArxivFetcher()
    
    # 根据提供商选择加载参数
    provider = os.getenv("HEAVY_MODEL_PROVIDER", "dashscope").lower()
    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL_HEAVY", "qwen2:7b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        api_key = "ollama" # Ollama不需要key
    else: # 默认使用 DashScope
        model = os.getenv("QWEN_MODEL", "qwen-max")
        base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key and provider != "ollama":
        print("错误：缺少 API 密钥。请检查 .env 文件中的 DASHSCOPE_API_KEY。")
        return
        
    llm_provider = LLMProvider(model, base_url, api_key)
    print(f"\n已初始化 LLM 提供商，使用模型: {model}")

    token_usage_stats = {} # 用于存储 token 使用情况

    # 仅处理前两个分类，生成画像
    for i, category in enumerate(categories):
        print(f"\n--- 开始处理分类 {i+1}/{len(categories)}: {category['id']} ---")
        category_id = category['id']
        
        try:
            # 1. 获取代表性论文 (按年份和相关性)
            print(f"正在为分类 {category_id} 获取过去几年的代表性论文...")
            
            all_papers = []
            current_year = datetime.now().year
            years_to_scan = 5  # 回顾最近5年
            papers_per_year = 3 # 每年获取3篇

            for year in range(current_year, current_year - years_to_scan, -1):
                print(f"  正在查询年份: {year}")
                start_date = f"{year}0101"
                end_date = f"{year}1231"
                query = f"cat:{category_id} AND submittedDate:[{start_date} TO {end_date}]"
                
                papers = fetcher.fetch_papers_by_query(
                    search_query=query,
                    max_results=papers_per_year,
                    sort_by="relevance"
                )
                if papers:
                    all_papers.extend(papers)
                    print(f"    -> 找到 {len(papers)} 篇论文。")
                else:
                    print(f"    -> {year} 年未找到论文。")
            
            if not all_papers:
                print(f"在过去 {years_to_scan} 年中未能为分类 {category_id} 获取到任何论文，跳过此分类。")
                continue
            
            print(f"成功为 {category_id} 获取到 {len(all_papers)} 篇代表性论文。")
            
            # 2. 生成画像
            profile, token_info = generate_category_profile(llm_provider, category, all_papers)
            
            if profile and token_info:
                # 3. 将画像添加到分类数据中
                category['profile'] = profile
                token_usage_stats[category_id] = token_info
                print(f"成功将画像添加到分类 {category_id} 中。")
                # 打印部分结果以供验证
                print(json.dumps(profile, ensure_ascii=False, indent=2))
            else:
                print(f"为 {category_id} 生成画像失败，跳过此分类。")

            # 避免过于频繁的API调用
            if i < len(categories) - 1:
                wait_time = 2
                print(f"等待 {wait_time} 秒后处理下一个分类...")
                time.sleep(wait_time)

        except Exception as e:
            print(f"处理分类 {category_id} 时发生意外错误: {e}")
            continue

    print("\n--- 所有分类处理完成 ---")
    
    # 保存增强版的分类数据
    output_file_path = project_root / "data" / "users" / "arxiv_categories_enhanced.json"
    save_enhanced_categories(categories, output_file_path)

    # 保存 Token 使用统计数据
    token_usage_file_path = project_root / "tools" / "category_profiling_generator" / "token_usage.json"
    try:
        with open(token_usage_file_path, 'w', encoding='utf-8') as f:
            json.dump(token_usage_stats, f, ensure_ascii=False, indent=2)
        print(f"\n成功将 Token 使用统计数据保存到: {token_usage_file_path}")
    except Exception as e:
        print(f"\n保存 Token 使用统计文件时出错: {e}")


if __name__ == "__main__":
    main()