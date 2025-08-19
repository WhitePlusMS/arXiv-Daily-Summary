"""
通用API提供商实现

为论文分析和总结提供OpenAI兼容API集成，支持通义千问、SiliconFlow等。
同时包含LLM提供商的抽象基类定义。
"""

import time
from openai import OpenAI


class OpenAIProvider:
    """用于LLM交互的通用API提供商，支持通义千问、SiliconFlow等OpenAI兼容API。"""
    
    def __init__(self, model: str, base_url: str, api_key: str):
        self._model_name = model
        self._client = OpenAI(base_url=base_url, api_key=api_key)
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name
    
    def _build_messages(self, prompt: str) -> list:
        """构建OpenAI API的消息结构。"""
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    
    def _call_api_with_retry(
        self, messages: list, temperature: float, max_retries: int = 10, wait_time: int = 1
    ) -> str:
        """使用重试机制调用OpenAI API。"""
        for attempt in range(max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self._model_name,
                    messages=messages,
                    temperature=temperature
                )
                return response.choices[0].message.content
                
            except Exception as error:
                if attempt < max_retries - 1:
                    print(f"API call failed (attempt {attempt + 1}/{max_retries}): {error}")
                    time.sleep(wait_time)
                else:
                    print(f"API call failed after {max_retries} attempts")
                    raise
    
    def generate_response(self, prompt: str, temperature: float = 0.7) -> str:
        """使用OpenAI API生成响应。"""
        messages = self._build_messages(prompt)
        return self._call_api_with_retry(messages, temperature)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # 加载.env文件中的环境变量
    load_dotenv()

    # 从环境变量读取通义千问配置
    test_model = os.getenv("QWEN_MODEL")
    test_base_url = os.getenv("DASHSCOPE_BASE_URL")
    test_api_key = os.getenv("DASHSCOPE_API_KEY")

    # 检查环境变量是否都已设置
    if not all([test_model, test_base_url, test_api_key]):
        print("错误：请确保 .env 文件中已配置 QWEN_MODEL, DASHSCOPE_BASE_URL, 和 DASHSCOPE_API_KEY")
    else:
        print("正在使用以下配置进行测试：")
        print(f"  - 模型: {test_model}")
        print(f"  - API 地址: {test_base_url}")

        try:
            # 初始化提供商
            provider = OpenAIProvider(
                model=test_model,
                base_url=test_base_url,
                api_key=test_api_key
            )

            # 测试生成响应
            prompt = "你好，请介绍一下你自己。"
            print(f"\n发送提示: '{prompt}'")
            response = provider.generate_response(prompt)
            print(f"\n收到响应:\n{response}")

        except Exception as e:
            print(f"\n测试过程中发生错误: {e}")