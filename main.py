from dotenv import load_dotenv
from AgentDemo import Agent, LLMClientFactory, available_tools, AGENT_SYSTEM_PROMPT

load_dotenv()


def main():
    """主函数"""
    print("=" * 60)
    print("MyAgentDemo 智能旅游助手")
    print("=" * 60)

    try:
        llm_client = LLMClientFactory.create_from_env()
        print(f"LLM 客户端已初始化: {type(llm_client).__name__}")
    except Exception as e:
        print(f"错误: 初始化 LLM 客户端失败 - {e}")
        return

    agent = Agent(available_tools=available_tools, llmClient=llm_client)

    print("\n提示: 您可以输入任何旅游相关查询，例如:")
    print("- '帮我查询北京的天气'")
    print("- '推荐上海的历史文化景点'")
    print("- '杭州有什么适合家庭游玩的地方？'")
    print("（输入 '退出' 或 'exit' 结束程序）")
    print("-" * 40)

    while True:
        user_input = input("\n请输入查询内容: ").strip()

        if user_input.lower() in ["退出", "exit", "quit"]:
            print("感谢使用，再见！")
            break

        if not user_input:
            print("查询内容不能为空")
            continue

        try:
            agent.run_assistant(
                user_input=user_input,
                system_prompt=AGENT_SYSTEM_PROMPT,
                max_iterations=5,
            )
        except Exception as e:
            print(f"错误: 执行查询时出错 - {e}")


if __name__ == "__main__":
    main()
