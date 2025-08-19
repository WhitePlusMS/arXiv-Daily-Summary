# ==============================================================================
# 文件名: time_updater_mcp.py
# 描述: 封装了通过LLM工具调用来获取当前时间的所有逻辑。
# ==============================================================================

import openai
import os
from dotenv import load_dotenv
from datetime import datetime
import logging
from typing import Union

# 配置日志，用于记录内部信息
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 模块初始化 ---
# 加载 .env 文件中的环境变量 (DASHSCOPE_API_KEY, etc.)
load_dotenv()
try:
    client = openai.OpenAI(
        api_key=os.getenv("QWEN_API_KEY"),
        base_url=os.getenv("QWEN_BASE_URL"),
    )
    QWEN_MODEL = os.getenv("QWEN_MODEL")
    if not all([os.getenv("QWEN_API_KEY"), os.getenv("QWEN_BASE_URL"), QWEN_MODEL]):
        raise ValueError("请确保 .env 文件中已设置 QWEN_API_KEY, QWEN_BASE_URL 和 QWEN_MODEL")
except Exception as e:
    logging.error(f"初始化OpenAI客户端失败: {e}")
    client = None # 将client设为None，以便后续函数可以检查

# --- 内部工具函数定义 ---
def _get_current_time() -> str:
    """[内部工具] 获取当前格式化的日期和时间。"""
    logging.info("执行本地工具: _get_current_time")
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# --- 对外暴露的主函数 ---
def get_time_via_llm_tool() -> Union[str, None]:
    """
    通过LLM工具调用获取关于当前时间的自然语言回答。
    这是一个完全封装的函数，处理所有与LLM的交互。

    :return: 成功时返回LLM生成的字符串，失败时返回 None。
    """
    if not client:
        logging.error("客户端未成功初始化，无法执行LLM调用。")
        return None

    try:
        user_prompt = "请问现在几点了？"
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "_get_current_time",
                    "description": "当用户询问当前日期或时间时使用此工具",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
        available_tools = {
            "_get_current_time": _get_current_time,
        }
        messages = [{"role": "user", "content": user_prompt}]

        # === 步骤 1: 请求LLM进行决策 ===
        logging.info("步骤1: 请求LLM决策...")
        response = client.chat.completions.create(
            model=QWEN_MODEL, messages=messages, tools=tools, tool_choice="auto"
        )
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # === 步骤 2: 执行工具并请求LLM总结 ===
        if tool_calls:
            logging.info("LLM决定调用工具。")
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                tool_function = available_tools.get(function_name)
                if tool_function:
                    function_response = tool_function()
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
            messages.append(
                {
                    "role": "system",
                    "content": "你是一个只会返回标准时间格式的机器人。请根据工具返回的结果，直接输出格式为 YYYY-MM-DD HH:MM:SS 的时间字符串，不要包含任何其他文字、标点或解释。",
                }
            )

            logging.info("步骤2: 请求LLM生成最终回答...")
            second_response = client.chat.completions.create(
                model=QWEN_MODEL, messages=messages
            )
            # 模型现在应该会返回一个干净的时间字符串
            return second_response.choices[0].message.content.strip()
        else:
            return response_message.content

    except Exception as e:
        logging.error(f"在与LLM交互过程中发生错误: {e}")
        return None

if __name__ == "__main__":
    print("--- 开始执行主逻辑 ---")
    print("正在尝试通过LLM工具调用获取时间...")
    llm_response = get_time_via_llm_tool()
    if llm_response:
        print(f"✅ LLM调用成功！模型回答: '{llm_response}'")
    else:
        # 失败，使用本地时间作为备用方案
        print("❌ LLM工具调用失败，将使用本地时间。")
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"🕒 本地备用时间: {current_time}")

    print("--- 主逻辑执行完毕 ---")