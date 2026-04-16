"""
拒绝学习与策略调整模块
分析用户拒绝模式，提供智能策略调整建议
与UserStateManager协同工作
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import Counter
import statistics


class RejectionTracker:
    """拒绝跟踪器，专注于拒绝模式分析和策略建议"""

    def __init__(self, state_manager):
        """
        初始化拒绝跟踪器

        Args:
            state_manager: UserStateManager实例
        """
        self.state_manager = state_manager

    def analyze_rejection_patterns(
        self, username: str, lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        分析用户拒绝模式

        Args:
            username: 用户名
            lookback_days: 回溯天数

        Returns:
            拒绝模式分析结果
        """
        state = self.state_manager.get_user_state(username)
        history = state.get("interaction_history", [])

        # 过滤指定时间范围内的反馈记录
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        cutoff_iso = cutoff_date.isoformat()

        feedback_history = [
            interaction
            for interaction in history
            if (
                interaction.get("type") == "feedback"
                and interaction.get("data", {}).get("feedback_type") == "reject"
                and interaction.get("timestamp", "") >= cutoff_iso
            )
        ]

        analysis = {
            "total_rejections": len(feedback_history),
            "reasons_distribution": {},
            "time_patterns": {},
            "category_patterns": {},
            "consecutive_patterns": {},
            "recommendation_quality_insights": [],
        }

        if not feedback_history:
            return analysis

        # 1. 原因分布分析
        reasons = []
        for feedback in feedback_history:
            reason = feedback.get("data", {}).get("reason")
            if reason:
                reasons.append(reason)

        if reasons:
            reason_counter = Counter(reasons)
            analysis["reasons_distribution"] = dict(reason_counter.most_common())

            # 主要拒绝原因
            if reason_counter:
                main_reason, main_count = reason_counter.most_common(1)[0]
                analysis["primary_reason"] = {
                    "reason": main_reason,
                    "count": main_count,
                    "percentage": main_count / len(reasons) * 100,
                }

        # 2. 时间模式分析（简化）
        # 实际中应该分析星期几、时间段等
        time_groups = {"morning": 0, "afternoon": 0, "evening": 0}
        for feedback in feedback_history:
            timestamp = feedback.get("timestamp")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    hour = dt.hour
                    if 6 <= hour < 12:
                        time_groups["morning"] += 1
                    elif 12 <= hour < 18:
                        time_groups["afternoon"] += 1
                    else:
                        time_groups["evening"] += 1
                except (ValueError, TypeError):
                    pass

        analysis["time_patterns"] = time_groups

        # 3. 连续拒绝模式分析
        consecutive_counts = []
        current_streak = 0

        for interaction in sorted(history, key=lambda x: x.get("timestamp", "")):
            if (
                interaction.get("type") == "feedback"
                and interaction.get("data", {}).get("feedback_type") == "reject"
            ):
                current_streak += 1
            else:
                if current_streak > 0:
                    consecutive_counts.append(current_streak)
                    current_streak = 0

        if current_streak > 0:
            consecutive_counts.append(current_streak)

        if consecutive_counts:
            analysis["consecutive_patterns"] = {
                "max_consecutive": max(consecutive_counts),
                "avg_consecutive": statistics.mean(consecutive_counts),
                "common_streak_length": Counter(consecutive_counts).most_common(1)[0][0]
                if consecutive_counts
                else 0,
            }

        # 4. 推荐质量洞察（简化）
        # 实际中应该分析推荐特征与拒绝原因的关系
        analysis["recommendation_quality_insights"] = self._generate_quality_insights(
            feedback_history
        )

        return analysis

    def generate_strategy_recommendations(self, username: str) -> List[Dict[str, Any]]:
        """
        基于拒绝模式生成策略推荐

        Args:
            username: 用户名

        Returns:
            策略推荐列表
        """
        analysis = self.analyze_rejection_patterns(username)
        recommendations = []

        total_rejections = analysis["total_rejections"]
        if total_rejections == 0:
            recommendations.append(
                {
                    "type": "no_rejections",
                    "priority": "low",
                    "description": "用户暂无拒绝记录，保持当前推荐策略",
                    "action": "maintain_current_strategy",
                }
            )
            return recommendations

        # 基于主要拒绝原因的推荐
        if "primary_reason" in analysis:
            primary = analysis["primary_reason"]
            reason = primary["reason"]

            if reason == "价格太高":
                recommendations.append(
                    {
                        "type": "budget_adjustment",
                        "priority": "high",
                        "description": f"用户主要因价格拒绝（{primary['percentage']:.1f}%），建议调整预算筛选",
                        "action": "adjust_budget_filter",
                        "parameters": {"budget_reduction": "20%"},
                    }
                )

            elif reason == "距离太远":
                recommendations.append(
                    {
                        "type": "location_adjustment",
                        "priority": "high",
                        "description": f"用户主要因距离拒绝（{primary['percentage']:.1f}%），建议优先推荐附近景点",
                        "action": "prioritize_nearby",
                        "parameters": {"max_distance_km": 10},
                    }
                )

            elif reason == "不感兴趣":
                recommendations.append(
                    {
                        "type": "category_exploration",
                        "priority": "medium",
                        "description": f"用户主要因兴趣不符拒绝（{primary['percentage']:.1f}%），建议尝试新类别",
                        "action": "explore_new_categories",
                        "parameters": {"exploration_rate": 0.3},
                    }
                )

            elif reason == "已经去过":
                recommendations.append(
                    {
                        "type": "novelty_focus",
                        "priority": "medium",
                        "description": f"用户主要因已去过拒绝（{primary['percentage']:.1f}%），建议推荐新景点",
                        "action": "prioritize_new_attractions",
                        "parameters": {"novelty_weight": 0.8},
                    }
                )

        # 基于连续拒绝模式的推荐
        if "consecutive_patterns" in analysis:
            consecutive_patterns = analysis["consecutive_patterns"]
            max_consecutive = consecutive_patterns.get("max_consecutive", 0)

            if max_consecutive >= 3:
                recommendations.append(
                    {
                        "type": "strategy_reset",
                        "priority": "critical",
                        "description": f"用户曾连续拒绝{max_consecutive}次，建议重置推荐策略",
                        "action": "reset_recommendation_strategy",
                        "parameters": {"reset_type": "full"},
                    }
                )

            elif max_consecutive >= 2:
                recommendations.append(
                    {
                        "type": "diversity_boost",
                        "priority": "medium",
                        "description": f"用户有连续拒绝模式，建议增加推荐多样性",
                        "action": "increase_diversity",
                        "parameters": {"diversity_factor": 0.5},
                    }
                )

        # 基于时间模式的推荐
        time_patterns = analysis.get("time_patterns", {})
        if time_patterns:
            max_time = max(time_patterns.items(), key=lambda x: x[1])
            if max_time[1] > total_rejections * 0.5:  # 超过50%在某个时间段
                recommendations.append(
                    {
                        "type": "temporal_adjustment",
                        "priority": "low",
                        "description": f"用户多在{self._translate_time_period(max_time[0])}拒绝，建议调整推荐时间",
                        "action": "adjust_recommendation_timing",
                        "parameters": {"avoid_period": max_time[0]},
                    }
                )

        # 基于总体拒绝率的推荐
        state = self.state_manager.get_user_state(username)
        total_feedback = state.get("acceptance_stats", {}).get("total", 0) + state.get(
            "rejection_stats", {}
        ).get("total", 0)

        if total_feedback > 0:
            rejection_rate = (
                state.get("rejection_stats", {}).get("total", 0) / total_feedback
            )

            if rejection_rate > 0.7:  # 拒绝率超过70%
                recommendations.append(
                    {
                        "type": "aggressive_adjustment",
                        "priority": "high",
                        "description": f"用户总体拒绝率较高（{rejection_rate:.0%}），建议大幅调整策略",
                        "action": "aggressive_strategy_adjustment",
                        "parameters": {"adjustment_strength": "high"},
                    }
                )
            elif rejection_rate > 0.5:  # 拒绝率超过50%
                recommendations.append(
                    {
                        "type": "moderate_adjustment",
                        "priority": "medium",
                        "description": f"用户拒绝率适中（{rejection_rate:.0%}），建议适度调整策略",
                        "action": "moderate_strategy_adjustment",
                        "parameters": {"adjustment_strength": "medium"},
                    }
                )

        # 按优先级排序
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return recommendations

    def apply_strategy_adjustment(
        self, username: str, strategy_type: str, parameters: Dict[str, Any] = None
    ) -> bool:
        """
        应用策略调整

        Args:
            username: 用户名
            strategy_type: 策略类型
            parameters: 调整参数

        Returns:
            是否成功应用
        """
        state = self.state_manager.get_user_state(username)

        # 记录策略调整
        adjustment = {
            "strategy_type": strategy_type,
            "parameters": parameters or {},
            "applied_at": datetime.now().isoformat(),
            "applied_by": "rejection_tracker",
        }

        if "strategy_adjustments" not in state:
            state["strategy_adjustments"] = []

        state["strategy_adjustments"].append(adjustment)

        # 根据策略类型更新用户状态
        if strategy_type == "adjust_budget_filter":
            # 更新预算偏好
            current_budget = state["preferences"].get("budget_range", "")
            if "budget_reduction" in parameters:
                # 简化：标记需要降低预算
                state["preferences"]["explicit_preferences"]["require_lower_budget"] = (
                    True
                )

        elif strategy_type == "prioritize_nearby":
            state["preferences"]["explicit_preferences"]["prefer_nearby"] = True

        elif strategy_type == "explore_new_categories":
            # 标记需要探索新类别
            state["preferences"]["explicit_preferences"]["explore_new_categories"] = (
                True
            )

        elif strategy_type == "reset_recommendation_strategy":
            # 重置一些统计（但保留历史）
            state["rejection_stats"]["consecutive"] = 0
            state["preferences"]["explicit_preferences"]["strategy_reset"] = True

        # 保存状态
        self.state_manager.save_user_state(username, state)

        print(f"已应用策略调整: {strategy_type} for {username}")
        return True

    def get_adjustment_effectiveness(
        self, username: str, lookback_days: int = 7
    ) -> Dict[str, Any]:
        """
        评估策略调整效果

        Args:
            username: 用户名
            lookback_days: 回溯天数

        Returns:
            调整效果评估
        """
        state = self.state_manager.get_user_state(username)

        # 获取最近的应用调整
        adjustments = state.get("strategy_adjustments", [])
        if not adjustments:
            return {"has_adjustments": False, "message": "暂无策略调整记录"}

        # 获取调整后的反馈数据
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        cutoff_iso = cutoff_date.isoformat()

        recent_feedback = [
            interaction
            for interaction in state.get("interaction_history", [])
            if (
                interaction.get("type") == "feedback"
                and interaction.get("timestamp", "") >= cutoff_iso
            )
        ]

        recent_adjustments = [
            adj for adj in adjustments if adj.get("applied_at", "") >= cutoff_iso
        ]

        # 简化效果评估
        effect = {
            "has_adjustments": True,
            "recent_adjustments_count": len(recent_adjustments),
            "recent_feedback_count": len(recent_feedback),
            "acceptance_rate_change": "待计算",
            "effectiveness_rating": "待评估",
        }

        if recent_feedback:
            acceptances = sum(
                1
                for f in recent_feedback
                if f.get("data", {}).get("feedback_type") == "accept"
            )
            rejection_rate = (
                1 - (acceptances / len(recent_feedback)) if recent_feedback else 0
            )

            # 与历史平均比较（简化）
            total_feedback = state.get("acceptance_stats", {}).get(
                "total", 0
            ) + state.get("rejection_stats", {}).get("total", 0)
            historical_acceptance = (
                state.get("acceptance_stats", {}).get("total", 0) / total_feedback
                if total_feedback > 0
                else 0
            )

            recent_acceptance = (
                acceptances / len(recent_feedback) if recent_feedback else 0
            )

            effect["recent_acceptance_rate"] = recent_acceptance
            effect["historical_acceptance_rate"] = historical_acceptance
            effect["improvement"] = recent_acceptance - historical_acceptance

            if recent_acceptance > historical_acceptance + 0.1:
                effect["effectiveness_rating"] = "优秀"
            elif recent_acceptance > historical_acceptance:
                effect["effectiveness_rating"] = "良好"
            else:
                effect["effectiveness_rating"] = "需要优化"

        return effect

    def _generate_quality_insights(self, feedback_history: List[Dict]) -> List[str]:
        """生成推荐质量洞察"""
        insights = []

        if not feedback_history:
            return insights

        # 分析拒绝原因的集中度
        reasons = [
            f.get("data", {}).get("reason")
            for f in feedback_history
            if f.get("data", {}).get("reason")
        ]
        if reasons:
            reason_counter = Counter(reasons)
            if len(reason_counter) <= 2:
                insights.append(
                    "拒绝原因较为集中，可能表明推荐系统在某些方面持续不符合用户期望"
                )

        # 检查是否有模式化的拒绝（如总是拒绝高价景点）
        # 简化实现
        insights.append("建议进一步分析推荐特征与拒绝原因的相关性")

        return insights

    def _translate_time_period(self, period: str) -> str:
        """翻译时间段"""
        translations = {"morning": "上午", "afternoon": "下午", "evening": "晚上"}
        return translations.get(period, period)


