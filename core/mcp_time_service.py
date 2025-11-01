"""MCP时间服务模块

封装了通过LLM工具调用来获取当前时间的所有逻辑。
"""

import openai
import os
from dotenv import load_dotenv
from datetime import datetime
from loguru import logger
from typing import Union, Optional


class MCPTimeService:
    """MCP时间服务，通过LLM工具调用获取时间信息。"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        """初始化MCP时间服务。
        
        Args:
            api_key: API密钥，如果为None则从环境变量获取
            base_url: API基础URL，如果为None则从环境变量获取
            model: 模型名称，如果为None则从环境变量获取
        """
        # 加载环境变量
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
        
        # 检查是否启用MCP时间服务
        self.mcp_enabled = os.getenv("ENABLE_MCP_TIME_SERVICE", "false").lower() == "true"
        
        # 获取配置
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url or os.getenv("DASHSCOPE_BASE_URL")
        self.model = model or os.getenv("QWEN_MODEL")
        
        logger.info("MCPTimeService初始化开始")
        
        # 如果MCP服务被禁用，直接设置client为None
        if not self.mcp_enabled:
            logger.info("MCP时间服务已禁用 - 将直接使用本地时间")
            self.client = None
        # 验证配置
        elif not all([self.api_key, self.base_url, self.model]):
            logger.warning("MCP配置不完整 - 将使用本地时间")
            self.client = None
        else:
            try:
                self.client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
                logger.success("MCPTimeService初始化完成")
            except Exception as e:
                logger.error(f"OpenAI客户端初始化失败: {e}")
                self.client = None
    
    def _get_current_time(self) -> str:
        """[内部工具] 获取当前格式化的日期和时间。
        
        Returns:
            格式化的当前时间字符串
        """
        logger.debug("本地时间获取开始")
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def get_time_via_llm_tool(self) -> Optional[str]:
        """通过LLM工具调用获取关于当前时间的自然语言回答。
        
        Returns:
            成功时返回LLM生成的时间字符串，失败时返回None
        """
        if not self.client:
            logger.error("LLM客户端未初始化 - 无法执行调用")
            return None

        try:
            logger.debug("LLM时间获取开始")
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
                "_get_current_time": self._get_current_time,
            }
            messages = [{"role": "user", "content": user_prompt}]

            # === 步骤 1: 请求LLM进行决策 ===
            logger.debug("LLM决策开始")
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, tools=tools, tool_choice="auto"
            )
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # === 步骤 2: 执行工具并请求LLM总结 ===
            if tool_calls:
                logger.debug("LLM工具执行开始")
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
                from core.llm_provider import LLMProvider
                messages.append(
                    {
                        "role": "system",
                        "content": LLMProvider.build_time_service_system_message(),
                    }
                )

                logger.debug("LLM最终回答生成开始")
                second_response = self.client.chat.completions.create(
                    model=self.model, messages=messages
                )
                # 模型现在应该会返回一个干净的时间字符串
                return second_response.choices[0].message.content.strip()
            else:
                return response_message.content

        except Exception as e:
            logger.error(f"LLM时间获取失败: {e}")
            return None
    
    def get_current_time(self) -> str:
        """获取当前时间，根据配置决定是否使用LLM工具调用。
        
        Returns:
            当前时间字符串
        """
        # 如果MCP服务被禁用，直接返回本地时间
        if not self.mcp_enabled:
            local_time = self._get_current_time()
            logger.debug(f"MCP服务已禁用，使用本地时间: {local_time}")
            return local_time
        
        # 尝试通过LLM获取时间
        llm_time = self.get_time_via_llm_tool()
        
        if llm_time and not "失败" in llm_time:
            logger.debug(f"LLM时间获取成功: {llm_time}")
            return llm_time
        else:
            # 使用本地时间作为备用方案
            local_time = self._get_current_time()
            logger.debug(f"使用本地时间备用: {local_time}")
            return local_time


# 全局时间服务实例
_time_service = None


def get_time_service() -> MCPTimeService:
    """获取全局时间服务实例。
    
    Returns:
        MCPTimeService实例
    """
    global _time_service
    if _time_service is None:
        _time_service = MCPTimeService()
    return _time_service


def get_current_time() -> str:
    """获取当前时间的便捷函数。
    
    Returns:
        当前时间字符串
    """
    return get_time_service().get_current_time()


def main():
    """独立测试函数。"""
    logger.info("MCPTimeService测试开始")
    
    # 创建时间服务实例
    time_service = MCPTimeService()
    
    logger.info("开始LLM时间获取测试")
    llm_response = time_service.get_time_via_llm_tool()
    
    if llm_response:
        logger.success(f"LLM时间获取测试完成: {llm_response}")
    else:
        logger.error("LLM时间获取测试失败")
    
    logger.info("开始统一时间接口测试")
    current_time = time_service.get_current_time()
    logger.success(f"统一时间接口测试完成: {current_time}")
    
    logger.info("开始便捷函数测试")
    convenient_time = get_current_time()
    logger.success(f"便捷函数测试完成: {convenient_time}")
    
    logger.success("MCPTimeService测试完成")


if __name__ == "__main__":
    main()