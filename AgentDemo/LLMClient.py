from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from anthropic import Anthropic
from anthropic.types import MessageParam

class OpenAICompatibleClient:
    """
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端。
    """
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, user_prompt: str, system_prompt: str) -> str:
        """调用LLM API来生成回应。"""
        print("正在调用大语言模型...")
        try:
            messages : list[ChatCompletionMessageParam]= [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content if response.choices[0].message.content else "抱歉，未能生成有效回答。"
            print("大语言模型响应成功。")
            return answer
        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误：调用语言模型服务时出错。"

class AnthropicAICompatibleClient:
    """
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端。
    """
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = Anthropic(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用LLM API来生成回应。"""
        print("正在调用大语言模型...")
        try:
            messages : list[MessageParam]= [
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,        # Claude 必须写 max_tokens
                messages=messages,          
                system=system_prompt,
                stream=False
            )
            answer = ""
            for content in response.content:
                if content.type == "text":
                    answer = content.text if content.text else "抱歉，未能生成有效回答。"
                    break
                
            print("大语言模型响应成功。")
            return answer
        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误：调用语言模型服务时出错。"