#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv分类匹配器服务 - 业务逻辑层
"""

import json
import os
import sys
from typing import List, Dict, Any, Tuple
from datetime import datetime
import datetime as dt
import streamlit as st

# 添加项目根目录到 Python 路径
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.category_matcher import CategoryMatcher, MultiUserDataManager
from core.llm_provider import LLMProvider
from core.env_config import get_str, reload


class CategoryMatcherService:
    """ArXiv分类匹配器业务逻辑服务类"""
    
    def __init__(self):
        self.matcher = None
        self.data_manager = None
        
    @staticmethod
    def get_service():
        """获取或创建分类匹配服务实例"""
        if 'category_matcher_service' not in st.session_state:
            st.session_state.category_matcher_service = CategoryMatcherService()
        return st.session_state.category_matcher_service
    
    def load_existing_data(self):
        """加载现有的用户数据"""
        try:
            project_root = Path(__file__).parent.parent.parent
            data_file = project_root / "data" / "users" / "user_categories.json"
            
            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            st.error(f"加载数据时出错: {str(e)}")
            return []

    def save_user_data(self, data):
        """保存用户数据到文件"""
        try:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data" / "users"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            data_file = data_dir / "user_categories.json"
            
            # 确保数据是可序列化的
            serializable_data = []
            for item in data:
                if isinstance(item, dict):
                    serializable_item = {}
                    for key, value in item.items():
                        if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                            serializable_item[key] = value
                        else:
                            serializable_item[key] = str(value)
                    serializable_data.append(serializable_item)
                else:
                    serializable_data.append(str(item))
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            st.error(f"保存数据时出错: {str(e)}")
            return False

    def initialize_matcher(self):
        """初始化分类匹配器（缓存以提高性能）"""
        # 强制重新加载环境变量
        reload()
        
        # 统一使用 DashScope (通义千问) API
        model = get_str("QWEN_MODEL_LIGHT", "qwen-plus")
        base_url = get_str("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        api_key = get_str("DASHSCOPE_API_KEY", "")
        
        if not api_key:
            st.error("❌ 请配置API密钥")
            st.info("请前往 **环境配置** 页面设置 DASHSCOPE_API_KEY")
            return None
        
        try:
            self.matcher = CategoryMatcher(model, base_url, api_key)
            return self.matcher
        except Exception as e:
            st.error(f"❌ 初始化匹配器失败: {e}")
            st.stop()

    def create_results_chart_data(self, results: List[Tuple[str, str, int]]):
        """创建结果可视化图表数据"""
        if not results:
            return None
        
        import pandas as pd
        # 准备数据用于Streamlit内置图表
        chart_data = pd.DataFrame({
            '分类ID': [r[0] for r in results],
            '分类名称': [r[1][:20] + '...' if len(r[1]) > 20 else r[1] for r in results],
            '匹配评分': [r[2] for r in results]
        })
        
        return chart_data

    def get_token_usage_data(self, matcher):
        """获取Token使用统计数据"""
        if hasattr(matcher, 'total_tokens') and matcher.total_tokens > 0:
            return {
                'total_input_tokens': matcher.total_input_tokens,
                'total_output_tokens': matcher.total_output_tokens,
                'total_tokens': matcher.total_tokens
            }
        return None

    def optimize_research_description(self, user_input):
        """使用AI优化研究描述"""
        # 初始化LLM提供商
        model = get_str("QWEN_MODEL_LIGHT", "qwen-plus")
        base_url = get_str("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        api_key = get_str("DASHSCOPE_API_KEY", "")
        if not api_key:
            raise Exception("请配置API密钥")
        
        llm_provider = LLMProvider(model, base_url, api_key)
        return llm_provider.optimize_research_description(user_input)

    def execute_matching(self, user_input, username, top_n=5):
        """执行分类匹配"""
        if not self.matcher:
            raise Exception("匹配器未初始化")
        
        # 重置Token计数器
        if hasattr(self.matcher, 'total_tokens'):
            self.matcher.total_tokens = 0
            self.matcher.total_input_tokens = 0
            self.matcher.total_output_tokens = 0
        
        # 执行实际匹配
        results = self.matcher.match_categories(
            user_input, 
            top_n=top_n, 
            save_detailed=True, 
            username=username
        )
        
        return results

    def save_matching_results(self, username, user_input, results):
        """保存匹配结果到数据库"""
        try:
            # 使用 MultiUserDataManager 保存结果
            data_manager = MultiUserDataManager("../../data/users/user_categories.json")
            data_manager.add_user_result(username, results, user_input)
            data_manager.save_to_json()
            return True
        except Exception as e:
            st.error(f"保存匹配结果失败: {e}")
            return False

    def get_detailed_score_files(self):
        """获取详细评分文件列表"""
        try:
            project_root = Path(__file__).parent.parent.parent
            score_dir = project_root / "data" / "users" / "detailed_scores"
            
            if not score_dir.exists():
                return []
            
            files = []
            for file_path in score_dir.glob("*.json"):
                files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                })
            
            return sorted(files, key=lambda x: x['modified'], reverse=True)
        except Exception as e:
            st.error(f"获取文件列表时出错: {str(e)}")
            return []

    def delete_score_file(self, file_path):
        """删除评分文件"""
        try:
            file_path.unlink()
            return True, f"已删除文件: {file_path.name}"
        except Exception as e:
            return False, f"删除文件失败: {e}"

    def get_file_info(self, file_path):
        """获取文件信息"""
        # 如果传入的是字典（来自get_detailed_score_files），直接返回
        if isinstance(file_path, dict):
            return {
                'name': file_path.get('name', ''),
                'size': file_path.get('size', 0),
                'time': file_path.get('modified', datetime.now()).strftime("%Y-%m-%d %H:%M:%S") if isinstance(file_path.get('modified'), datetime) else str(file_path.get('modified', ''))
            }
        
        # 如果传入的是路径字符串，转换为Path对象
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # 处理Path对象
        return {
            'name': file_path.name,
            'size': file_path.stat().st_size,
            'time': dt.datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        }

    def read_file_content(self, file_path):
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"读取文件失败: {e}")

    def filter_data(self, data, search_term):
        """过滤数据"""
        if not search_term:
            return data
        
        return [
            item for item in data
            if search_term.lower() in item.get('username', '').lower() or
               search_term.lower() in item.get('user_input', '').lower() or
               search_term.lower() in item.get('category_id', '').lower()
        ]

    def batch_delete_records(self, existing_data, selected_indices):
        """批量删除记录"""
        indices_to_delete = sorted(selected_indices, reverse=True)
        for idx in indices_to_delete:
            if 0 <= idx < len(existing_data):
                existing_data.pop(idx)
        
        # 保存到文件
        self.save_user_data(existing_data)
        return len(indices_to_delete)

    def update_record(self, existing_data, original_index, new_username, new_category_id, new_user_input):
        """更新记录"""
        existing_data[original_index]['username'] = new_username
        existing_data[original_index]['category_id'] = new_category_id
        existing_data[original_index]['user_input'] = new_user_input
        
        # 保存到文件
        return self.save_user_data(existing_data)

    def delete_single_record(self, existing_data, original_index):
        """删除单条记录"""
        existing_data.pop(original_index)
        return self.save_user_data(existing_data)

    def export_data_to_json(self, filtered_data):
        """导出数据为JSON格式"""
        import json
        return json.dumps(filtered_data, ensure_ascii=False, indent=2)

    def get_provider_config(self):
        """获取提供商配置信息"""
        api_key = get_str("DASHSCOPE_API_KEY", "")
        return {
            'provider': 'dashscope',
            'configured': bool(api_key)
        }

    def get_statistics(self, existing_data):
        """获取统计信息"""
        if existing_data:
            usernames = [item.get('username', 'Unknown') for item in existing_data]
            unique_users = len(set(usernames))
            return {
                'total_records': len(existing_data),
                'unique_users': unique_users
            }
        return None

    def clear_caches(self):
        """清除缓存"""
        st.cache_data.clear()
        st.cache_resource.clear()
        # 强制重新加载环境变量
        reload()