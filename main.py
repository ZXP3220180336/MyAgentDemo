import os
import sys
from dotenv import load_dotenv

# 导入增强功能模块
from AgentDemo import (
    OpenAICompatibleClient,
    available_tools,
    EnhancedAgent,
    AGENT_SYSTEM_PROMPT,
    AuthManager,
    UserStateManager,
    RejectionTracker,
    StrategyAdjuster,
    FeedbackManager,
    create_feedback_collector,
    TicketAPIFactory,
)

# 加载环境变量
load_dotenv()


class EnhancedConsoleApp:
    """增强版控制台应用程序"""

    def __init__(self):
        """初始化应用程序"""
        self.auth_manager = AuthManager()
        self.user_state_manager = None
        self.rejection_tracker = None
        self.strategy_adjuster = None
        self.feedback_manager = None
        self.ticket_client = None
        self.agent = None

        self.current_user = None
        self.current_session = None
        self.user_preferences = {}

        # 初始化组件
        self._init_components()

    def _init_components(self):
        """初始化各个组件"""
        print("正在初始化增强功能组件...")

        # 初始化票务客户端
        try:
            self.ticket_client = TicketAPIFactory.create_from_env()
            print(f"票务客户端已初始化: {type(self.ticket_client).__name__}")
        except Exception as e:
            print(f"警告: 初始化票务客户端失败 - {e}")
            # 使用模拟客户端作为回退
            self.ticket_client = TicketAPIFactory.create_client("mock")
            print("已回退到模拟票务客户端")

        # 初始化反馈管理器
        try:
            feedback_callback = self._on_feedback_received
            collector = create_feedback_collector(
                "console", on_feedback=feedback_callback
            )
            self.feedback_manager = FeedbackManager(collector)
            print("反馈管理器已初始化")
        except Exception as e:
            print(f"警告: 初始化反馈管理器失败 - {e}")

    def _on_feedback_received(self, feedback):
        """反馈回调函数"""
        print(f"[反馈记录] 收到反馈: {feedback}")

    def show_main_menu(self):
        """显示主菜单"""
        while True:
            print("\n" + "=" * 60)
            print("MyAgentDemo 智能旅游助手 - 增强版")
            print("=" * 60)

            if self.current_user:
                print(f"当前用户: {self.current_user}")
                print("1. 执行查询任务")
                print("2. 查看用户偏好")
                print("3. 查看拒绝分析报告")
                print("4. 查看用户洞察")
                print("5. 修改用户偏好")
                print("6. 登出")
                print("7. 退出程序")
            else:
                print("1. 用户登录")
                print("2. 用户注册")
                print("3. 退出程序")

            print("=" * 60)

            choice = input("请选择操作 (1-7): ").strip()

            if self.current_user:
                if choice == "1":
                    self.run_query()
                elif choice == "2":
                    self.show_user_preferences()
                elif choice == "3":
                    self.show_rejection_analysis()
                elif choice == "4":
                    self.show_user_insights()
                elif choice == "5":
                    self.update_user_preferences()
                elif choice == "6":
                    self.logout()
                elif choice == "7":
                    print("感谢使用，再见！")
                    sys.exit(0)
                else:
                    print("无效选择，请重试。")
            else:
                if choice == "1":
                    self.login()
                elif choice == "2":
                    self.register()
                elif choice == "3":
                    print("感谢使用，再见！")
                    sys.exit(0)
                else:
                    print("无效选择，请重试。")

    def login(self):
        """用户登录"""
        print("\n--- 用户登录 ---")
        username = input("用户名: ").strip()
        password = input("密码: ").strip()

        if not username or not password:
            print("错误: 用户名和密码不能为空")
            return

        session_token = self.auth_manager.login_user(username, password)

        if session_token:
            self.current_user = username
            self.current_session = session_token

            # 初始化用户状态管理器
            self.user_state_manager = UserStateManager()
            self.rejection_tracker = RejectionTracker(self.user_state_manager)
            self.strategy_adjuster = StrategyAdjuster(self.user_state_manager)

            # 加载用户偏好
            self._load_user_preferences()

            # 初始化智能体
            self._init_agent()

            print(f"登录成功！欢迎 {username}！")
            print("已启用个性化推荐、拒绝学习和策略调整功能。")
        else:
            print("错误: 用户名或密码错误")

    def register(self):
        """用户注册"""
        print("\n--- 用户注册 ---")
        username = input("用户名: ").strip()
        password = input("密码: ").strip()

        if not username or not password:
            print("错误: 用户名和密码不能为空")
            return

        if len(password) < 6:
            print("错误: 密码长度至少6位")
            return

        success = self.auth_manager.register_user(username, password)

        if success:
            print("注册成功！请登录。")
        else:
            print("错误: 用户名已存在")

    def logout(self):
        """用户登出"""
        if self.current_session:
            self.auth_manager.logout_user(self.current_session)

        self.current_user = None
        self.current_session = None
        self.user_state_manager = None
        self.rejection_tracker = None
        self.strategy_adjuster = None
        self.agent = None

        print("已成功登出。")

    def _load_user_preferences(self):
        """加载用户偏好"""
        if not self.current_user:
            return

        try:
            user_info = self.auth_manager.get_user_info(self.current_user)
            if user_info and "preferences" in user_info:
                self.user_preferences = user_info["preferences"]
                print(f"已加载用户偏好: {self.user_preferences}")
        except Exception as e:
            print(f"警告: 加载用户偏好时出错 - {e}")

    def _init_agent(self):
        """初始化增强智能体"""
        if not self.current_user:
            print("错误: 请先登录")
            return

        try:
            # 初始化LLM客户端
            llm_client = OpenAICompatibleClient(
                model=os.getenv("OPENAI_MODEL_ID") or "deepseek-chat",
                api_key=os.getenv("OPENAI_API_KEY") or "",
                base_url=os.getenv("OPENAI_BASE_URL") or "https://api.deepseek.com",
            )

            # 创建增强智能体
            self.agent = EnhancedAgent(
                available_tools=available_tools,
                llmClient=llm_client,
                user_id=self.current_user,
                enable_memory=True,
                enable_rejection_learning=True,
                enable_ticket_check=True,
            )

            # 注入票务客户端
            self.agent.ticket_client = self.ticket_client

            print("增强智能体已初始化，支持:")
            print("- 用户偏好记忆")
            print("- 拒绝学习与策略调整")
            print("- 门票可用性检查")
            print("- 个性化推荐")

        except Exception as e:
            print(f"错误: 初始化智能体失败 - {e}")
            # 增强版本要求智能体必须初始化成功
            self.agent = None

    def run_query(self):
        """执行查询任务"""
        if not self.agent:
            print("错误: 智能体未初始化")
            return

        print("\n--- 执行查询 ---")
        print("提示: 您可以输入任何旅游相关查询，例如:")
        print("- '帮我查询北京的天气'")
        print("- '推荐上海的历史文化景点'")
        print("- '杭州有什么适合家庭游玩的地方？'")
        print("- '帮我检查故宫博物院明天的门票'")
        print("（输入 '退出' 返回主菜单）")
        print("-" * 40)

        while True:
            query = input("\n请输入查询内容: ").strip()

            if query.lower() in ["退出", "exit", "quit"]:
                break

            if not query:
                print("查询内容不能为空")
                continue

            print(f"\n正在处理查询: {query}")
            print("-" * 60)

            try:
                # 执行智能体
                result = self.agent.run_assistant_enhanced(
                    user_input=query,
                    system_prompt=AGENT_SYSTEM_PROMPT,
                    max_iterations=5,
                    extract_preferences=True,
                )

                # 显示结果
                print("\n查询结果:")
                print("=" * 60)
                print(result)
                print("=" * 60)

                # 显示增强功能统计
                print("\n[增强功能统计]")
                self.agent._display_enhanced_stats()

                # 提示用户反馈
                self._prompt_feedback(query)

            except Exception as e:
                print(f"错误: 执行查询时出错 - {e}")

    def _prompt_feedback(self, query: str):
        """提示用户提供反馈"""
        print("\n--- 反馈收集 ---")
        print("您对刚才的推荐满意吗？")
        print("1. 接受推荐")
        print("2. 拒绝推荐")
        print("3. 跳过反馈")

        choice = input("请选择 (1-3): ").strip()

        if choice == "1":
            # 记录接受
            recommendation = {"query": query, "timestamp": "当前查询"}
            self.user_state_manager.record_feedback(
                self.current_user, "accept", recommendation, None
            )
            print("已记录接受反馈，感谢您的反馈！")

        elif choice == "2":
            # 显示拒绝原因
            print("\n请选择拒绝原因:")
            print("1. 价格太高")
            print("2. 距离太远")
            print("3. 已经去过")
            print("4. 不感兴趣")
            print("5. 其他原因")

            reason_choice = input("请选择原因 (1-5): ").strip()

            reason_map = {
                "1": "价格太高",
                "2": "距离太远",
                "3": "已经去过",
                "4": "不感兴趣",
                "5": "其他原因",
            }

            reason = reason_map.get(reason_choice, "其他原因")

            # 记录拒绝
            recommendation = {"query": query, "timestamp": "当前查询"}
            self.user_state_manager.record_feedback(
                self.current_user, "reject", recommendation, reason
            )

            print(f"已记录拒绝反馈，原因: {reason}")

            # 检查是否需要策略调整
            state = self.user_state_manager.get_user_state(self.current_user)
            consecutive_rejections = state.get("rejection_stats", {}).get(
                "consecutive", 0
            )

            if consecutive_rejections >= 3:
                print(
                    f"[系统提示] 检测到连续{consecutive_rejections}次拒绝，已自动调整推荐策略。"
                )

        else:
            print("已跳过反馈。")

    def show_user_preferences(self):
        """显示用户偏好"""
        if not self.current_user:
            print("错误: 请先登录")
            return

        if not self.user_state_manager:
            print("错误: 用户状态管理器未初始化")
            return

        state = self.user_state_manager.get_user_state(self.current_user)
        preferences = state.get("preferences", {})

        print("\n--- 用户偏好 ---")
        print(f"用户名: {self.current_user}")

        if not preferences:
            print("暂无用户偏好信息。")
            print(
                "提示: 在查询中使用类似'预算500元'、'喜欢历史文化'等表述，系统会自动学习您的偏好。"
            )
            return

        # 显示预算范围
        budget = preferences.get("budget_range")
        if budget:
            print(f"预算范围: {budget}")

        # 显示类别偏好
        category_prefs = preferences.get("category_preferences", {})
        if category_prefs:
            print("兴趣类别偏好:")
            for category, score in sorted(
                category_prefs.items(), key=lambda x: x[1], reverse=True
            ):
                strength = "强" if score > 0.7 else "中" if score > 0.4 else "弱"
                print(f"  - {category}: {strength} ({score:.2f})")

        # 显示其他偏好
        explicit_prefs = preferences.get("explicit_preferences", {})
        if explicit_prefs:
            print("其他偏好:")
            for pref_key, pref_value in explicit_prefs.items():
                if isinstance(pref_value, bool) and pref_value:
                    print(f"  - {pref_key}")
                elif pref_value:
                    print(f"  - {pref_key}: {pref_value}")

        # 显示最后提取时间
        last_extracted = preferences.get("last_extracted")
        if last_extracted:
            print(f"最后更新: {last_extracted}")

    def show_rejection_analysis(self):
        """显示拒绝分析报告"""
        if not self.current_user:
            print("错误: 请先登录")
            return

        if not self.rejection_tracker:
            print("错误: 拒绝跟踪器未初始化")
            return

        print("\n--- 拒绝分析报告 ---")

        # 获取分析结果
        analysis = self.rejection_tracker.analyze_rejection_patterns(self.current_user)

        total_rejections = analysis.get("total_rejections", 0)

        if total_rejections == 0:
            print("暂无拒绝记录，保持优秀！")
            return

        print(f"总拒绝次数: {total_rejections}")

        # 显示原因分布
        reasons_dist = analysis.get("reasons_distribution", {})
        if reasons_dist:
            print("\n拒绝原因分布:")
            for reason, count in sorted(
                reasons_dist.items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (count / total_rejections) * 100
                print(f"  - {reason}: {count}次 ({percentage:.1f}%)")

        # 显示主要拒绝原因
        if "primary_reason" in analysis:
            primary = analysis["primary_reason"]
            print(f"\n主要拒绝原因: {primary['reason']} ({primary['percentage']:.1f}%)")

        # 显示连续拒绝模式
        consecutive_patterns = analysis.get("consecutive_patterns", {})
        if consecutive_patterns:
            print("\n连续拒绝模式:")
            print(f"  最长连续拒绝: {consecutive_patterns.get('max_consecutive', 0)}次")
            print(
                f"  平均连续拒绝: {consecutive_patterns.get('avg_consecutive', 0):.1f}次"
            )

        # 显示策略建议
        recommendations = self.rejection_tracker.generate_strategy_recommendations(
            self.current_user
        )

        if recommendations:
            print("\n策略调整建议:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. [{rec['priority']}] {rec['description']}")

        # 显示调整效果
        effectiveness = self.rejection_tracker.get_adjustment_effectiveness(
            self.current_user
        )
        if effectiveness.get("has_adjustments"):
            print("\n策略调整效果:")
            print(f"  近期接受率: {effectiveness.get('recent_acceptance_rate', 0):.1%}")
            print(
                f"  历史接受率: {effectiveness.get('historical_acceptance_rate', 0):.1%}"
            )
            print(f"  改善情况: {effectiveness.get('improvement', 0):+.1%}")
            print(f"  效果评级: {effectiveness.get('effectiveness_rating', '待评估')}")

    def show_user_insights(self):
        """显示用户洞察"""
        if not self.current_user:
            print("错误: 请先登录")
            return

        if not self.user_state_manager:
            print("错误: 用户状态管理器未初始化")
            return

        insights = self.user_state_manager.get_user_insights(self.current_user)

        print("\n--- 用户洞察 ---")

        # 显示推荐成功率
        success_rate = insights.get("recommendation_success_rate", 0)
        print(f"推荐成功率: {success_rate:.1%}")

        # 显示偏好类别
        preferred_categories = insights.get("preferred_categories", [])
        if preferred_categories:
            print("\n最感兴趣的类别:")
            for i, (category, score) in enumerate(preferred_categories[:3], 1):
                print(f"  {i}. {category} (偏好强度: {score:.2f})")

        # 显示拒绝模式
        rejection_patterns = insights.get("rejection_patterns", {})
        if rejection_patterns and "main_reason" in rejection_patterns:
            main_reason, count = rejection_patterns["main_reason"]
            print(f"\n主要拒绝原因: {main_reason} (共{count}次)")

        # 显示交互统计
        state = self.user_state_manager.get_user_state(self.current_user)
        total_interactions = len(state.get("interaction_history", []))
        print(f"\n总交互次数: {total_interactions}")

        # 显示连续拒绝次数
        consecutive_rejections = state.get("rejection_stats", {}).get("consecutive", 0)
        if consecutive_rejections > 0:
            print(f"当前连续拒绝次数: {consecutive_rejections}")
            if consecutive_rejections >= 3:
                print("[注意] 连续拒绝次数较高，系统已自动调整推荐策略。")

    def update_user_preferences(self):
        """手动更新用户偏好"""
        if not self.current_user:
            print("错误: 请先登录")
            return

        print("\n--- 更新用户偏好 ---")
        print("当前支持的偏好设置:")
        print("1. 预算范围")
        print("2. 兴趣类别偏好")
        print("3. 其他偏好（交通方便、人少等）")
        print("4. 返回主菜单")

        choice = input("请选择要设置的偏好类型 (1-4): ").strip()

        if choice == "1":
            self._update_budget_preference()
        elif choice == "2":
            self._update_category_preferences()
        elif choice == "3":
            self._update_other_preferences()
        elif choice == "4":
            return
        else:
            print("无效选择")

    def _update_budget_preference(self):
        """更新预算偏好"""
        print("\n--- 设置预算范围 ---")
        print("请选择您的预算范围:")
        print("1. 经济型 (0-200元)")
        print("2. 中等预算 (200-500元)")
        print("3. 较高预算 (500-1000元)")
        print("4. 豪华型 (1000元以上)")
        print("5. 自定义预算范围")

        choice = input("请选择 (1-5): ").strip()

        budget_map = {
            "1": "经济型 (0-200元)",
            "2": "中等预算 (200-500元)",
            "3": "较高预算 (500-1000元)",
            "4": "豪华型 (1000元以上)",
        }

        if choice in budget_map:
            budget = budget_map[choice]
        elif choice == "5":
            custom_budget = input("请输入自定义预算范围 (例如: '300-800元'): ").strip()
            if custom_budget:
                budget = custom_budget
            else:
                print("无效的预算范围")
                return
        else:
            print("无效选择")
            return

        # 更新偏好
        preferences = {"budget_range": budget}
        self.auth_manager.update_user_preferences(self.current_user, preferences)
        self.user_preferences["budget_range"] = budget

        print(f"预算范围已设置为: {budget}")

    def _update_category_preferences(self):
        """更新类别偏好"""
        print("\n--- 设置兴趣类别偏好 ---")
        print("请选择您感兴趣的景点类别 (可多选，用逗号分隔):")
        print("1. 历史文化")
        print("2. 自然风光")
        print("3. 主题乐园")
        print("4. 美食购物")
        print("5. 现代建筑")
        print("6. 休闲度假")
        print("7. 户外运动")

        choices = input("请选择 (例如: '1,3,5'): ").strip().split(",")

        category_map = {
            "1": "历史文化",
            "2": "自然风光",
            "3": "主题乐园",
            "4": "美食购物",
            "5": "现代建筑",
            "6": "休闲度假",
            "7": "户外运动",
        }

        selected_categories = []
        for choice in choices:
            choice = choice.strip()
            if choice in category_map:
                selected_categories.append(category_map[choice])

        if not selected_categories:
            print("未选择任何类别")
            return

        # 更新偏好
        category_prefs = {}
        for category in selected_categories:
            category_prefs[category] = 0.8  # 设置较高偏好分数

        preferences = {"category_preferences": category_prefs}
        self.auth_manager.update_user_preferences(self.current_user, preferences)
        self.user_preferences["category_preferences"] = category_prefs

        print(f"兴趣类别偏好已设置为: {', '.join(selected_categories)}")

    def _update_other_preferences(self):
        """更新其他偏好"""
        print("\n--- 设置其他偏好 ---")
        print("请选择您的其他偏好 (可多选，用逗号分隔):")
        print("1. 交通方便")
        print("2. 人少安静")
        print("3. 适合拍照")
        print("4. 适合家庭")
        print("5. 适合情侣")
        print("6. 有讲解服务")
        print("7. 距离近")

        choices = input("请选择 (例如: '1,3,5'): ").strip().split(",")

        preference_map = {
            "1": "交通方便",
            "2": "人少安静",
            "3": "适合拍照",
            "4": "适合家庭",
            "5": "适合情侣",
            "6": "有讲解服务",
            "7": "距离近",
        }

        other_prefs = {}
        for choice in choices:
            choice = choice.strip()
            if choice in preference_map:
                other_prefs[preference_map[choice]] = True

        if not other_prefs:
            print("未选择任何偏好")
            return

        # 更新偏好
        preferences = {"explicit_preferences": other_prefs}
        self.auth_manager.update_user_preferences(self.current_user, preferences)

        if "explicit_preferences" not in self.user_preferences:
            self.user_preferences["explicit_preferences"] = {}

        self.user_preferences["explicit_preferences"].update(other_prefs)

        print(f"其他偏好已设置为: {', '.join(other_prefs.keys())}")


def main():
    """主函数"""
    print("=" * 60)
    print("欢迎使用 MyAgentDemo 智能旅游助手 - 增强版")
    print("=" * 60)
    print("本版本包含以下增强功能:")
    print("1. 用户认证系统（注册/登录）")
    print("2. 用户偏好记忆与学习")
    print("3. 门票可用性检查与备选推荐")
    print("4. 拒绝学习与策略调整")
    print("5. 个性化推荐与反馈收集")
    print("=" * 60)
    print("注意: 本版本要求用户登录后才能使用所有功能。")

    # 创建应用程序实例
    app = EnhancedConsoleApp()

    # 显示主菜单
    app.show_main_menu()


if __name__ == "__main__":
    main()
