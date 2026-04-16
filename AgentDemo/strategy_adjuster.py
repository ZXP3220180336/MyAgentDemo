"""
策略调整器 - 根据用户反馈和学习到的偏好调整推荐策略
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import random


class StrategyAdjuster:
    """策略调整器，根据用户状态调整推荐参数"""

    def __init__(self, state_manager):
        """
        初始化策略调整器

        Args:
            state_manager: UserStateManager实例
        """
        self.state_manager = state_manager

    def adjust_recommendation_parameters(self, username: str, base_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据用户状态调整推荐参数

        Args:
            username: 用户名
            base_parameters: 基础推荐参数

        Returns:
            调整后的推荐参数
        """
        state = self.state_manager.get_user_state(username)
        adjusted = base_parameters.copy()

        # 1. 基于连续拒绝次数的调整
        consecutive_rejections = state.get("rejection_stats", {}).get("consecutive", 0)

        if consecutive_rejections >= 3:
            # 连续拒绝3次以上，大幅调整策略
            adjusted["strategy"] = "aggressive_diversification"
            adjusted["diversity_weight"] = 0.8
            adjusted["novelty_weight"] = 0.7
            adjusted["risk_tolerance"] = "high"

            # 记录调整原因
            adjusted["adjustment_reason"] = f"连续拒绝{consecutive_rejections}次"

        elif consecutive_rejections >= 2:
            # 连续拒绝2次，适度调整
            adjusted["strategy"] = "moderate_adjustment"
            adjusted["diversity_weight"] = 0.5
            adjusted["novelty_weight"] = 0.4
            adjusted["risk_tolerance"] = "medium"

        # 2. 基于拒绝原因分布的调整
        rejection_stats = state.get("rejection_stats", {})
        total_rejections = rejection_stats.get("total", 0)

        if total_rejections > 0:
            # 检查主要拒绝原因
            reason_keys = [k for k in rejection_stats.keys()
                          if k not in ["total", "consecutive", "last_rejection_time"]]

            if reason_keys:
                main_reason = max(reason_keys, key=lambda k: rejection_stats.get(k, 0))

                if main_reason == "价格太高":
                    adjusted["budget_constraint"] = "strict"
                    adjusted["max_price_multiplier"] = 0.8  # 降低最高价格限制
                    if "adjustment_reason" not in adjusted:
                        adjusted["adjustment_reason"] = "主要拒绝原因: 价格太高"

                elif main_reason == "距离太远":
                    adjusted["max_distance_km"] = adjusted.get("max_distance_km", 50) * 0.7
                    adjusted["location_priority"] = "proximity"
                    if "adjustment_reason" not in adjusted:
                        adjusted["adjustment_reason"] = "主要拒绝原因: 距离太远"

                elif main_reason == "不感兴趣":
                    # 尝试不同类别
                    adjusted["category_exploration_rate"] = 0.4
                    adjusted["preference_strength"] = "weak"  # 弱化现有偏好
                    if "adjustment_reason" not in adjusted:
                        adjusted["adjustment_reason"] = "主要拒绝原因: 不感兴趣"

                elif main_reason == "已经去过":
                    adjusted["novelty_weight"] = adjusted.get("novelty_weight", 0.3) + 0.3
                    adjusted["exclude_visited"] = True
                    if "adjustment_reason" not in adjusted:
                        adjusted["adjustment_reason"] = "主要拒绝原因: 已经去过"

        # 3. 基于用户偏好的调整
        preferences = state.get("preferences", {})

        # 预算调整
        budget_range = preferences.get("budget_range")
        if budget_range:
            if "经济型" in budget_range or "便宜" in budget_range:
                adjusted["price_sensitivity"] = "high"
                adjusted["budget_tier"] = "low"
            elif "高端" in budget_range or "豪华" in budget_range:
                adjusted["price_sensitivity"] = "low"
                adjusted["budget_tier"] = "high"

        # 类别偏好调整
        category_prefs = preferences.get("category_preferences", {})
        if category_prefs:
            # 计算偏好强度
            pref_values = list(category_prefs.values())
            if pref_values:
                avg_pref = sum(pref_values) / len(pref_values)

                if avg_pref < 0.3:
                    # 偏好不明显，增加探索
                    adjusted["exploration_rate"] = 0.6
                elif avg_pref > 0.7:
                    # 偏好明显，强化利用
                    adjusted["exploitation_rate"] = 0.8

                # 设置首选类别
                top_categories = sorted(category_prefs.items(), key=lambda x: x[1], reverse=True)[:2]
                if top_categories:
                    adjusted["preferred_categories"] = [cat for cat, _ in top_categories]

        # 4. 基于接受历史的调整
        acceptance_stats = state.get("acceptance_stats", {})
        recent_acceptances = acceptance_stats.get("recent_acceptances", [])

        if recent_acceptances:
            # 分析最近接受的景点特征
            accepted_categories = []
            for acceptance in recent_acceptances[-3:]:  # 最近3次接受
                rec = acceptance.get("recommendation", {})
                category = rec.get("category")
                if category:
                    accepted_categories.append(category)

            if accepted_categories:
                # 偏好最近接受的类别
                from collections import Counter
                category_counter = Counter(accepted_categories)
                if category_counter:
                    preferred_category = category_counter.most_common(1)[0][0]
                    adjusted["recently_accepted_category"] = preferred_category
                    adjusted["category_reinforcement"] = 0.3

        # 5. 应用活动策略调整
        strategy_adjustments = state.get("strategy_adjustments", [])
        if strategy_adjustments:
            # 获取最近的有效调整
            active_adjustments = [adj for adj in strategy_adjustments
                                  if self._is_adjustment_active(adj)]

            for adj in active_adjustments[-2:]:  # 应用最近2个调整
                adj_type = adj.get("strategy_type", "")
                params = adj.get("parameters", {})

                if adj_type == "adjust_budget_filter":
                    adjusted["budget_filter_strength"] = params.get("budget_reduction", "20%")
                elif adj_type == "prioritize_nearby":
                    adjusted["distance_weight"] = 0.8
                elif adj_type == "explore_new_categories":
                    adjusted["category_exploration"] = True
                    adjusted["exploration_rate"] = params.get("exploration_rate", 0.3)

        # 6. 添加元数据
        adjusted["adjusted_at"] = datetime.now().isoformat()
        adjusted["adjustment_count"] = len([k for k in adjusted.keys()
                                           if k not in base_parameters])

        return adjusted

    def generate_personalized_query(self, username: str, base_query: str) -> str:
        """
        生成个性化查询语句

        Args:
            username: 用户名
            base_query: 基础查询

        Returns:
            个性化查询语句
        """
        state = self.state_manager.get_user_state(username)
        preferences = state.get("preferences", {})

        personalized_parts = []

        # 添加预算信息
        budget_range = preferences.get("budget_range")
        if budget_range:
            if "经济型" in budget_range or "便宜" in budget_range:
                personalized_parts.append("经济实惠")
            elif "高端" in budget_range or "豪华" in budget_range:
                personalized_parts.append("高端体验")

        # 添加类别偏好
        category_prefs = preferences.get("category_preferences", {})
        if category_prefs:
            top_categories = sorted(category_prefs.items(), key=lambda x: x[1], reverse=True)[:1]
            if top_categories:
                personalized_parts.append(top_categories[0][0])

        # 添加拒绝学习提示
        consecutive_rejections = state.get("rejection_stats", {}).get("consecutive", 0)
        if consecutive_rejections >= 2:
            personalized_parts.append(f"避免近期拒绝的类型")

        # 构建最终查询
        if personalized_parts:
            personalized_str = "，".join(personalized_parts)
            return f"{base_query}，要求：{personalized_str}"
        else:
            return base_query

    def should_try_different_approach(self, username: str) -> bool:
        """
        判断是否应该尝试完全不同的方法

        Args:
            username: 用户名

        Returns:
            是否应该尝试不同方法
        """
        state = self.state_manager.get_user_state(username)

        # 检查连续拒绝次数
        consecutive_rejections = state.get("rejection_stats", {}).get("consecutive", 0)
        if consecutive_rejections >= 4:
            return True

        # 检查总体拒绝率
        total_feedback = (state.get("acceptance_stats", {}).get("total", 0) +
                         state.get("rejection_stats", {}).get("total", 0))
        if total_feedback > 10:  # 有足够历史数据
            rejection_rate = state.get("rejection_stats", {}).get("total", 0) / total_feedback
            if rejection_rate > 0.8:  # 拒绝率超过80%
                return True

        # 检查策略调整效果
        strategy_adjustments = state.get("strategy_adjustments", [])
        if strategy_adjustments:
            recent_adjustments = [adj for adj in strategy_adjustments[-3:]
                                  if self._is_adjustment_active(adj)]
            if len(recent_adjustments) >= 2:
                # 最近有多个调整但可能效果不佳
                return True

        return False

    def get_different_approach_suggestion(self, username: str) -> Dict[str, Any]:
        """
        获取不同方法的建议

        Args:
            username: 用户名

        Returns:
            不同方法的建议
        """
        state = self.state_manager.get_user_state(username)
        preferences = state.get("preferences", {})

        suggestions = []

        # 建议1: 尝试完全不同的类别
        category_prefs = preferences.get("category_preferences", {})
        if category_prefs:
            # 找到最不喜欢的类别
            if category_prefs:
                least_preferred = min(category_prefs.items(), key=lambda x: x[1])[0]
                suggestions.append(f"尝试{least_preferred}类景点")

        # 建议2: 调整预算范围
        budget_range = preferences.get("budget_range")
        if budget_range:
            if "经济型" in budget_range:
                suggestions.append("尝试中等预算的选择")
            else:
                suggestions.append("尝试更经济的选择")

        # 建议3: 调整时间/季节
        suggestions.append("考虑不同季节或时间的景点")

        # 建议4: 调整旅行方式
        suggestions.append("尝试不同类型的旅行体验（如文化深度游、自然探险等）")

        return {
            "should_try_different": self.should_try_different_approach(username),
            "suggestions": suggestions[:3],  # 返回前3个建议
            "reason": "基于您的反馈历史，建议尝试不同的推荐策略"
        }

    def _is_adjustment_active(self, adjustment: Dict[str, Any], hours_threshold: int = 48) -> bool:
        """
        判断调整是否仍在有效期内

        Args:
            adjustment: 调整记录
            hours_threshold: 有效小时数

        Returns:
            是否有效
        """
        applied_at = adjustment.get("applied_at")
        if not applied_at:
            return False

        try:
            applied_time = datetime.fromisoformat(applied_at.replace('Z', '+00:00'))
            time_diff = datetime.now() - applied_time
            return time_diff.total_seconds() < hours_threshold * 3600
        except (ValueError, TypeError):
            return False


