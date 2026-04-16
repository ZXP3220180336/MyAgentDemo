import os
import re
from typing import Callable
from .LLMClient import OpenAICompatibleClient


class Agent:
    """
    一个简单的智能体类，能够与兼容OpenAI接口的LLM服务交互。
    """

    def __init__(
        self, available_tools: dict[str, Callable], llmClient: OpenAICompatibleClient
    ):
        self.available_tools = available_tools
        self.llm = llmClient
        self.prompt_history = []

    def display_conversation(self, history):
        """美观地显示对话历史"""
        print("\n" + "=" * 60)
        print("对话历史")
        print("=" * 60)

        for i, message in enumerate(history, 1):
            if message.startswith("用户请求:"):
                print(f"\n用户 [{i}]: {message[5:]}")
            elif message.startswith("Thought:"):
                print(f"\n思考 [{i}]: {message[8:].strip()}")
            elif message.startswith("Action:"):
                print(f"行动 [{i}]: {message[7:].strip()}")
            elif message.startswith("Observation:"):
                print(f"观察 [{i}]: {message[12:].strip()}")
            else:
                print(f"消息 [{i}]: {message}")

        print("=" * 60 + "\n")

    def format_code(self, content: str, file_path: str) -> str:
        """
        根据文件后缀自动格式化 HTML / CSS / JS 代码
        :param content: 原始代码字符串
        :param file_path: 文件路径（用于判断类型）
        :return: 格式化后的漂亮代码
        """
        try:
            ext = os.path.splitext(file_path)[1].lower()

            # ------------ HTML 格式化 ------------
            if ext == ".html":
                lines = (
                    content.replace(">", ">\\n")
                    .replace("<", "\\n<")
                    .replace('\\"', '"')
                    .split("\\n")
                )
                indent = 0
                result = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("</"):
                        indent -= 1
                    result.append("  " * indent + line)
                    if (
                        line.startswith("<")
                        and not line.startswith("</")
                        and not line.endswith("/>")
                    ):
                        indent += 1
                return "\n".join(result)

            # ------------ CSS 格式化 ------------

            elif ext == ".css":
                content = (
                    content.replace("{", "{\\n")
                    .replace("}", "}\\n")
                    .replace(";", ";\\n")
                )
                lines = content.split("\\n")
                indent = 0
                result = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if "}" in line:
                        indent -= 1
                    result.append("  " * indent + line)
                    if "{" in line and not "}" in line:
                        indent += 1
                return "\n".join(result)

            # ------------ JS 格式化 ------------
            elif ext == ".js":
                # 基础格式化：大括号、分号换行 + 缩进
                content = (
                    content.replace("{", "{\\n")
                    .replace("}", "}\\n")
                    .replace(";", ";\\n")
                )
                lines = content.split("\\n")
                indent = 0
                result = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # 减少缩进
                    if "}" in line or ")" in line and line.endswith(")"):
                        indent = max(indent - 1, 0)
                    result.append("  " * indent + line)
                    # 增加缩进
                    if "{" in line and not "}" in line:
                        indent += 1
                return "\n".join(result)

            # 其他类型直接返回
            else:
                return content
        except:  # noqa: E722
            return content  # 出错则不格式化，保证不崩溃

    def parse_action(self, action_str: str):
        """解析行动字符串，返回工具名和参数字典"""
        if action_str.startswith("Finish"):
            match = re.match(r"\w+\[(.*)\]", action_str)
            if match:
                return "finish", {"answer": match.group(1)}
            return "finish", {"answer": "任务完成"}

        tool_name_match = re.search(r"(\w+)\(", action_str)
        if not tool_name_match:
            return None, {}
        tool_name = tool_name_match.group(1)

        args_match = re.search(r"\((.*)\)", action_str, re.DOTALL)
        if args_match:
            args_str = args_match.group(1).strip()
            kwargs = dict(re.findall(r'(\w+)="([\s\S]*?)"(?=,|$)', args_str))
        else:
            kwargs = {}

        if tool_name == "writeFile" and "file_path" in kwargs and "content" in kwargs:
            kwargs["content"] = self.format_code(kwargs["content"], kwargs["file_path"])

        return tool_name, kwargs

    def run_assistant(self, user_input: str, system_prompt: str, max_iterations=5):

        print(f"👤 用户输入: {user_input}")
        self.prompt_history.append(f"用户请求: {user_input}")

        """运行智能体的主循环"""
        while True:
            # print(f"\n循环 {i + 1}/{max_iterations}")

            # 构建完整的Prompt
            full_prompt = "\n".join(self.prompt_history)

            # 调用LLM进行思考
            llm_output = self.llm.generate(full_prompt, system_prompt)
            # 模型可能会输出多余的Thought-Action，需要截断
            match = re.search(
                r"(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)",
                llm_output,
                re.DOTALL,
            )
            if match:
                truncated = match.group(1).strip()
                if truncated != llm_output.strip():
                    llm_output = truncated
                    print("已截断多余的 Thought-Action 对")

            print(f"模型输出:\n{llm_output}")
            self.prompt_history.append(llm_output)

            # 解析并执行行动
            action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
            if not action_match:
                observation = "错误: 未能解析到 Action 字段。请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"
                print(f"观察结果: {observation}\n" + "=" * 40)
                self.prompt_history.append(f"Observation: {observation}")
                continue
            action_str = action_match.group(1).strip()

            tool_name, kwargs = self.parse_action(action_str)
            # 处理完成行动
            if tool_name == "finish":
                final_answer = kwargs.get("answer", "任务完成")
                # final_answer = kwargs
                print("任务完成!")
                print(f"最终答案: {final_answer}")
                return
            # 处理工具调用
            if tool_name in self.available_tools:
                print(f"调用工具: {tool_name}({kwargs})")

                should_continue = (
                    input("是否继续执行工具调用？(y/n): ").strip().lower()
                    if tool_name == "runTerminalCommand"
                    else "y"
                )
                if should_continue != "y":
                    print(f"调用工具: {tool_name}({kwargs} 已被用户取消。)")
                    return
                else:
                    observation = self.available_tools[tool_name](**kwargs)
            else:
                observation = f"错误：未定义的工具 '{tool_name}'"

            # 记录观察结果
            print(f"观察结果: {observation}")
            print("=" * 50)
            self.prompt_history.append(f"Observation: {observation}")

        # 如果达到最大循环次数仍未完成
        # print(
        #    "⏰ 达到最大循环次数: 抱歉，经过多次尝试仍未完成您的请求。请尝试简化您的问题或稍后重试。"
        # )
