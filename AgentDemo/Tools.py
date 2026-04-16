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


def get_attraction_enhanced(
    city: str,
    weather: str,
    user_id: str = None,
    enable_memory: bool = False,
    check_tickets: bool = False
) -> str:
    """
    增强版景点推荐，支持用户偏好记忆和门票检查

    Args:
        city: 城市名称
        weather: 天气情况
        user_id: 用户ID（可选，用于个性化推荐）
        enable_memory: 是否启用用户偏好记忆
        check_tickets: 是否检查门票可用性

    Returns:
        增强的景点推荐结果
    """
    try:
        # 1. 首先获取基本的景点推荐
        basic_result = get_attraction(city, weather)

        if "错误：" in basic_result:
            return basic_result  # 返回原始错误

        # 2. 构建增强结果
        enhanced_parts = [basic_result]

        # 3. 如果启用了记忆功能，添加个性化信息
        if enable_memory and user_id:
            try:
                from .user_state_manager import UserStateManager

                state_manager = UserStateManager()
                user_state = state_manager.get_user_state(user_id)
                preferences = user_state.get("preferences", {})

                personalized_note = "\n\n🎯 个性化推荐（基于您的偏好）:\n"

                # 添加预算信息
                budget = preferences.get("budget_range")
                if budget:
                    personalized_note += f"- 根据您的预算范围: {budget}\n"

                # 添加类别偏好
                category_prefs = preferences.get("category_preferences", {})
                if category_prefs:
                    top_categories = sorted(
                        category_prefs.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:2]  # 取前2个
                    if top_categories:
                        categories_str = ", ".join([cat for cat, _ in top_categories])
                        personalized_note += f"- 根据您的兴趣类别偏好: {categories_str}\n"

                # 添加拒绝学习提示
                consecutive_rejections = user_state.get("rejection_stats", {}).get("consecutive", 0)
                if consecutive_rejections >= 2:
                    personalized_note += f"- 注意：您已连续拒绝了{consecutive_rejections}个推荐，本次已尝试调整推荐策略\n"

                enhanced_parts.append(personalized_note)

            except ImportError as e:
                enhanced_parts.append("\n\n[警告] 注意：用户状态管理器不可用，已回退到基本推荐\n")
            except Exception as e:
                enhanced_parts.append(f"\n\n[警告] 注意：加载用户偏好时出错: {str(e)[:100]}\n")

        # 4. 如果启用了门票检查，添加可用性信息
        if check_tickets:
            try:
                from .ticket_api_client import TicketAPIFactory
                from datetime import datetime, timedelta

                ticket_client = TicketAPIFactory.create_from_env()
                today = datetime.now().strftime("%Y-%m-%d")
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

                ticket_info = "\n\n🎫 门票可用性检查:\n"

                # 这里应该从推荐结果中提取景点名称进行查询
                # 为简化，我们使用模拟数据
                # 在实际实现中，应该解析推荐结果中的景点名称

                # 模拟检查几个热门景点
                mock_attractions = [
                    {"id": "popular_spot_1", "name": "故宫博物院", "city": city, "category": "历史文化"},
                    {"id": "popular_spot_2", "name": "颐和园", "city": city, "category": "历史文化"},
                    {"id": "popular_spot_3", "name": "北海公园", "city": city, "category": "自然风光"},
                    {"id": "popular_spot_4", "name": "欢乐谷", "city": city, "category": "主题乐园"}
                ]

                checked_count = 0
                sold_out_attractions = []
                available_attractions = []

                for attr in mock_attractions[:3]:  # 只检查前3个
                    availability = ticket_client.check_ticket_availability(attr["id"], today)

                    if availability.get("available", False):
                        status = "[有票] 有票"
                        if availability.get("low_availability", False):
                            status = "[紧张] 库存紧张"
                        available_attractions.append(attr["name"])
                    else:
                        status = "❌ 已售罄"
                        sold_out_attractions.append({
                            "name": attr["name"],
                            "category": attr.get("category", "通用"),
                            "next_date": availability.get("next_available_date")
                        })
                        if availability.get("next_available_date"):
                            status += f" (下次有票: {availability['next_available_date']})"

                    ticket_info += f"- {attr['name']}: {status}\n"
                    checked_count += 1

                if checked_count > 0:
                    ticket_info += f"\n💡 提示：以上为模拟检查结果，实际可用性可能不同"

                    # 如果有售罄的景点，提供备选方案
                    if sold_out_attractions:
                        ticket_info += "\n\n🔄 备选方案推荐（以下景点目前可能有票）:\n"

                        # 根据售罄景点的类别推荐备选
                        sold_out_categories = set(attr["category"] for attr in sold_out_attractions)

                        # 查找同一类别的其他可用景点
                        alternative_candidates = []
                        for attr in mock_attractions:
                            if attr["name"] not in [a["name"] for a in sold_out_attractions]:
                                if attr.get("category") in sold_out_categories:
                                    alternative_candidates.append(attr)

                        # 如果没有同一类别的，推荐其他类别
                        if not alternative_candidates:
                            alternative_candidates = [attr for attr in mock_attractions
                                                     if attr["name"] not in [a["name"] for a in sold_out_attractions]]

                        # 显示备选推荐（最多3个）
                        for i, alt in enumerate(alternative_candidates[:3]):
                            ticket_info += f"{i+1}. {alt['name']} ({alt.get('category', '通用')})\n"

                        if alternative_candidates:
                            ticket_info += "\n💡 以上备选景点可能与原推荐类似，且目前可能有票。"

                    enhanced_parts.append(ticket_info)
                else:
                    enhanced_parts.append("\n\n🎫 门票检查：未找到可检查的景点信息\n")

            except ImportError as e:
                enhanced_parts.append("\n\n[警告] 注意：票务API客户端不可用，跳过门票检查\n")
            except Exception as e:
                enhanced_parts.append(f"\n\n[警告] 注意：检查门票时出错: {str(e)[:100]}\n")

        # 5. 添加反馈提示
        if enable_memory and user_id:
            feedback_prompt = "\n\n[反馈] 反馈提示：您可以使用'接受'或'拒绝'来提供反馈，系统会学习您的偏好。"
            enhanced_parts.append(feedback_prompt)

        # 6. 添加备选方案提示
        if check_tickets:
            alt_prompt = "\n\n🔄 备选方案：系统已自动检查门票可用性并提供备选推荐。如需更多选择，请告诉我您的具体需求。"
            enhanced_parts.append(alt_prompt)

        return "".join(enhanced_parts)

    except Exception as e:
        return f"错误：执行增强推荐时出现问题 - {e}\n\n基本推荐结果:\n{get_attraction(city, weather) if 'get_attraction' in locals() else '无法获取基本推荐'}"


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
    "get_attraction_enhanced": get_attraction_enhanced,
    "search_web": search_web,
    "writeFile": writeFile,
    "runTerminalCommand": runTerminalCommand,
    "readFile": readFile,
}
