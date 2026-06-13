"""用户研究配置读取工具。

集中处理 data/users/user_categories.json 的读取、用户选择和字段解析。
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


DEFAULT_RESEARCH_INTERESTS = {
    "positive_query": "机器学习、深度学习、计算机视觉、自然语言处理",
    "negative_query": "",
}


def load_user_config_records(config_path: str | Path) -> List[Dict[str, Any]]:
    """读取用户配置记录，失败时返回空列表。"""
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"用户分类文件不存在: {path}")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON文件解析失败: {e}")
        return []
    except Exception as e:
        logger.error(f"用户分类文件读取失败: {e}")
        return []

    if not isinstance(data, list):
        logger.warning(f"用户分类文件格式不正确: {path}")
        return []

    return [item for item in data if isinstance(item, dict)]


def select_user_config(records: List[Dict[str, Any]], username: Optional[str]) -> Optional[Dict[str, Any]]:
    """按用户名选择配置；未指定或未命中时使用第一条记录。"""
    if not records:
        return None

    if username:
        for record in records:
            if record.get("username") == username:
                logger.debug(f"找到指定用户配置: {username}")
                return record
        logger.warning(f"未找到用户 {username} 的配置，使用第一个用户配置")
    else:
        logger.debug("未指定用户名，使用第一个用户配置")

    return records[0]


def load_selected_user_config(config_path: str | Path, username: Optional[str]) -> Optional[Dict[str, Any]]:
    """读取并选择当前用户配置。"""
    records = load_user_config_records(config_path)
    return select_user_config(records, username)


def get_username_from_config(config_path: str | Path, username: Optional[str], default: str = "TEST") -> str:
    """获取当前用户名。"""
    if username:
        return username

    user_config = load_selected_user_config(config_path, None)
    if user_config and user_config.get("username"):
        return str(user_config["username"])
    return default


def parse_user_categories(user_config: Optional[Dict[str, Any]]) -> List[str]:
    """从用户配置解析 arXiv 分类列表。"""
    if not user_config:
        return []

    category_str = str(user_config.get("category_id") or "").strip()
    if not category_str:
        return []

    return [cat.strip() for cat in category_str.split(",") if cat.strip()]


def parse_research_interests(user_config: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """从用户配置解析正向与负向研究兴趣。"""
    if not user_config:
        return DEFAULT_RESEARCH_INTERESTS.copy()

    positive_query = str(user_config.get("user_input") or "")
    negative_query = str(user_config.get("negative_query") or "")
    if not positive_query:
        return DEFAULT_RESEARCH_INTERESTS.copy()

    return {
        "positive_query": positive_query,
        "negative_query": negative_query,
    }
