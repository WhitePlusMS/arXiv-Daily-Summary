"""LLM token 用量统计工具。"""

from threading import Lock
from typing import Dict

from core.env_config import get_float


class UsageTracker:
    """线程安全的 token 用量统计器。"""

    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self._lock = Lock()

    def add_usage(self, input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0):
        with self._lock:
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.total_tokens += total_tokens

    def snapshot(self) -> Dict[str, int]:
        with self._lock:
            return {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "total_tokens": self.total_tokens,
            }

    def compute_cost_yuan(self, input_price_per_1k: float = None, output_price_per_1k: float = None) -> Dict[str, float]:
        default_in = get_float("PRICE_INPUT_PER_1K", 0.008)
        default_out = get_float("PRICE_OUTPUT_PER_1K", 0.02)
        input_price = input_price_per_1k if input_price_per_1k is not None else default_in
        output_price = output_price_per_1k if output_price_per_1k is not None else default_out
        stats = self.snapshot()
        input_cost = (stats["input_tokens"] / 1000.0) * input_price
        output_cost = (stats["output_tokens"] / 1000.0) * output_price
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
        }
