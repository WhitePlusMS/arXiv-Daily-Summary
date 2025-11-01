import time
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