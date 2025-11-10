#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一提示词管理器

职责：
- 将默认提示词（config/prompts.default.json）作为初始值单一真源集中管理；
- 读取/合并用户自定义提示词（项目根目录 prompts.json）；
- 提供获取、更新、重置与渲染接口，供后端服务与核心模块使用；

说明：
- 前端可自由修改当前提示词；
- “重置为默认”即删除或覆盖自定义差异，恢复到默认文件内容；
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional
from copy import deepcopy
import re


class PromptManager:
    def __init__(self, defaults_path: Optional[Path] = None, custom_path: Optional[Path] = None):
        project_root = Path(__file__).parent.parent
        self.defaults_path = Path(defaults_path) if defaults_path else project_root / "config" / "prompts.default.json"
        # 将自定义覆盖文件的默认路径调整为 config/prompts.json
        default_custom_path = project_root / "config" / "prompts.json"
        self.custom_path = Path(custom_path) if custom_path else default_custom_path

        self._defaults: Dict[str, Dict[str, Any]] = self._load_json(self.defaults_path)

        # 兼容旧版根目录 prompts.json：若 config 下为空且根目录存在，则读取旧版作为有效自定义覆盖
        config_custom = self._load_json(self.custom_path)
        legacy_custom_path = project_root / "prompts.json"
        legacy_custom = self._load_json(legacy_custom_path)
        effective_custom = config_custom if config_custom else legacy_custom

        self._prompts: Dict[str, Dict[str, Any]] = self._merge_with_custom(self._defaults, effective_custom)

    # ===============
    # 内部工具方法
    # ===============
    def _load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _merge_with_custom(self, defaults: Dict[str, Dict[str, Any]], custom: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        merged = deepcopy(defaults)
        for key, data in (custom or {}).items():
            if key in merged and isinstance(merged[key], dict) and isinstance(data, dict):
                merged[key].update(data)
            else:
                merged[key] = data
        return merged

    def _compute_diff(self) -> Dict[str, Dict[str, Any]]:
        """计算当前提示词相对于默认值的差异，用于保存到 custom 文件。"""
        diffs: Dict[str, Dict[str, Any]] = {}
        for key, data in self._prompts.items():
            default_data = self._defaults.get(key, {})
            if not isinstance(data, dict):
                continue
            diff = {k: v for k, v in data.items() if default_data.get(k) != v}
            if diff:
                diffs[key] = diff
        return diffs

    def _save_custom(self):
        """保存自定义差异到 custom 文件（项目根目录 prompts.json）。"""
        diffs = self._compute_diff()
        with open(self.custom_path, 'w', encoding='utf-8') as f:
            json.dump(diffs, f, ensure_ascii=False, indent=4)

    # ===============
    # 对外接口
    # ===============
    def reload(self):
        """重新加载默认与自定义提示词。"""
        self._defaults = self._load_json(self.defaults_path)
        self._prompts = self._merge_with_custom(self._defaults, self._load_json(self.custom_path))

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        return self._prompts

    def get(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        return self._prompts.get(prompt_id)

    def get_template(self, prompt_id: str) -> Optional[str]:
        prompt = self.get(prompt_id)
        if not prompt:
            return None
        tpl = prompt.get("template")
        return tpl if isinstance(tpl, str) else None

    def update(self, prompt_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新提示词的可编辑字段：name/template"""
        if prompt_id not in self._prompts:
            raise KeyError("未找到指定的提示词")
        allowed_keys = {"name", "template"}
        updated = {k: v for k, v in updates.items() if k in allowed_keys}
        if not updated:
            raise ValueError("无可更新的字段")
        # 若更新了模板，则进行占位符与格式校验
        if "template" in updated and isinstance(updated["template"], str):
            tpl = updated["template"]
            # 更通用的占位符解析：提取花括号中的字段名，去除格式/变体标记
            raw_tokens = re.findall(r"\{([^{}]+)\}", tpl)
            field_names = []
            for tok in raw_tokens:
                base = re.split(r"[!:\.\[]", tok)[0].strip()
                if base:
                    field_names.append(base)
            placeholders = set[Any](field_names)
            allowed_vars = set[Any](self._prompts[prompt_id].get("variables") or [])
            unknown = placeholders - allowed_vars
            if unknown:
                unknown_list = ", ".join(sorted(unknown))
                allowed_list = ", ".join(sorted(allowed_vars))
                raise ValueError(
                    f"模板占位符不匹配：{unknown_list}；允许的变量：[{allowed_list}]。"
                    "修复建议：仅使用字母/数字/下划线的变量名，并与变量列表一致"
                )
            # 使用空值进行格式健全性检查（捕获花括号不配对、位置参数等问题）
            try:
                dummy = {k: "" for k in allowed_vars}
                tpl.format(**dummy)
            except KeyError as ke:
                # 格式渲染过程中发现缺失变量，抛出带缺失字段的 KeyError
                raise KeyError(str(ke))
            except IndexError as ie:
                # 位置占位符导致的索引错误
                raise ValueError(f"模板格式错误：{ie}")
            except ValueError as ve:
                raise ValueError(f"模板格式错误：{ve}")
        self._prompts[prompt_id].update(updated)
        self._save_custom()
        return deepcopy(self._prompts[prompt_id])

    def reset_prompt(self, prompt_id: str) -> Dict[str, Any]:
        if prompt_id not in self._prompts:
            raise KeyError("未找到指定的提示词")
        default_data = self._defaults.get(prompt_id)
        if not default_data:
            # 如果默认中不存在该ID，则移除自定义并返回当前（空）
            self._prompts.pop(prompt_id, None)
        else:
            self._prompts[prompt_id] = deepcopy(default_data)
        self._save_custom()
        return deepcopy(self._prompts.get(prompt_id, {}))

    def reset_all(self):
        """删除所有自定义，恢复到默认。"""
        self._prompts = deepcopy(self._defaults)
        if self.custom_path.exists():
            self.custom_path.unlink()
        # 不写入空文件，直接删除即可

    def render(self, prompt_id: str, variables: Dict[str, Any]) -> str:
        """使用 str.format 渲染模板。若变量缺失，抛出 KeyError。"""
        tpl = self.get_template(prompt_id)
        if not tpl:
            raise KeyError(f"未找到模板: {prompt_id}")
        return tpl.format(**variables)


# 便捷获取全局管理器（简单缓存）
_global_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = PromptManager()
    return _global_manager


def clear_prompt_manager_cache():
    """清除全局 PromptManager 缓存，强制下次获取时重新初始化"""
    global _global_manager
    _global_manager = None