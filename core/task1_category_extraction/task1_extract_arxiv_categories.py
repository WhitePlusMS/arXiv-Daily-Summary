#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv分类信息提取工具
从source.html文件中提取arXiv分类信息并按照指定格式输出到markdown文件
"""

import os
from bs4 import BeautifulSoup
import re

def extract_categories_from_html(html_file_path):
    """
    从HTML文件中提取arXiv分类信息
    
    Args:
        html_file_path (str): HTML文件路径
    
    Returns:
        dict: 分类信息字典，格式为 {主分类名: [(子分类ID, 子分类名, 描述), ...]}
    """
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    categories = {}
    
    # 查找所有主分类
    main_categories = soup.find_all('h2', class_='accordion-head')
    
    for main_cat in main_categories:
        main_category_name = main_cat.get_text().strip()
        categories[main_category_name] = []
        
        # 查找该主分类下的所有子分类
        accordion_body = main_cat.find_next_sibling('div', class_='accordion-body')
        if accordion_body:
            # 查找所有h4标签（子分类）
            subcategories = accordion_body.find_all('h4')
            
            for subcat in subcategories:
                # 提取分类ID和名称
                subcat_text = subcat.get_text().strip()
                
                # 使用正则表达式提取分类ID和名称
                # 格式: cs.AI (Artificial Intelligence)
                match = re.match(r'([a-z-]+\.[A-Z]+)\s*\((.+?)\)', subcat_text)
                if match:
                    category_id = match.group(1)
                    category_name = match.group(2)
                    
                    # 查找描述
                    description = ""
                    # 查找同一个columns divided容器中的描述段落
                    columns_div = subcat.find_parent('div', class_='columns divided')
                    if columns_div:
                        desc_p = columns_div.find('p')
                        if desc_p:
                            description = desc_p.get_text().strip()
                    
                    categories[main_category_name].append((category_id, category_name, description))
    
    return categories

def generate_markdown(categories, output_file_path):
    """
    生成markdown格式的分类文件
    
    Args:
        categories (dict): 分类信息字典
        output_file_path (str): 输出文件路径
    """
    with open(output_file_path, 'w', encoding='utf-8') as f:
        for main_category, subcategories in categories.items():
            # 写入主分类标题
            if main_category == "Computer Science":
                f.write(f"# {main_category}  计算机科学\n\n")
            elif main_category == "Economics":
                f.write(f"# {main_category}  经济学\n\n")
            else:
                f.write(f"# {main_category}\n\n")
            
            # 写入子分类
            for category_id, category_name, description in subcategories:
                f.write(f"## {category_id} ({category_name})\n\n")
                if description:
                    f.write(f"{description}\n\n")
                else:
                    f.write("\n")

def main():
    """
    主函数
    """
    # 文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = os.path.join(current_dir, 'source.html')
    output_file = os.path.join(current_dir, 'extracted_categories.md')
    
    # 检查HTML文件是否存在
    if not os.path.exists(html_file):
        print(f"错误: 找不到文件 {html_file}")
        return
    
    print("开始提取arXiv分类信息...")
    
    try:
        # 提取分类信息
        categories = extract_categories_from_html(html_file)
        
        # 生成markdown文件
        generate_markdown(categories, output_file)
        
        print(f"提取完成! 结果已保存到: {output_file}")
        print(f"共提取了 {len(categories)} 个主分类")
        
        # 统计子分类数量
        total_subcategories = sum(len(subcats) for subcats in categories.values())
        print(f"共提取了 {total_subcategories} 个子分类")
        
    except Exception as e:
        print(f"提取过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main()