"""集中化的 .env 配置读取模块

为 core 目录下的代码提供统一的配置访问入口，避免各处直接使用
`os.getenv` 或自行加载 `.env`。该模块直接解析项目根目录下的
`.env` 文件，并提供类型安全的读取方法。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

from dotenv import dotenv_values


class EnvConfig:
    """集中化的 .env 配置管理器。

    - 仅解析 `.env` 文件，不污染进程环境变量。
    - 提供类型化读取方法，保持与现有默认值处理一致。
    - 可调用 `reload()` 在写入 `.env` 后刷新内存配置。
    """

    def __init__(self, env_path: Optional[Union[str, Path]] = None) -> None:
        self.project_root = Path(__file__).resolve().parent.parent
        self.env_file = Path(env_path) if env_path else self.project_root / ".env"
        self._values: Dict[str, str] = {}
        self.reload()

    def reload(self) -> None:
        """重新解析 `.env` 到内存字典，忽略无效项。"""
        try:
            if self.env_file.exists():
                raw = dotenv_values(self.env_file)
                # 过滤 None 并统一为字符串
                self._values = {
                    str(k): str(v)
                    for k, v in (raw or {}).items()
                    if k is not None and v is not None
                }
            else:
                self._values = {}
        except Exception:
            # 保守兜底：出现解析异常时提供空配置
            self._values = {}

    def all(self) -> Dict[str, str]:
        """返回当前内存中的全部键值副本。"""
        return dict(self._values)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取字符串值；不存在则返回默认值。"""
        return self._values.get(key, default)

    def get_str(self, key: str, default: str) -> str:
        v = self.get(key)
        return default if v is None else v

    def get_int(self, key: str, default: int) -> int:
        v = self.get(key)
        if v is None:
            return default
        try:
            return int(str(v))
        except Exception:
            return default

    def get_float(self, key: str, default: float) -> float:
        v = self.get(key)
        if v is None:
            return default
        try:
            return float(str(v))
        except Exception:
            return default

    def get_bool(self, key: str, default: bool) -> bool:
        v = self.get(key)
        if v is None:
            return default
        return str(v).lower() == "true"

    def get_list(self, key: str, sep: str = ",", default: Optional[List[str]] = None) -> List[str]:
        v = self.get(key)
        if v is None:
            return default or []
        return [s.strip() for s in str(v).split(sep) if s.strip()]

    def get_json(self, key: str, default: Any = None) -> Any:
        v = self.get(key)
        if v is None:
            return default
        try:
            return json.loads(str(v))
        except Exception:
            return default


# 单例实例与便捷函数（供各模块直接使用）
_ENV = EnvConfig()


def reload() -> None:
    _ENV.reload()


def all() -> Dict[str, str]:
    return _ENV.all()


def get(key: str, default: Optional[str] = None) -> Optional[str]:
    return _ENV.get(key, default)


def get_str(key: str, default: str) -> str:
    return _ENV.get_str(key, default)


def get_int(key: str, default: int) -> int:
    return _ENV.get_int(key, default)


def get_float(key: str, default: float) -> float:
    return _ENV.get_float(key, default)


def get_bool(key: str, default: bool) -> bool:
    return _ENV.get_bool(key, default)


def get_list(key: str, sep: str = ",", default: Optional[List[str]] = None) -> List[str]:
    return _ENV.get_list(key, sep, default)


def get_json(key: str, default: Any = None) -> Any:
    return _ENV.get_json(key, default)