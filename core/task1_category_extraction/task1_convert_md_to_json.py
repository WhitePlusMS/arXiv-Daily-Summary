#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv分类信息Markdown转JSON工具
从extracted_categories.md文件中解析分类信息并转换为JSON格式
"""

import os
import json
import re

def parse_markdown_categories(md_file_path):
    """
    从Markdown文件中解析arXiv分类信息
    
    Args:
        md_file_path (str): Markdown文件路径
    
    Returns:
        dict: 分类信息字典，格式为 {主分类名: [{"id": 子分类ID, "name": 子分类名, "description": 描述}, ...]}
    """
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    categories = {}
    current_main_category = None
    
    # 按行处理
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 检查是否是主分类标题 (以 # 开头)
        if line.startswith('# ') and not line.startswith('## '):
            # 提取主分类名称，去掉可能的中文翻译
            main_category_text = line[2:].strip()
            # 去掉中文部分（如果存在）
            if '  ' in main_category_text:
                current_main_category = main_category_text.split('  ')[0].strip()
            else:
                current_main_category = main_category_text
            
            categories[current_main_category] = []
        
        # 检查是否是子分类标题 (以 ## 开头)
        elif line.startswith('## ') and current_main_category:
            # 提取子分类信息
            subcat_text = line[3:].strip()
            
            # 使用正则表达式提取分类ID和名称
            # 格式: cs.AI (Artificial Intelligence)
            match = re.match(r'([a-z-]+\.[A-Z]+)\s*\((.+?)\)', subcat_text)
            if match:
                category_id = match.group(1)
                category_name = match.group(2)
                
                # 查找描述（下一个非空行）
                description = ""
                j = i + 1
                while j < len(lines):
                    desc_line = lines[j].strip()
                    if desc_line and not desc_line.startswith('#'):
                        # 收集描述内容，直到遇到下一个标题或空行
                        desc_parts = []
                        while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith('#'):
                            desc_parts.append(lines[j].strip())
                            j += 1
                        description = ' '.join(desc_parts)
                        break
                    j += 1
                
                # 添加到当前主分类
                categories[current_main_category].append({
                    "id": category_id,
                    "name": category_name,
                    "description": description
                })
        
        i += 1
    
    return categories

def generate_json(categories, output_file_path):
    """
    生成JSON格式的分类文件
    
    Args:
        categories (dict): 分类信息字典
        output_file_path (str): 输出文件路径
    """
    # 创建更结构化的JSON格式
    json_data = {
        "arxiv_categories": {
            "metadata": {
                "total_main_categories": len(categories),
                "total_subcategories": sum(len(subcats) for subcats in categories.values()),
                "generated_from": "extracted_categories.md"
            },
            "categories": []
        }
    }
    
    # 转换分类数据
    for main_category, subcategories in categories.items():
        category_data = {
            "main_category": main_category,
            "subcategory_count": len(subcategories),
            "subcategories": subcategories
        }
        json_data["arxiv_categories"]["categories"].append(category_data)
    
    # 写入JSON文件
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

def main():
    """
    主函数
    """
    # 文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    md_file = os.path.join(current_dir, 'extracted_categories.md')
    output_file = os.path.join(current_dir, 'arxiv_categories.json')
    
    # 检查Markdown文件是否存在
    if not os.path.exists(md_file):
        print(f"错误: 找不到文件 {md_file}")
        return
    
    print("开始转换Markdown文件为JSON格式...")
    
    try:
        # 解析Markdown文件
        categories = parse_markdown_categories(md_file)
        
        # 生成JSON文件
        generate_json(categories, output_file)
        
        print(f"转换完成! 结果已保存到: {output_file}")
        print(f"共转换了 {len(categories)} 个主分类")
        
        # 统计子分类数量
        total_subcategories = sum(len(subcats) for subcats in categories.values())
        print(f"共转换了 {total_subcategories} 个子分类")
        
        # 显示部分转换结果
        print("\n转换结果预览:")
        for main_cat, subcats in list(categories.items())[:2]:  # 只显示前2个主分类
            print(f"- {main_cat}: {len(subcats)} 个子分类")
            for subcat in subcats[:3]:  # 每个主分类只显示前3个子分类
                print(f"  - {subcat['id']}: {subcat['name']}")
            if len(subcats) > 3:
                print(f"  - ... 还有 {len(subcats) - 3} 个子分类")
        
        if len(categories) > 2:
            print(f"... 还有 {len(categories) - 2} 个主分类")
        
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()