# 测试代码
if __name__ == "__main__":
    print("测试拒绝跟踪器...")

    # 需要先创建UserStateManager
    from user_state_manager import UserStateManager

    state_manager = UserStateManager()
    tracker = RejectionTracker(state_manager)

    test_user = "rejection_test_user"

    # 清理测试数据
    import os

    test_file = os.path.join(
        "user_states", f"{hashlib.md5(test_user.encode()).hexdigest()[:16]}.json"
    )
    if os.path.exists(test_file):
        os.remove(test_file)

    # 创建测试数据
    state = state_manager.get_user_state(test_user)

    # 模拟一些拒绝记录
    test_recommendations = [
        {"id": "rec1", "name": "故宫", "category": "历史文化", "price": "60元"},
        {"id": "rec2", "name": "颐和园", "category": "历史文化", "price": "50元"},
        {"id": "rec3", "name": "长城", "category": "自然风光", "price": "45元"},
    ]

    # 记录拒绝
    state_manager.record_feedback(
        test_user, "reject", test_recommendations[0], "价格太高"
    )
    state_manager.record_feedback(
        test_user, "reject", test_recommendations[1], "价格太高"
    )
    state_manager.record_feedback(
        test_user, "reject", test_recommendations[2], "距离太远"
    )

    print("\n1. 分析拒绝模式:")
    analysis = tracker.analyze_rejection_patterns(test_user)
    print(f"总拒绝次数: {analysis['total_rejections']}")
    print(f"原因分布: {analysis['reasons_distribution']}")

    print("\n2. 生成策略推荐:")
    recommendations = tracker.generate_strategy_recommendations(test_user)
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"{i}. [{rec['priority']}] {rec['description']}")

    print("\n3. 应用策略调整:")
    if recommendations:
        success = tracker.apply_strategy_adjustment(
            test_user,
            recommendations[0]["action"],
            recommendations[0].get("parameters", {}),
        )
        print(f"应用策略调整: {'成功' if success else '失败'}")

    print("\n4. 评估调整效果:")
    effectiveness = tracker.get_adjustment_effectiveness(test_user)
    print(f"调整效果: {effectiveness}")

    print("\n拒绝跟踪器测试完成")
