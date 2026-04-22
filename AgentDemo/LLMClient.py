from abc import ABC, abstractmethod
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from anthropic import Anthropic
from anthropic.types import MessageParam


class LLMClient(ABC):
    """LLM客户端抽象基类"""

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    def generate(self, user_prompt: str, system_prompt: str) -> str:
        """
        调用LLM API生成回应

        Args:
            user_prompt: 用户输入的提示词
            system_prompt: 系统提示词

        Returns:
            LLM生成的回应文本
        """
        pass


class OpenAICompatibleClient(LLMClient):
    """
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端。
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        super().__init__(model, api_key, base_url)
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, user_prompt: str, system_prompt: str) -> str:
        """调用LLM API来生成回应。"""
        print("正在调用大语言模型...")
        try:
            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, stream=False
            )
            answer = (
                response.choices[0].message.content
                if response.choices[0].message.content
                else "抱歉，未能生成有效回答。"
            )
            print("大语言模型响应成功。")
            return answer
        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误：调用语言模型服务时出错。"


class AnthropicAICompatibleClient(LLMClient):
    """
    兼容Anthropic Claude API的LLM客户端
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        super().__init__(model, api_key, base_url)
        self.client = Anthropic(api_key=api_key, base_url=base_url)

    def generate(self, user_prompt: str, system_prompt: str) -> str:
        """调用LLM API来生成回应。"""
        print("正在调用大语言模型...")
        try:
            messages: list[MessageParam] = [{"role": "user", "content": user_prompt}]
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,  # Claude 必须写 max_tokens
                messages=messages,
                system=system_prompt,
                stream=False,
            )
            answer = ""
            for content in response.content:
                if content.type == "text":
                    answer = (
                        content.text if content.text else "抱歉，未能生成有效回答。"
                    )
                    break

            print("大语言模型响应成功。")
            return answer
        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误：调用语言模型服务时出错。"


class LLMClientFactory:
    """LLM客户端工厂类，用于创建合适的客户端"""

    @staticmethod
    def create_client(api_type: str = "openai", **kwargs) -> LLMClient:
        """
        创建LLM客户端

        Args:
            api_type: API类型 ("openai", "anthropic")
            **kwargs: 客户端参数
                - model: 模型名称
                - api_key: API密钥
                - base_url: API基础URL

        Returns:
            LLM客户端实例
        """
        model = kwargs.get("model", "")
        api_key = kwargs.get("api_key", "")
        base_url = kwargs.get("base_url", "")

        if api_type == "anthropic":
            return AnthropicAICompatibleClient(
                model=model or "claude-3-haiku-20240307",
                api_key=api_key or "demo_anthropic_key",
                base_url=base_url or "https://api.anthropic.com",
            )
        else:
            # 默认返回OpenAI兼容客户端
            return OpenAICompatibleClient(
                model=model or "gpt-3.5-turbo",
                api_key=api_key or "demo_openai_key",
                base_url=base_url or "https://api.openai.com/v1",
            )

    @staticmethod
    def create_from_env() -> LLMClient:
        """从环境变量创建客户端"""
        import os

        # 读取配置
        llm_api_type = os.getenv("LLM_API_TYPE", "openai")
        llm_model = os.getenv("LLM_MODEL", "")
        llm_api_key = os.getenv("LLM_API_KEY", "")
        llm_base_url = os.getenv("LLM_BASE_URL", "")

        return LLMClientFactory.create_client(
            api_type=llm_api_type,
            model=llm_model,
            api_key=llm_api_key,
            base_url=llm_base_url,
        )


# 测试代码
if __name__ == "__main__":
    print("测试LLM客户端工厂...")

    # 测试OpenAI客户端
    print("\n1. 测试OpenAI客户端:")
    openai_client = LLMClientFactory.create_client("openai")
    print(f"创建的客户端类型: {type(openai_client).__name__}")

    # 测试Anthropic客户端
    print("\n2. 测试Anthropic客户端:")
    anthropic_client = LLMClientFactory.create_client("anthropic")
    print(f"创建的客户端类型: {type(anthropic_client).__name__}")

    # 测试带参数的客户端创建
    print("\n3. 测试带自定义参数的客户端:")
    custom_client = LLMClientFactory.create_client(
        api_type="openai",
        model="gpt-4",
        api_key="custom_key",
        base_url="https://custom.openai.com",
    )
    print(f"自定义客户端模型: {custom_client.model}")

    # 测试从环境变量创建客户端
    print("\n4. 测试从环境变量创建客户端:")
    try:
        # 加载环境变量文件（实际应用中应在主程序入口加载）
        from dotenv import load_dotenv

        load_dotenv()

        import os

        print(f"环境变量LLM_API_TYPE: {os.getenv('LLM_API_TYPE')}")
        print(f"环境变量LLM_MODEL: {os.getenv('LLM_MODEL')}")

        # 测试读取现有环境变量
        env_client = LLMClientFactory.create_from_env()
        print(f"从环境变量创建的客户端类型: {type(env_client).__name__}")
        print(f"客户端模型: {env_client.model}")
        print(
            f"客户端API类型: {'openai' if isinstance(env_client, OpenAICompatibleClient) else 'anthropic'}"
        )

    except Exception as e:
        print(f"环境变量创建客户端失败: {e}")

    print("\nLLM客户端工厂测试完成")
