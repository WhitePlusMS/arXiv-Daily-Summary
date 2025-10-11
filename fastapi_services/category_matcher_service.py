#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv 分类匹配器服务 - FastAPI版本
移除 Streamlit 依赖，提供后端API能力：优化描述、执行匹配、数据读写与管理。
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env', override=True)

from core.category_matcher import CategoryMatcher, MultiUserDataManager
from core.llm_provider import LLMProvider
from loguru import logger


class CategoryMatcherService:
    """分类匹配器业务逻辑服务（无Streamlit依赖）"""

    def __init__(self):
        self.matcher: Optional[CategoryMatcher] = None

    def _get_users_json_path(self) -> Path:
        return project_root / "data" / "users" / "user_categories.json"

    def _ensure_users_dir(self):
        path = self._get_users_json_path()
        path.parent.mkdir(parents=True, exist_ok=True)

    # 配置/提供商信息
    def get_provider_config(self) -> Dict[str, Any]:
        provider = os.getenv("LIGHT_MODEL_PROVIDER", "dashscope").lower()
        if provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            model = os.getenv("OLLAMA_MODEL_LIGHT", "qwen3:0.6B")
            return {
                "provider": "ollama",
                "model": model,
                "base_url": base_url,
                "configured": True
            }
        else:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            model = os.getenv("QWEN_MODEL_LIGHT", "qwen-plus")
            return {
                "provider": "dashscope",
                "model": model,
                "configured": bool(api_key)
            }

    # 数据读取/保存
    def load_existing_data(self) -> List[Dict[str, Any]]:
        json_path = self._get_users_json_path()
        if json_path.exists():
            try:
                import json
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_user_data(self, data: List[Dict[str, Any]]) -> bool:
        self._ensure_users_dir()
        import json
        try:
            with open(self._get_users_json_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def get_statistics(self, existing_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not existing_data:
            return {"total_records": 0, "unique_users": 0}
        usernames = [item.get('username', 'Unknown') for item in existing_data]
        return {"total_records": len(existing_data), "unique_users": len(set(usernames))}

    # 匹配器初始化
    def initialize_matcher(self) -> Optional[CategoryMatcher]:
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
                return None
        try:
            self.matcher = CategoryMatcher(model, base_url, api_key or "ollama")
            try:
                self.matcher.warmup(attempts=5)
            except Exception:
                pass
            return self.matcher
        except Exception:
            return None

    # AI优化描述
    def optimize_research_description(self, user_input: str) -> str:
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

    # 执行匹配
    def execute_matching(self, user_input: str, username: str, top_n: int = 5):
        if not self.matcher:
            matcher = self.initialize_matcher()
            if matcher is None:
                raise Exception("匹配器未初始化或API密钥未配置")

        # 重置Token计数
        if hasattr(self.matcher, 'total_tokens'):
            self.matcher.total_tokens = 0
            self.matcher.total_input_tokens = 0
            self.matcher.total_output_tokens = 0

        # 执行匹配
        results: List[Tuple[str, str, int]] = self.matcher.match_categories_enhanced(
            user_input,
            top_n=top_n,
            save_detailed=True,
            username=username
        )

        # 返回结构化结果及token使用情况
        token_usage = None
        if hasattr(self.matcher, 'total_tokens'):
            token_usage = {
                'inputTokens': getattr(self.matcher, 'total_input_tokens', 0),
                'outputTokens': getattr(self.matcher, 'total_output_tokens', 0),
                'totalTokens': getattr(self.matcher, 'total_tokens', 0),
            }

        return [{
            'id': r[0], 'name': r[1], 'score': r[2]
        } for r in results], token_usage

    # 保存匹配结果
    def save_matching_results(self, username: str, user_input: str, results: List[Dict[str, Any]]) -> bool:
        try:
            # 确保输出目录存在，避免因目录缺失导致写入失败
            self._ensure_users_dir()

            # 统一输出路径为绝对路径，避免工作目录差异导致未写入
            output_path = str(self._get_users_json_path())
            logger.info(f"保存匹配结果到: {output_path}")
            data_manager = MultiUserDataManager(output_path)

            # 兼容不同结果结构：将 dict 列表转换为 (id, name, score) 元组列表
            top_matches: List[Tuple[str, str, int]] = []
            if results and isinstance(results[0], dict):
                for r in results:
                    cid = r.get('id') or r.get('category_id')
                    name = r.get('name') or r.get('category_name') or ''
                    score = int(r.get('score') or 0)
                    if cid:
                        top_matches.append((cid, name, score))
            else:
                # 已是元组形式
                top_matches = [(r[0], r[1], int(r[2])) for r in results]  # type: ignore

            # 调用数据管理器保存（追加模式）
            data_manager.add_user_result(username, top_matches, user_input)
            data_manager.save_to_json()
            return True
        except Exception as e:
            logger.error(f"保存匹配结果失败: {e}")
            return False

    # 详细评分文件管理
    def list_detailed_score_files(self) -> List[Dict[str, Any]]:
        detailed_scores_dir = project_root / "data" / "users" / "detailed_scores"
        if not detailed_scores_dir.exists():
            return []
        files = list(detailed_scores_dir.glob("*_detailed_scores.json"))
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return [{
            'name': f.name,
            'size': f.stat().st_size,
            'time': f.stat().st_mtime,
            'path': str(f)
        } for f in files]

    def read_score_file_content(self, name: str) -> str:
        detailed_scores_dir = project_root / "data" / "users" / "detailed_scores"
        file_path = detailed_scores_dir / name
        if not file_path.exists():
            raise FileNotFoundError("评分文件不存在")
        return file_path.read_text(encoding='utf-8')

    def delete_score_file(self, name: str) -> bool:
        detailed_scores_dir = project_root / "data" / "users" / "detailed_scores"
        file_path = detailed_scores_dir / name
        if not file_path.exists():
            return False
        file_path.unlink(missing_ok=False)
        return True

    # 记录管理
    def batch_delete_records(self, indices: List[int]) -> int:
        data = self.load_existing_data()
        if not data:
            return 0
        # 倒序删除
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(data):
                data.pop(idx)
        self.save_user_data(data)
        return len(indices)

    def update_record(self, index: int, username: str, category_id: str, user_input: str) -> bool:
        data = self.load_existing_data()
        if 0 <= index < len(data):
            data[index]['username'] = username
            data[index]['category_id'] = category_id
            data[index]['user_input'] = user_input
            return self.save_user_data(data)
        return False

    def delete_single_record(self, index: int) -> bool:
        data = self.load_existing_data()
        if 0 <= index < len(data):
            data.pop(index)
            return self.save_user_data(data)
        return False