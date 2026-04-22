import os
import requests
from tavily import TavilyClient


def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    """
    # API端点，我们请求JSON格式的数据
    url = f"https://wttr.in/{city}?format=j1"

    try:
        # 发起网络请求
        response = requests.get(url)
        # 检查响应状态码是否为200 (成功)
        response.raise_for_status()
        # 解析返回的JSON数据
        data = response.json()
        # print(f"✅ 成功获取天气数据: {data}")

        # 提取当前天气状况
        current_condition = data["current_condition"][0]
        weather_desc = current_condition["weatherDesc"][0]["value"]
        temp_c = current_condition["temp_C"]

        # 格式化成自然语言返回
        return f"{city}当前天气：{weather_desc}，气温{temp_c}摄氏度"

    except requests.exceptions.RequestException as e:
        # 处理网络错误
        return f"错误：查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        # 处理数据解析错误
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"


def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
    """
    api_key = os.environ.get("TAVILY_API_KEY")

    if not api_key:
        return "错误：未配置TAVILY_API_KEY。"

    # 初始化Tavily客户端
    tavily = TavilyClient(api_key=api_key)

    # 构造一个精确的查询
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        # 调用API，include_answer=True会返回一个综合性的回答
        response = tavily.search(query=query, search_depth="basic", include_answer=True)
        # Tavily返回的结果已经非常干净，可以直接使用
        if response.get("answer"):
            return response["answer"]

        # 如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"

        return "根据搜索，为您找到以下信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：执行Tavily搜索时出现问题 - {e}"


def search_web(query: str) -> str:
    """
    使用Tavily Search API执行网络搜索并返回结果。
    """
    api_key = os.environ.get("TAVILY_API_KEY")

    if not api_key:
        return "错误：未配置TAVILY_API_KEY。"

    tavily = TavilyClient(api_key=api_key)

    try:
        response = tavily.search(query=query, search_depth="basic", include_answer=True)
        if response.get("answer"):
            return response["answer"]

        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关信息。"

        return "根据搜索，为您找到以下信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：执行Tavily搜索时出现问题 - {e}"


def readFile(file_path: str) -> str:
    """
    读取指定路径的文本文件内容并返回。
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            return content
    except FileNotFoundError:
        return f"错误：文件 '{file_path}' 未找到。"
    except Exception as e:
        return f"错误：读取文件时发生问题 - {e}"


def writeFile(file_path: str, content: str) -> str:
    """
    将指定内容写入文本文件，如果文件不存在则创建。
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
            return f"成功将内容写入 '{file_path}'。"
    except Exception as e:
        return f"错误：写入文件时发生问题 - {e}"


def runTerminalCommand(command: str) -> str:
    """
    执行指定的终端命令并返回输出结果。
    """
    import subprocess

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return f"执行成功 - {result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        return f"错误：执行命令时发生问题 - {e.stderr.strip()}"


# 将所有工具函数放入一个字典，方便后续调用
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
    "search_web": search_web,
    "writeFile": writeFile,
    "runTerminalCommand": runTerminalCommand,
    "readFile": readFile,
}
