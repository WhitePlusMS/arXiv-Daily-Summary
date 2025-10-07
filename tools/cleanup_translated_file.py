import json
import os
from loguru import logger

# --- 配置 ---
# 目标文件路径 (即需要被清理的文件)
TARGET_FILE = r'c:\Users\admin\Desktop\arxiv_recommender_v2\data\users\arxiv_categories_cn_translated.json'

def cleanup_data(data: dict) -> dict:
    """
    遍历数据，删除每个子分类下的 'name' 和 'description' 字段。
    """
    categories = data.get("arxiv_categories", {}).get("categories", [])
    
    for main_cat in categories:
        for sub_cat in main_cat.get("subcategories", []):
            sub_cat_id = sub_cat.get('id', '未知ID')
            logger.debug(f"正在处理子分类: {sub_cat_id}")
            
            # 删除 name 字段
            if 'name' in sub_cat:
                del sub_cat['name']
                logger.trace(f"  - 已删除 'name' 字段")
            
            # 删除 description 字段
            if 'description' in sub_cat:
                del sub_cat['description']
                logger.trace(f"  - 已删除 'description' 字段")
                
    return data

def main():
    """
    主函数，执行清理流程。
    """
    logger.info(f"正在加载目标文件: {TARGET_FILE}")
    try:
        with open(TARGET_FILE, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"错误: 未找到目标文件 {TARGET_FILE}")
        return
    except json.JSONDecodeError:
        logger.error(f"错误: 文件 {TARGET_FILE} 不是有效的JSON格式。")
        return

    logger.info("开始清理文件，删除 'name' 和 'description' 字段...")
    cleaned_data = cleanup_data(source_data)
    
    logger.info(f"正在将清理后的数据写回原文件: {TARGET_FILE}")
    try:
        with open(TARGET_FILE, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        logger.success(f"清理成功！文件已更新。")
    except Exception as e:
        logger.error(f"保存文件时出错: {e}")

if __name__ == "__main__":
    # 配置loguru
    log_file_path = os.path.join(os.path.dirname(__file__), 'logs', 'cleanup.log')
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    logger.add(log_file_path, rotation="1 MB", level="DEBUG", encoding="utf-8")

    logger.info("=============================================")
    logger.info("      清理已翻译分类文件脚本")
    logger.info("=============================================")
    logger.info(f"目标文件: {TARGET_FILE}")
    logger.info("本脚本将从此文件中删除原始的 'name' 和 'description' 字段。")
    logger.info("操作将直接修改原文件，请提前备份（如果需要）。")
    logger.info("---------------------------------------------")
    main()