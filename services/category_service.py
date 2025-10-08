#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分类服务 - 处理ArXiv分类数据的加载和管理
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import streamlit as st


class CategoryService:
    """ArXiv分类数据服务类"""
    
    def __init__(self):
        """初始化分类服务"""
        self.base_path = Path(__file__).parent.parent
        self.categories_data = None
    
    def load_categories_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        加载并合并ArXiv分类数据
        
        Returns:
            List[Dict[str, Any]]: 合并后的分类数据列表，如果加载失败返回None
        """
        try:
            # 如果已经加载过数据，直接返回缓存
            if self.categories_data is not None:
                return self.categories_data
            
            # 加载原始分类数据
            original_file = self.base_path / "data" / "users" / "arxiv_categories.json"
            if not original_file.exists():
                error_msg = f"错误：找不到原始分类文件 {original_file}"
                print(error_msg)
                st.error(error_msg)
                return None
            
            with open(original_file, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
            
            # 提取分类数据
            categories_data = original_data['arxiv_categories']['categories']
            
            # 加载翻译数据
            translated_file = self.base_path / "data" / "users" / "arxiv_categories_cn.json"
            translated_data = {}
            
            if translated_file.exists():
                try:
                    with open(translated_file, 'r', encoding='utf-8') as f:
                        translated_raw_data = json.load(f)
                    # 提取翻译数据并转换为字典格式
                    translated_categories = translated_raw_data['arxiv_categories']['categories']
                    translated_data = {}
                    for main_cat in translated_categories:
                        for sub_cat in main_cat['subcategories']:
                            translated_data[sub_cat['id']] = {
                                'name_cn': sub_cat.get('name_cn', ''),
                                'description_cn': sub_cat.get('description_cn', '')
                            }
                except Exception as e:
                    print(f"警告：加载翻译文件失败 {e}，将使用原始数据")
            else:
                print(f"警告：找不到翻译文件 {translated_file}，将使用原始数据")
            
            # 合并数据
            merged_categories = self._merge_category_data(categories_data, translated_data)
            
            # 缓存数据
            self.categories_data = merged_categories
            
            return merged_categories
            
        except Exception as e:
            error_msg = f"加载分类数据时发生错误: {e}"
            print(error_msg)
            st.error(error_msg)
            return None
    
    def _merge_category_data(self, original_data: List[Dict], translated_data: Dict) -> List[Dict[str, Any]]:
        """
        合并原始数据和翻译数据
        
        Args:
            original_data: 原始分类数据
            translated_data: 翻译数据
            
        Returns:
            List[Dict[str, Any]]: 合并后的数据
        """
        merged_categories = []
        
        for category in original_data:
            main_category = category['main_category']
            
            # 创建合并后的分类对象
            merged_category = {
                'main_category': main_category,
                'subcategories': []
            }
            
            # 处理子分类
            for subcat in category['subcategories']:
                subcat_id = subcat['id']
                
                # 创建合并后的子分类对象
                merged_subcat = {
                    'id': subcat_id,
                    'name': subcat['name'],
                    'description': subcat['description']
                }
                
                # 添加翻译信息（如果存在）
                if subcat_id in translated_data:
                    translation = translated_data[subcat_id]
                    merged_subcat['name_cn'] = translation.get('name_cn', '')
                    merged_subcat['description_cn'] = translation.get('description_cn', '')
                else:
                    merged_subcat['name_cn'] = ''
                    merged_subcat['description_cn'] = ''
                
                merged_category['subcategories'].append(merged_subcat)
            
            merged_categories.append(merged_category)
        
        return merged_categories
    
    def get_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        """
        根据分类ID获取分类信息
        
        Args:
            category_id: 分类ID
            
        Returns:
            Optional[Dict[str, Any]]: 分类信息，如果未找到返回None
        """
        if self.categories_data is None:
            self.load_categories_data()
        
        if self.categories_data is None:
            return None
        
        for category in self.categories_data:
            for subcat in category['subcategories']:
                if subcat['id'] == category_id:
                    return subcat
        
        return None
    
    def get_main_categories(self) -> List[str]:
        """
        获取所有主分类名称
        
        Returns:
            List[str]: 主分类名称列表
        """
        if self.categories_data is None:
            self.load_categories_data()
        
        if self.categories_data is None:
            return []
        
        return [cat['main_category'] for cat in self.categories_data]
    
    def get_subcategories_by_main(self, main_category: str) -> List[Dict[str, Any]]:
        """
        根据主分类获取所有子分类
        
        Args:
            main_category: 主分类名称
            
        Returns:
            List[Dict[str, Any]]: 子分类列表
        """
        if self.categories_data is None:
            self.load_categories_data()
        
        if self.categories_data is None:
            return []
        
        for category in self.categories_data:
            if category['main_category'] == main_category:
                return category['subcategories']
        
        return []
    
    def search_categories(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索包含关键词的分类
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[Dict[str, Any]]: 匹配的分类列表
        """
        if self.categories_data is None:
            self.load_categories_data()
        
        if self.categories_data is None:
            return []
        
        results = []
        keyword_lower = keyword.lower()
        
        for category in self.categories_data:
            for subcat in category['subcategories']:
                # 在ID、名称、描述中搜索
                if (keyword_lower in subcat['id'].lower() or
                    keyword_lower in subcat['name'].lower() or
                    keyword_lower in subcat['description'].lower() or
                    keyword_lower in subcat.get('name_cn', '').lower() or
                    keyword_lower in subcat.get('description_cn', '').lower()):
                    results.append(subcat)
        
        return results