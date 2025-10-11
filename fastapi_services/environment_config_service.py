#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境配置服务 - FastAPI版本
提供 .env 的读取、保存、重新加载与恢复默认能力。
"""

import os
from pathlib import Path
from typing import Dict, Any, List

from .base_service import BaseService, ServiceResponse


class EnvConfigService(BaseService):
    """环境配置管理服务（无 Streamlit 依赖）"""

    def __init__(self):
        super().__init__("EnvConfigService")
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / ".env"
        self.env_example_file = self.project_root / ".env.example"
        self.config: Dict[str, Any] = {}
        self.load_config()

    def _parse_lines_to_config(self, lines: List[str]) -> Dict[str, Any]:
        cfg: Dict[str, Any] = {}
        for raw in lines:
            line = raw.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                cfg[key.strip()] = value.strip()
        return cfg

    async def get_config(self) -> ServiceResponse:
        """获取当前配置"""
        self.log_info("获取环境配置")
        return self.success_response(self.config, "获取配置成功")

    def load_config(self) -> None:
        """加载 .env 配置到内存"""
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                self.config = self._parse_lines_to_config(f.readlines())
        else:
            self.config = {}

    async def reload_config(self) -> ServiceResponse:
        """重新从 .env 读取配置"""
        self.log_info("重新加载 .env 配置")
        self.load_config()
        return self.success_response(self.config, "重新加载成功")

    async def save_config(self, new_config: Dict[str, Any]) -> ServiceResponse:
        """保存配置到 .env，保留原注释与未变更行"""
        try:
            self.log_info("保存环境配置", keys=list(new_config.keys()))
            self.env_file.parent.mkdir(parents=True, exist_ok=True)

            original_lines: List[str] = []
            if self.env_file.exists():
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    original_lines = f.readlines()

            updated_lines: List[str] = []
            updated_keys = set()

            for line in original_lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    if key in new_config:
                        updated_lines.append(f"{key}={new_config[key]}\n")
                        updated_keys.add(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)

            # 追加新的键
            for key, value in new_config.items():
                if key not in updated_keys:
                    updated_lines.append(f"\n{key}={value}\n")

            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)

            # 验证与刷新内存
            if not self.env_file.exists():
                return self.error_response(f"配置文件写入失败: {self.env_file}")
            self.load_config()
            return self.success_response({"saved": True}, "保存配置成功")
        except Exception as e:
            self.log_error("保存配置失败", e)
            return self.error_response(f"保存配置失败: {str(e)}")

    async def load_example_config(self) -> ServiceResponse:
        """读取 .env.example 并返回"""
        try:
            if not self.env_example_file.exists():
                return self.error_response("示例配置文件不存在")
            with open(self.env_example_file, 'r', encoding='utf-8') as f:
                example = self._parse_lines_to_config(f.readlines())
            return self.success_response(example, "示例配置加载成功")
        except Exception as e:
            self.log_error("加载示例配置失败", e)
            return self.error_response(f"加载示例配置失败: {str(e)}")

    async def restore_default(self) -> ServiceResponse:
        """将 .env.example 写入 .env 并重新加载"""
        try:
            self.log_info("恢复默认配置")
            ex = await self.load_example_config()
            if not ex.success or not isinstance(ex.data, dict):
                return self.error_response(ex.error or "示例配置加载失败")
            save_res = await self.save_config(ex.data)
            if not save_res.success:
                return save_res
            # 返回最新配置
            return await self.reload_config()
        except Exception as e:
            self.log_error("恢复默认配置失败", e)
            return self.error_response(f"恢复默认配置失败: {str(e)}")