# 测试代码
if __name__ == "__main__":
    print("测试策略调整器...")

    # 需要先创建UserStateManager
    from user_state_manager import UserStateManager

    state_manager = UserStateManager()
    adjuster = StrategyAdjuster(state_manager)

    test_user = "strategy_test_user"

    # 清理测试数据
    import os
    test_file = os.path.join("user_states", f"{hashlib.md5(test_user.encode()).hexdigest()[:16]}.json")
    if os.path.exists(test_file):
        os.remove(test_file)

    # 创建测试状态
    state = state_manager.get_user_state(test_user)

    # 设置测试偏好和拒绝记录
    state["preferences"]["budget_range"] = "经济型"
    state["preferences"]["category_preferences"] = {
        "历史文化": 0.8,
        "自然风光": 0.3
    }
    state["rejection_stats"]["consecutive"] = 2
    state["rejection_stats"]["total"] = 5
    state["rejection_stats"]["价格太高"] = 3

    state_manager.save_user_state(test_user, state)

    print("\n1. 测试参数调整:")
    base_params = {
        "city": "北京",
        "budget": "中等",
        "categories": ["历史文化", "自然风光"]
    }
    adjusted = adjuster.adjust_recommendation_parameters(test_user, base_params)
    print(f"基础参数: {base_params}")
    print(f"调整后参数: {adjusted}")

    print("\n2. 测试个性化查询生成:")
    base_query = "推荐北京的旅游景点"
    personalized = adjuster.generate_personalized_query(test_user, base_query)
    print(f"基础查询: {base_query}")
    print(f"个性化查询: {personalized}")

    print("\n3. 测试不同方法建议:")
    diff_approach = adjuster.get_different_approach_suggestion(test_user)
    print(f"应该尝试不同方法: {diff_approach['should_try_different']}")
    print(f"建议: {diff_approach['suggestions']}")

    print("\n✅ 策略调整器测试完成")