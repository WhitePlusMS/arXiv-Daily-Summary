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
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.category_matcher import CategoryMatcher, MultiUserDataManager
from core.llm_provider import LLMProvider


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
        """加载现有的JSON数据"""
        # 获取项目根目录的绝对路径
        project_root = Path(__file__).parent.parent
        json_file = project_root / "data" / "users" / "user_categories.json"
        
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"加载JSON文件失败: {e}")
                return []
        return []

    def save_user_data(self, data):
        """保存用户数据到JSON文件"""
        # 获取项目根目录的绝对路径
        project_root = Path(__file__).parent.parent
        json_file = project_root / "data" / "users" / "user_categories.json"
        
        try:
            # 确保目录存在
            json_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存数据
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            st.error(f"保存JSON文件失败: {e}")
            return False

    def initialize_matcher(self):
        """初始化分类匹配器（缓存以提高性能）"""
        # 强制重新加载环境变量
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'), override=True)
        
        # 根据提供商选择加载参数
        provider = os.getenv("LIGHT_MODEL_PROVIDER", "dashscope").lower()

        if provider == "ollama":
            # 使用本地 OLLAMA
            model = os.getenv("OLLAMA_MODEL_LIGHT", "qwen3:0.6B")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            # OpenAI SDK 需要 api_key 参数，但本地 OLLAMA 实际不会验证；传入占位值即可
            api_key = os.getenv("OLLAMA_API_KEY", "ollama")
        else:
            # 默认使用 DashScope (通义千问) API
            model = os.getenv("QWEN_MODEL_LIGHT", "qwen-plus")
            base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            api_key = os.getenv("DASHSCOPE_API_KEY")
            
            if not api_key:
                st.error("❌ 请配置API密钥")
                st.info("请前往 **环境配置** 页面设置 DASHSCOPE_API_KEY")
                return None
        
        try:
            self.matcher = CategoryMatcher(model, base_url, api_key or "ollama")
            # 预热模型：对Ollama等本地服务首次加载较慢的情况进行一次小请求，降低冷启动失败概率
            try:
                self.matcher.warmup(attempts=10)
            except Exception:
                # 预热失败不影响后续流程
                pass
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
        provider = os.getenv("LIGHT_MODEL_PROVIDER", "dashscope").lower()
        if provider == "ollama":
            model = os.getenv("OLLAMA_MODEL_LIGHT", "qwen3:0.6B")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            api_key = os.getenv("OLLAMA_API_KEY", "ollama")
        else:
            model = os.getenv("QWEN_MODEL_LIGHT", "qwen-plus")
            base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            api_key = os.getenv("DASHSCOPE_API_KEY")
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
        results = self.matcher.match_categories_enhanced(
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
            data_manager = MultiUserDataManager("data/users/user_categories.json")
            data_manager.add_user_result(username, results, user_input)
            data_manager.save_to_json()
            return True
        except Exception as e:
            st.error(f"保存匹配结果失败: {e}")
            return False

    def get_detailed_score_files(self):
        """获取详细评分文件列表"""
        project_root = Path(__file__).parent.parent
        detailed_scores_dir = project_root / "data" / "users" / "detailed_scores"
        
        if detailed_scores_dir.exists():
            score_files = list(detailed_scores_dir.glob("*_detailed_scores.json"))
            if score_files:
                # 按修改时间排序（最新的在前）
                score_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return score_files
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
        provider = os.getenv("LIGHT_MODEL_PROVIDER", "dashscope").lower()
        
        if provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            model = os.getenv("OLLAMA_MODEL_LIGHT", "qwen3:0.6B")
            return {
                'provider': 'ollama',
                'model': model,
                'base_url': base_url,
                'configured': True
            }
        else:
            api_key = os.getenv("DASHSCOPE_API_KEY")
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
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'), override=True)