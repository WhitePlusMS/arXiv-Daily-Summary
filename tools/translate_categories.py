import json
import time
import os
from core.llm_provider import LLMProvider
from core.env_config import get_str, get_float, get_int
from loguru import logger

# --- 配置 ---
# 源文件路径
SOURCE_FILE = r'c:\Users\admin\Desktop\arxiv_recommender_v2\data\users\arxiv_categories_cn.json'
# 翻译后文件的保存路径
TARGET_FILE = r'c:\Users\admin\Desktop\arxiv_recommender_v2\data\users\arxiv_categories_cn_translated.json'

class CategoryTranslator:
    """
    使用LLM翻译ArXiv分类目录。
    """
    def __init__(self):
        """
        初始化翻译器，加载LLM提供商。
        """
        # 从环境变量读取通义千问配置
        qwen_model = get_str("QWEN_MODEL", "")
        dashscope_base_url = get_str("DASHSCOPE_BASE_URL", "")
        dashscope_api_key = get_str("DASHSCOPE_API_KEY", "")
        
        # 读取模型参数配置
        temperature = get_float("QWEN_MODEL_TEMPERATURE", 0.7)
        top_p = get_float("QWEN_MODEL_TOP_P", 0.9)
        max_tokens = get_int("QWEN_MODEL_MAX_TOKENS", 4000)

        if not all([qwen_model, dashscope_base_url, dashscope_api_key]):
            raise ValueError("错误：请确保 .env 文件中已配置 QWEN_MODEL, DASHSCOPE_BASE_URL, 和 DASHSCOPE_API_KEY")

        self.llm_provider = LLMProvider(
            model=qwen_model,
            base_url=dashscope_base_url,
            api_key=dashscope_api_key,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens
        )
        logger.info("LLMProvider 初始化成功，用于翻译。")

    def translate_text(self, text: str) -> str:
        """
        使用LLM翻译单个文本。
        """
        if not text or not isinstance(text, str):
            return ""
        
        prompt = LLMProvider.build_category_translation_prompt(text)
        try:
            # 使用较低的温度以获得更稳定、确定性的翻译结果
            translated_text = self.llm_provider.generate_response(prompt, temperature=0.1)
            return translated_text.strip()
        except Exception as e:
            logger.error(f"调用LLM翻译失败: {e}")
            return f"翻译失败: {e}"

    def translate_data(self, data: dict) -> dict:
        """
        遍历数据，翻译 'name' 和 'description' 字段。
        """
        categories = data.get("arxiv_categories", {}).get("categories", [])
        
        total_sub_cats = sum(len(main_cat.get("subcategories", [])) for main_cat in categories)
        processed_count = 0

        for main_cat in categories:
            logger.info(f"--- 正在处理主分类: {main_cat.get('main_category')} ---")
            for sub_cat in main_cat.get("subcategories", []):
                processed_count += 1
                sub_cat_id = sub_cat.get('id', '未知ID')
                
                logger.info(f"进度: {processed_count}/{total_sub_cats} | 正在翻译子分类: {sub_cat_id}")

                try:
                    # 翻译 name
                    original_name = sub_cat.get('name')
                    if original_name and 'name_cn' not in sub_cat:
                        logger.debug(f"翻译名称: '{original_name}'")
                        sub_cat['name_cn'] = self.translate_text(original_name)
                        time.sleep(0.2)  # 避免过于频繁的API调用

                    # 翻译 description
                    original_desc = sub_cat.get('description')
                    if original_desc and 'description_cn' not in sub_cat:
                        logger.debug(f"翻译描述: '{original_desc[:50]}...'")
                        sub_cat['description_cn'] = self.translate_text(original_desc)
                        time.sleep(0.2)

                except Exception as e:
                    logger.error(f"翻译 {sub_cat_id} 时发生未知错误: {e}")
                    continue
        return data

def main():
    """
    主函数，执行翻译流程。
    """
    logger.info(f"正在加载源文件: {SOURCE_FILE}")
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"错误: 未找到源文件 {SOURCE_FILE}")
        return
    except json.JSONDecodeError:
        logger.error(f"错误: 文件 {SOURCE_FILE} 不是有效的JSON格式。")
        return

    try:
        translator = CategoryTranslator()
        logger.info("开始翻译...")
        translated_data = translator.translate_data(source_data)
        
        logger.info(f"正在保存翻译文件到: {TARGET_FILE}")
        try:
            with open(TARGET_FILE, 'w', encoding='utf-8') as f:
                json.dump(translated_data, f, ensure_ascii=False, indent=2)
            logger.success(f"翻译成功！文件已保存到 {TARGET_FILE}")
        except Exception as e:
            logger.error(f"保存翻译文件时出错: {e}")

    except ValueError as e:
        logger.error(e)
        return


if __name__ == "__main__":
    # 配置loguru
    log_file_path = os.path.join(os.path.dirname(__file__), 'logs', 'translation.log')
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    logger.add(log_file_path, rotation="5 MB", level="DEBUG", encoding="utf-8")

    logger.info("=============================================")
    logger.info("      ArXiv 分类数据自动翻译脚本 (LLM版)")
    logger.info("=============================================")
    logger.info(f"源文件: {SOURCE_FILE}")
    logger.info(f"目标文件: {TARGET_FILE}")
    logger.info("本脚本将使用QWEN模型翻译 'name' 和 'description' 字段。")
    logger.info("请确保 .env 文件已正确配置。")
    logger.info("---------------------------------------------")
    main()