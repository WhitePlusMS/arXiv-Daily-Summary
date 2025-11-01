import time
import re
import json
import os
from typing import Callable, Optional, Any
from loguru import logger

# 星级评分的统一阈值（与现有逻辑保持一致）
STAR_LOW_THRESHOLD = 2
STAR_HIGH_THRESHOLD = 8


def run_with_retries(
    call: Callable[[], Any],
    retries: int,
    delay: float,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Any:
    """通用重试封装，保持最小依赖与行为透明。

    Args:
        call: 无参可调用，封装一次实际操作（如HTTP请求）。
        retries: 最大重试次数。
        delay: 每次重试之间的等待秒数。
        on_retry: 当发生异常且将重试时的回调，入参为(当前第几次重试, 异常)。

    Returns:
        任意类型，来自 `call()` 的返回值。

    Raises:
        最后一次异常在耗尽重试后抛出，由调用方决定兜底行为。
    """
    last_exc: Optional[Exception] = None
    for attempt in range(retries):
        try:
            return call()
        except Exception as e:
            last_exc = e
            # 仅在还有剩余重试时执行回调与等待
            if attempt < retries - 1:
                if on_retry:
                    try:
                        on_retry(attempt + 1, e)
                    except Exception as cb_err:
                        logger.debug(f"重试回调执行失败: {cb_err}")
                time.sleep(delay)
            else:
                # 耗尽重试，向上传递异常
                raise last_exc


def sanitize_username(username: str) -> str:
    """将用户名转换为安全的文件名片段（跨模块统一）。

    此实现与现有各处逻辑保持完全一致，仅抽取为公共工具函数，
    不改变任何行为或性能。
    """
    if not username:
        return "USER"
    return re.sub(r'[\\/:*?"<>|\s]+', '_', username.strip())


def write_json(file_path: str, data: Any, ensure_ascii: bool = False, indent: int = 2) -> None:
    """以UTF-8编码写入JSON文件（参数默认与现有用法一致）。

    为减少重复而抽取的薄封装；调用方应显式传递与原来一致的参数，
    以确保行为与输出完全不变。
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)


def get_env_int(name: str, default: int) -> int:
    """读取整数环境变量，解析失败返回默认值。

    行为与现有 try/except 转 int 完全一致：不可解析或缺失时返回默认。
    """
    try:
        val = os.getenv(name, None)
        if val is None:
            return default
        return int(val)
    except Exception:
        return default

def get_env_bool(name: str, default: bool) -> bool:
    """以与现有代码一致的方式解析布尔环境变量。

    规则与当前实现保持一致：仅当值（不区分大小写）为 'true' 时返回 True；
    否则返回 False；若变量不存在则返回默认值。
    """
    val = os.getenv(name, None)
    if val is None:
        return default
    return val.lower() == 'true'


def backoff_sleep(attempt: int, base: float, factor: int = 2) -> None:
    """按既有公式 base * (factor ** attempt) 进行休眠。

    保持与现有代码中指数退避的时间序列完全一致。
    """
    time.sleep(base * (factor ** attempt))


def make_on_retry_logger(prefix: str, context: str, retries: int, delay: float) -> Callable[[int, Exception], None]:
    """生成一个与现有语义一致的 on_retry 回调函数。

    日志格式：
    - warning: "{prefix}失败 ({attempt}/{retries}) - {context}: {exc}"
    - debug:   "等待 {delay} 秒后重试"
    """
    def _on_retry(attempt_idx: int, exc: Exception):
        logger.warning(f"{prefix}失败 ({attempt_idx}/{retries}) - {context}: {exc}")
        logger.debug(f"等待 {delay} 秒后重试")
    return _on_retry