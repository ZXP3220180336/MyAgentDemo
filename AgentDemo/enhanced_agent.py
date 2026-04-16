"""
增强版智能体 - 集成用户状态管理、拒绝学习和策略调整
继承自基础Agent类，添加个性化推荐能力
"""

import os
from typing import Dict, Any, Optional
from .Agent import Agent
from .user_state_manager import UserStateManager
from .rejection_tracker import RejectionTracker
from .strategy_adjuster import StrategyAdjuster
from .ticket_api_client import TicketAPIFactory


class EnhancedAgent(Agent):
    """
    增强版智能体，支持用户偏好记忆、拒绝学习和个性化推荐
    """

    def __init__(
        self,
        available_tools: Dict[str, Any],
        llmClient,
        user_id: str = None,
        enable_memory: bool = True,
        enable_rejection_learning: bool = True,
        enable_ticket_check: bool = False,
    ):
        """
        初始化增强版智能体

        Args:
            available_tools: 可用工具字典
            llmClient: LLM客户端
            user_id: 用户ID（用于个性化）
            enable_memory: 是否启用用户记忆
            enable_rejection_learning: 是否启用拒绝学习
            enable_ticket_check: 是否启用门票检查
        """
        super().__init__(available_tools, llmClient)

        self.user_id = user_id
        self.enable_memory = enable_memory
        self.enable_rejection_learning = enable_rejection_learning
        self.enable_ticket_check = enable_ticket_check

        # 初始化管理器
        if enable_memory:
            self.state_manager = UserStateManager()
            self.rejection_tracker = RejectionTracker(self.state_manager)
            self.strategy_adjuster = StrategyAdjuster(self.state_manager)

            if user_id:
                self.user_state = self.state_manager.get_user_state(user_id)
            else:
                self.user_state = None
        else:
            self.state_manager = None
            self.rejection_tracker = None
            self.strategy_adjuster = None
            self.user_state = None

        # 初始化票务客户端
        if enable_ticket_check:
            try:
                self.ticket_client = TicketAPIFactory.create_from_env()
            except Exception as e:
                print(f"警告：初始化票务客户端失败: {e}")
                self.ticket_client = None
        else:
            self.ticket_client = None

        # 增强的工具调用统计
        self.enhanced_stats = {
            "personalized_recommendations": 0,
            "rejection_learned": 0,
            "strategy_adjusted": 0,
            "ticket_checked": 0,
        }

    def run_assistant_enhanced(
        self,
        user_input: str,
        system_prompt: str,
        max_iterations: int = 5,
        extract_preferences: bool = True,
    ) -> str:
        """
        增强版运行助手，支持用户偏好提取和个性化

        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            max_iterations: 最大迭代次数
            extract_preferences: 是否从输入中提取偏好

        Returns:
            执行结果
        """
        # 1. 提取用户偏好（如果启用）
        if (
            self.enable_memory
            and self.user_id
            and extract_preferences
            and self.state_manager
        ):
            preferences = self.state_manager.extract_preferences_from_text(user_input)
            if preferences.get("extracted_keywords"):
                print(f"提取到用户偏好: {preferences['extracted_keywords']}")
                self.state_manager.update_user_preferences(self.user_id, preferences)

                # 记录交互
                self.state_manager.record_interaction(
                    self.user_id,
                    "query",
                    {
                        "query": user_input,
                        "extracted_preferences": preferences,
                        "has_preferences": bool(preferences.get("extracted_keywords")),
                    },
                )

                self.enhanced_stats["personalized_recommendations"] += 1

        # 2. 增强系统提示词（添加用户上下文）
        enhanced_prompt = self._enhance_system_prompt(system_prompt)

        # 3. 运行基础ReAct循环
        print(f"用户输入: {user_input}")
        self.prompt_history.append(f"用户请求: {user_input}")

        iteration = 0
        while iteration < max_iterations:
            # 构建当前对话上下文
            conversation_context = "\n".join(self.prompt_history[-10:])  # 最近10条

            # 调用LLM
            llm_response = self.llm.generate(conversation_context, enhanced_prompt)

            if not llm_response:
                print("LLM未返回有效响应，结束对话。")
                break

            # 添加到历史
            self.prompt_history.append(llm_response)
            print(f"模型响应:\n{llm_response}")

            # 检查是否应该结束
            if "Finish:" in llm_response:
                finish_text = llm_response.split("Finish:")[-1].strip()
                print(f"任务完成: {finish_text}")
                break

            # 解析行动
            if "Action:" in llm_response:
                action_line = ""
                for line in llm_response.split("\n"):
                    if line.strip().startswith("Action:"):
                        action_line = line.strip()
                        break

                if action_line:
                    action_str = action_line[7:].strip()  # 移除"Action:"
                    tool_name, kwargs = self.parse_action(action_str)

                    if tool_name in self.available_tools:
                        print(f"执行工具: {tool_name}({kwargs})")

                        try:
                            # 增强工具调用：添加用户上下文
                            enhanced_kwargs = self._enhance_tool_parameters(
                                tool_name, kwargs
                            )

                            # 执行工具
                            tool_result = self.available_tools[tool_name](
                                **enhanced_kwargs
                            )

                            # 处理工具结果
                            processed_result = self._process_tool_result(
                                tool_name, tool_result, kwargs
                            )

                            observation = f"Observation: {processed_result}"
                            self.prompt_history.append(observation)
                            print(f"观察结果:\n{processed_result}")

                            # 记录工具执行（如果启用了记忆）
                            if (
                                self.enable_memory
                                and self.user_id
                                and tool_name
                                in ["get_attraction", "get_attraction_enhanced"]
                            ):
                                self._record_recommendation_interaction(
                                    tool_name, kwargs, processed_result
                                )

                        except Exception as e:
                            error_msg = f"执行工具时出错: {e}"
                            observation = f"Observation: {error_msg}"
                            self.prompt_history.append(observation)
                            print(f"工具执行错误: {e}")
                    else:
                        error_msg = f"未知工具: {tool_name}"
                        observation = f"Observation: {error_msg}"
                        self.prompt_history.append(observation)
                        print(f"{error_msg}")
                else:
                    print("未找到有效的Action行")

            iteration += 1

        # 4. 显示增强统计
        self._display_enhanced_stats()

        # 5. 返回最终结果
        if self.prompt_history:
            return self.prompt_history[-1]
        return "未生成有效结果"

    def _enhance_system_prompt(self, base_prompt: str) -> str:
        """增强系统提示词，包含用户上下文"""
        if not self.enable_memory or not self.user_id or not self.user_state:
            return base_prompt

        user_context = "\n\n## 用户上下文信息（用于个性化推荐）:\n"

        # 添加用户偏好
        preferences = self.user_state.get("preferences", {})
        if preferences:
            user_context += "- 用户偏好:\n"

            budget = preferences.get("budget_range")
            if budget:
                user_context += f"  * 预算范围: {budget}\n"

            category_prefs = preferences.get("category_preferences", {})
            if category_prefs:
                top_categories = sorted(
                    category_prefs.items(), key=lambda x: x[1], reverse=True
                )[:2]
                if top_categories:
                    categories_str = ", ".join([cat for cat, _ in top_categories])
                    user_context += f"  * 兴趣类别: {categories_str}\n"

            explicit_prefs = preferences.get("explicit_preferences", {})
            if explicit_prefs:
                for pref_key, pref_value in explicit_prefs.items():
                    if isinstance(pref_value, bool) and pref_value:
                        user_context += f"  * 偏好: {pref_key}\n"

        # 添加拒绝学习信息
        rejection_stats = self.user_state.get("rejection_stats", {})
        consecutive_rejections = rejection_stats.get("consecutive", 0)
        if consecutive_rejections > 0:
            user_context += (
                f"- 学习信息: 用户已连续拒绝{consecutive_rejections}个推荐\n"
            )

            if consecutive_rejections >= 2:
                user_context += "  * 建议: 尝试不同的推荐策略，避免重复类似错误\n"

            # 主要拒绝原因
            reason_keys = [
                k
                for k in rejection_stats.keys()
                if k not in ["total", "consecutive", "last_rejection_time"]
            ]
            if reason_keys:
                main_reason = max(reason_keys, key=lambda k: rejection_stats.get(k, 0))
                user_context += f"  * 主要拒绝原因: {main_reason}\n"

        # 添加策略建议
        if self.enable_rejection_learning and self.rejection_tracker:
            try:
                recommendations = (
                    self.rejection_tracker.generate_strategy_recommendations(
                        self.user_id
                    )
                )
                if recommendations:
                    user_context += "- 策略建议:\n"
                    for i, rec in enumerate(recommendations[:2], 1):  # 显示前2个
                        user_context += f"  {i}. {rec['description']}\n"
            except Exception as e:
                print(f"生成策略建议时出错: {e}")

        # 添加工具使用指导
        user_context += "\n## 工具使用指导:\n"
        if "get_attraction_enhanced" in self.available_tools:
            user_context += (
                "- 推荐使用`get_attraction_enhanced`工具进行个性化推荐\n"
                "- 该工具支持用户偏好记忆和门票检查\n"
            )

        if self.enable_ticket_check and self.ticket_client:
            user_context += "- 门票检查已启用，可提供可用性信息\n"

        return base_prompt + user_context

    def _enhance_tool_parameters(
        self, tool_name: str, base_kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增强工具参数，添加用户上下文"""
        enhanced = base_kwargs.copy()

        if not self.enable_memory or not self.user_id:
            return enhanced

        # 为景点推荐工具添加增强参数
        if tool_name in ["get_attraction", "get_attraction_enhanced"]:
            enhanced["user_id"] = self.user_id

            if tool_name == "get_attraction_enhanced":
                enhanced["enable_memory"] = self.enable_memory
                enhanced["check_tickets"] = self.enable_ticket_check

            # 添加策略调整参数
            if self.strategy_adjuster:
                strategy_params = (
                    self.strategy_adjuster.adjust_recommendation_parameters(
                        self.user_id, {"tool": tool_name, **base_kwargs}
                    )
                )
                enhanced["strategy_params"] = strategy_params

        return enhanced

    def _process_tool_result(
        self, tool_name: str, result: str, kwargs: Dict[str, Any]
    ) -> str:
        """处理工具结果，添加学习机会"""
        processed = result

        # 检测用户反馈（简化实现）
        feedback_keywords = {
            "接受": "accept",
            "拒绝": "reject",
            "不喜欢": "reject",
            "太贵": "reject",
            "距离远": "reject",
            "不错": "accept",
            "喜欢": "accept",
        }

        # 检查结果中是否包含用户反馈
        if self.enable_memory and self.user_id:
            # 这里应该从对话历史中提取用户反馈
            # 简化：从最近的消息中查找
            recent_messages = (
                self.prompt_history[-3:]
                if len(self.prompt_history) >= 3
                else self.prompt_history
            )

            for message in recent_messages:
                if "用户" in message or "User" in message:
                    lower_msg = message.lower()
                    for keyword, feedback_type in feedback_keywords.items():
                        if keyword in lower_msg:
                            # 记录反馈
                            self._record_user_feedback(
                                feedback_type, kwargs, extracted_reason=keyword
                            )
                            break

        # 如果是推荐结果，添加个性化提示
        if tool_name in ["get_attraction", "get_attraction_enhanced"]:
            if self.enable_memory and self.user_id:
                processed += "\n\n💡 个性化提示: 系统已根据您的偏好和历史反馈调整推荐。"

        return processed

    def _record_recommendation_interaction(
        self, tool_name: str, kwargs: Dict[str, Any], result: str
    ):
        """记录推荐交互"""
        if not self.enable_memory or not self.user_id:
            return

        recommendation_data = {
            "tool": tool_name,
            "parameters": kwargs,
            "result_preview": result[:200] + "..." if len(result) > 200 else result,
            "timestamp": "记录于工具执行时",
        }

        self.state_manager.record_interaction(
            self.user_id, "recommendation_generated", recommendation_data
        )

    def _record_user_feedback(
        self,
        feedback_type: str,
        recommendation: Dict[str, Any],
        extracted_reason: str = None,
    ):
        """记录用户反馈"""
        if not self.enable_memory or not self.user_id:
            return

        # 分类拒绝原因
        reason_mapping = {
            "太贵": "价格太高",
            "距离远": "距离太远",
            "不喜欢": "不感兴趣",
            "去过": "已经去过",
        }

        reason = None
        if feedback_type == "reject" and extracted_reason:
            reason = reason_mapping.get(extracted_reason, "其他原因")

        self.state_manager.record_feedback(
            self.user_id, feedback_type, recommendation, reason
        )

        self.enhanced_stats["rejection_learned"] += 1
        print(
            f"记录用户反馈: {feedback_type}" + (f", 原因: {reason}" if reason else "")
        )

        # 如果连续拒绝多次，应用策略调整
        if (
            feedback_type == "reject"
            and self.enable_rejection_learning
            and self.rejection_tracker
            and self.strategy_adjuster
        ):
            state = self.state_manager.get_user_state(self.user_id)
            consecutive_rejections = state.get("rejection_stats", {}).get(
                "consecutive", 0
            )

            if consecutive_rejections >= 3:
                print("检测到连续3次拒绝，应用策略调整...")
                recommendations = (
                    self.rejection_tracker.generate_strategy_recommendations(
                        self.user_id
                    )
                )

                if recommendations:
                    # 应用最高优先级的推荐
                    top_recommendation = recommendations[0]
                    self.rejection_tracker.apply_strategy_adjustment(
                        self.user_id,
                        top_recommendation["action"],
                        top_recommendation.get("parameters", {}),
                    )
                    self.enhanced_stats["strategy_adjusted"] += 1

    def _display_enhanced_stats(self):
        """显示增强统计信息"""
        if not self.enable_memory:
            return

        print("\n" + "=" * 60)
        print("增强功能统计")
        print("=" * 60)

        print(f"个性化推荐次数: {self.enhanced_stats['personalized_recommendations']}")
        print(f"学习到的用户反馈: {self.enhanced_stats['rejection_learned']}")
        print(f"策略调整次数: {self.enhanced_stats['strategy_adjusted']}")
        print(f"门票检查次数: {self.enhanced_stats['ticket_checked']}")

        if self.user_id and self.user_state:
            state = self.state_manager.get_user_state(self.user_id)
            rejection_stats = state.get("rejection_stats", {})
            acceptance_stats = state.get("acceptance_stats", {})

            total_feedback = rejection_stats.get("total", 0) + acceptance_stats.get(
                "total", 0
            )
            if total_feedback > 0:
                acceptance_rate = acceptance_stats.get("total", 0) / total_feedback
                print(f"用户接受率: {acceptance_rate:.1%}")
                print(f"连续拒绝次数: {rejection_stats.get('consecutive', 0)}")

        print("=" * 60)

    def get_user_insights(self) -> Optional[Dict[str, Any]]:
        """获取用户洞察"""
        if not self.enable_memory or not self.user_id or not self.state_manager:
            return None

        return self.state_manager.get_user_insights(self.user_id)

    def clear_user_memory(self):
        """清除用户记忆（重置用户状态）"""
        if not self.enable_memory or not self.user_id or not self.state_manager:
            return

        # 创建新的默认状态
        default_state = self.state_manager._create_default_state(self.user_id)
        self.state_manager.save_user_state(self.user_id, default_state)
        self.user_state = default_state

        print(f"已清除用户 {self.user_id} 的记忆")


# 测试代码
if __name__ == "__main__":
    print("测试增强版智能体...")

    # 简化测试，需要配置环境变量
    import os
    from dotenv import load_dotenv
    from .LLMClient import OpenAICompatibleClient
    from .Tools import available_tools

    load_dotenv()

    try:
        # 初始化LLM客户端（使用模拟数据避免实际API调用）
        class MockLLMClient:
            def generate(self, user_prompt, system_prompt):
                return 'Thought: 测试思考\nAction: get_weather(city="北京")\nFinish: 测试完成'

        llm_client = MockLLMClient()

        # 创建增强智能体
        agent = EnhancedAgent(
            available_tools=available_tools,
            llmClient=llm_client,
            user_id="test_user_001",
            enable_memory=True,
            enable_rejection_learning=True,
            enable_ticket_check=False,
        )

        print("增强版智能体创建成功")
        print(f"用户ID: {agent.user_id}")
        print(f"启用记忆: {agent.enable_memory}")
        print(f"启用拒绝学习: {agent.enable_rejection_learning}")

        # 测试用户偏好提取
        test_input = "我想去北京玩，预算500元左右，喜欢历史文化景点"
        print(f"\n测试输入: {test_input}")

        # 运行增强版助手（简化）
        result = agent.run_assistant_enhanced(
            user_input=test_input, system_prompt="你是一个旅游助手", max_iterations=2
        )

        print(f"\n测试完成，结果长度: {len(result) if result else 0}")

    except Exception as e:
        print(f"测试过程中出错: {e}")

    print("\n增强版智能体测试完成")
