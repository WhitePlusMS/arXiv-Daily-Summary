#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词管理服务 - FastAPI版本
定位：仅作为 HTTP API 包装层，对外提供提示词读取/更新/重置能力。
所有提示词的业务逻辑与单一真源由 core.prompt_manager.PromptManager 统一维护；
此服务不直接持有业务状态，不新增业务逻辑，仅做委托转发与错误包装。
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from copy import deepcopy

from .base_service import BaseService, ServiceResponse
from core.prompt_manager import get_prompt_manager, PromptManager

# 默认提示词改为引用统一模块，避免在此文件重复定义

class PromptService(BaseService):
    """提示词管理服务"""

    def __init__(self):
        super().__init__("PromptService")
        self.project_root = Path(__file__).parent.parent
        self.manager: PromptManager = get_prompt_manager()

    # 由 PromptManager 统一负责加载与保存，无需本地实现

    async def get_all_prompts(self) -> ServiceResponse:
        """获取所有提示词的列表"""
        # 重新加载以确保获取最新的提示词（包括新添加的）
        self.manager.reload()
        prompts = self.manager.get_all()
        return self.success_response(
            [{"id": k, **v} for k, v in prompts.items()],
            "成功获取所有提示词"
        )

    async def get_prompt(self, prompt_id: str) -> ServiceResponse:
        """获取单个提示词的详细信息"""
        prompt = self.manager.get(prompt_id)
        if prompt:
            return self.success_response({"id": prompt_id, **prompt}, "成功获取提示词")
        return self.error_response("未找到指定的提示词", status_code=404)

    async def update_prompt(self, prompt_id: str, updates: Dict[str, Any]) -> ServiceResponse:
        """更新一个提示词模板"""
        try:
            updated = self.manager.update(prompt_id, updates)
            return self.success_response({"id": prompt_id, **updated}, "提示词更新成功")
        except KeyError as e:
            # 区分提示词不存在与模板变量缺失两种情况
            msg = str(e)
            if msg == "未找到指定的提示词":
                return self.error_response("未找到指定的提示词", status_code=404)
            # KeyError("'missing_field'")
            return self.error_response(msg, status_code=400)
        except ValueError as e:
            return self.error_response(str(e), status_code=400)
        except Exception as e:
            self.log_error(f"更新提示词失败: {e}")
            # 尝试重新加载以保持一致
            self.manager.reload()
            return self.error_response(f"保存提示词失败: {e}", status_code=500)

    async def reset_prompt(self, prompt_id: str) -> ServiceResponse:
        """重置单个提示词为默认版本"""
        try:
            data = self.manager.reset_prompt(prompt_id)
            return self.success_response({"id": prompt_id, **data}, "提示词重置成功")
        except KeyError:
            return self.error_response("未找到指定的提示词", status_code=404)
        except Exception as e:
            self.log_error(f"重置提示词失败: {e}")
            self.manager.reload()
            return self.error_response(f"保存提示词失败: {e}", status_code=500)

    async def reset_all_prompts(self) -> ServiceResponse:
        """重置所有提示词为默认版本"""
        try:
            self.manager.reset_all()
            return self.success_response(None, "所有提示词已成功重置为默认值")
        except Exception as e:
            self.log_error(f"重置所有提示词失败: {e}")
            return self.error_response(f"重置所有提示词失败: {e}", status_code=500)

    # 提示：保存逻辑由 PromptManager 维护；
    # LLMProvider 等核心模块应直接依赖 PromptManager，而非通过服务层访问。