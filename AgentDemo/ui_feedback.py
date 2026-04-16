"""
用户反馈UI组件
支持命令行和GUI界面的用户反馈收集
"""

import json
from typing import Dict, Any, Optional, Callable
from enum import Enum


class FeedbackType(Enum):
    """反馈类型枚举"""
    ACCEPT = "accept"
    REJECT = "reject"


class RejectionReason(Enum):
    """拒绝原因枚举"""
    TOO_EXPENSIVE = "价格太高"
    TOO_FAR = "距离太远"
    ALREADY_VISITED = "已经去过"
    NOT_INTERESTED = "不感兴趣"
    TIME_NOT_SUITABLE = "时间不合适"
    OTHER = "其他原因"


class Feedback:
    """反馈数据类"""

    def __init__(
        self,
        recommendation_id: str,
        feedback_type: FeedbackType,
        reason: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ):
        self.recommendation_id = recommendation_id
        self.feedback_type = feedback_type
        self.reason = reason
        self.additional_info = additional_info or {}
        self.timestamp = None  # 将在record_feedback中设置

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "recommendation_id": self.recommendation_id,
            "feedback_type": self.feedback_type.value,
            "reason": self.reason,
            "additional_info": self.additional_info,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feedback':
        """从字典创建"""
        feedback = cls(
            recommendation_id=data["recommendation_id"],
            feedback_type=FeedbackType(data["feedback_type"]),
            reason=data.get("reason"),
            additional_info=data.get("additional_info", {})
        )
        feedback.timestamp = data.get("timestamp")
        return feedback


class FeedbackCollector:
    """反馈收集器基类"""

    def __init__(self, on_feedback: Callable[[Feedback], None]):
        """
        初始化反馈收集器

        Args:
            on_feedback: 反馈回调函数
        """
        self.on_feedback = on_feedback
        self.current_recommendation_id = None
        self.current_recommendation_info = None

    def show_recommendation(
        self,
        recommendation_id: str,
        recommendation_info: Dict[str, Any]
    ):
        """
        显示推荐信息

        Args:
            recommendation_id: 推荐ID
            recommendation_info: 推荐信息
        """
        self.current_recommendation_id = recommendation_id
        self.current_recommendation_info = recommendation_info

    def collect_feedback(self) -> Optional[Feedback]:
        """
        收集用户反馈

        Returns:
            反馈对象，用户取消则为None
        """
        raise NotImplementedError("子类必须实现此方法")

    def _create_feedback(
        self,
        feedback_type: FeedbackType,
        reason: Optional[str] = None
    ) -> Feedback:
        """创建反馈对象"""
        feedback = Feedback(
            recommendation_id=self.current_recommendation_id,
            feedback_type=feedback_type,
            reason=reason,
            additional_info={
                "recommendation_info": self.current_recommendation_info
            }
        )
        return feedback


class ConsoleFeedbackCollector(FeedbackCollector):
    """命令行反馈收集器"""

    def collect_feedback(self) -> Optional[Feedback]:
        """通过命令行收集反馈"""
        if not self.current_recommendation_id:
            print("错误：没有显示的推荐")
            return None

        # 显示推荐信息
        self._display_recommendation()

        # 收集反馈
        while True:
            print("\n请提供反馈:")
            print("1. 接受推荐")
            print("2. 拒绝推荐")
            print("3. 跳过（不提供反馈）")

            try:
                choice = input("请输入选项 (1-3): ").strip()

                if choice == "1":
                    # 接受推荐
                    feedback = self._create_feedback(FeedbackType.ACCEPT)
                    self.on_feedback(feedback)
                    return feedback

                elif choice == "2":
                    # 拒绝推荐，需要原因
                    reason = self._collect_rejection_reason()
                    if reason:
                        feedback = self._create_feedback(FeedbackType.REJECT, reason)
                        self.on_feedback(feedback)
                        return feedback
                    # 用户取消选择原因
                    continue

                elif choice == "3":
                    # 跳过
                    print("已跳过反馈")
                    return None

                else:
                    print("无效选项，请重新输入")

            except (EOFError, KeyboardInterrupt):
                print("\n反馈收集已取消")
                return None

    def _display_recommendation(self):
        """显示推荐信息"""
        info = self.current_recommendation_info or {}

        print("\n" + "=" * 50)
        print("推荐详情")
        print("=" * 50)

        if "name" in info:
            print(f"景点名称: {info['name']}")

        if "city" in info:
            print(f"所在城市: {info['city']}")

        if "category" in info:
            print(f"景点类别: {info['category']}")

        if "price" in info:
            print(f"参考价格: {info['price']}")

        if "description" in info:
            desc = info['description']
            if len(desc) > 100:
                desc = desc[:100] + "..."
            print(f"景点描述: {desc}")

        if "rating" in info:
            print(f"用户评分: {info['rating']}")

        if "distance" in info:
            print(f"距离市中心: {info['distance']}")

        print("=" * 50)

    def _collect_rejection_reason(self) -> Optional[str]:
        """收集拒绝原因"""
        print("\n请选择拒绝原因:")
        reasons = [
            ("1", RejectionReason.TOO_EXPENSIVE.value),
            ("2", RejectionReason.TOO_FAR.value),
            ("3", RejectionReason.ALREADY_VISITED.value),
            ("4", RejectionReason.NOT_INTERESTED.value),
            ("5", RejectionReason.TIME_NOT_SUITABLE.value),
            ("6", RejectionReason.OTHER.value),
            ("7", "取消")
        ]

        for num, reason in reasons:
            print(f"{num}. {reason}")

        while True:
            try:
                choice = input("请输入选项 (1-7): ").strip()

                if choice == "7":
                    return None  # 取消

                if choice in ["1", "2", "3", "4", "5", "6"]:
                    selected_reason = reasons[int(choice) - 1][1]

                    # 如果是"其他原因"，询问具体原因
                    if selected_reason == RejectionReason.OTHER.value:
                        custom_reason = input("请输入具体原因: ").strip()
                        if custom_reason:
                            return custom_reason
                        else:
                            print("原因不能为空")
                            continue

                    return selected_reason

                print("无效选项，请重新输入")

            except (EOFError, KeyboardInterrupt):
                print("\n原因选择已取消")
                return None


class FeedbackManager:
    """反馈管理器"""

    def __init__(self, collector: FeedbackCollector):
        """
        初始化反馈管理器

        Args:
            collector: 反馈收集器实例
        """
        self.collector = collector
        self.feedback_history = []
        self._load_history()

    def show_and_collect(
        self,
        recommendation_id: str,
        recommendation_info: Dict[str, Any]
    ) -> Optional[Feedback]:
        """
        显示推荐并收集反馈

        Args:
            recommendation_id: 推荐ID
            recommendation_info: 推荐信息

        Returns:
            反馈对象，用户取消则为None
        """
        # 显示推荐
        self.collector.show_recommendation(recommendation_id, recommendation_info)

        # 收集反馈
        feedback = self.collector.collect_feedback()

        if feedback:
            # 记录时间戳
            from datetime import datetime
            feedback.timestamp = datetime.now().isoformat()

            # 保存到历史
            self.feedback_history.append(feedback)
            self._save_history()

            # 记录统计
            self._update_statistics(feedback)

        return feedback

    def get_feedback_history(self, limit: int = 50) -> list[Feedback]:
        """
        获取反馈历史

        Args:
            limit: 返回的最大记录数

        Returns:
            反馈历史列表
        """
        return self.feedback_history[-limit:] if self.feedback_history else []

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取反馈统计

        Returns:
            统计信息字典
        """
        total = len(self.feedback_history)
        accepts = sum(1 for f in self.feedback_history
                     if f.feedback_type == FeedbackType.ACCEPT)
        rejects = total - accepts

        # 拒绝原因统计
        rejection_reasons = {}
        for feedback in self.feedback_history:
            if (feedback.feedback_type == FeedbackType.REJECT and
                feedback.reason):
                rejection_reasons[feedback.reason] = (
                    rejection_reasons.get(feedback.reason, 0) + 1
                )

        return {
            "total_feedbacks": total,
            "acceptances": accepts,
            "rejections": rejects,
            "acceptance_rate": accepts / total if total > 0 else 0,
            "rejection_reasons": rejection_reasons,
            "last_feedback_time": (
                self.feedback_history[-1].timestamp if self.feedback_history else None
            )
        }

    def clear_history(self):
        """清空反馈历史"""
        self.feedback_history.clear()
        self._save_history()

    def _load_history(self):
        """加载反馈历史"""
        try:
            import os
            history_file = "feedback_history.json"

            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.feedback_history = [
                        Feedback.from_dict(item) for item in data
                    ]
        except Exception as e:
            print(f"加载反馈历史时出错: {e}")
            self.feedback_history = []

    def _save_history(self):
        """保存反馈历史"""
        try:
            history_file = "feedback_history.json"
            data = [feedback.to_dict() for feedback in self.feedback_history]

            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存反馈历史时出错: {e}")

    def _update_statistics(self, feedback: Feedback):
        """更新统计信息（可扩展）"""
        # 这里可以添加更复杂的统计逻辑
        pass


def create_feedback_collector(interface_type: str = "console", **kwargs) -> FeedbackCollector:
    """
    创建反馈收集器工厂函数

    Args:
        interface_type: 界面类型 ("console", "gui")
        **kwargs: 额外参数

    Returns:
        反馈收集器实例
    """
    def default_callback(feedback: Feedback):
        """默认回调函数"""
        action = "接受" if feedback.feedback_type == FeedbackType.ACCEPT else "拒绝"
        reason_str = f"，原因: {feedback.reason}" if feedback.reason else ""
        print(f"[反馈] 用户{action}了推荐 {feedback.recommendation_id}{reason_str}")

    on_feedback = kwargs.get('on_feedback', default_callback)

    if interface_type == "console":
        return ConsoleFeedbackCollector(on_feedback)
    elif interface_type == "gui":
        # GUI版本需要tkinter，如果不可用则回退到控制台
        try:
            from .ui_feedback_gui import GUIFeedbackCollector
            return GUIFeedbackCollector(on_feedback, **kwargs)
        except ImportError:
            print("警告：tkinter不可用，回退到控制台界面")
            return ConsoleFeedbackCollector(on_feedback)
    else:
        raise ValueError(f"不支持的界面类型: {interface_type}")


# 测试代码
if __name__ == "__main__":
    def test_callback(feedback: Feedback):
        print(f"收到反馈: {feedback.to_dict()}")

    # 创建控制台反馈收集器
    collector = ConsoleFeedbackCollector(test_callback)
    manager = FeedbackManager(collector)

    # 测试推荐
    test_recommendation = {
        "id": "test_rec_001",
        "name": "故宫博物院",
        "city": "北京",
        "category": "历史文化",
        "price": "60元",
        "description": "中国古代宫殿建筑之精华，世界上现存规模最大、保存最为完整的木质结构古建筑之一。",
        "rating": 4.8,
        "distance": "市中心2公里"
    }

    print("开始测试反馈收集...")
    feedback = manager.show_and_collect(
        recommendation_id=test_recommendation["id"],
        recommendation_info=test_recommendation
    )

    if feedback:
        print(f"收集到反馈: {feedback.feedback_type.value}")
        if feedback.reason:
            print(f"拒绝原因: {feedback.reason}")

        # 显示统计
        stats = manager.get_statistics()
        print(f"\n反馈统计:")
        print(f"总反馈数: {stats['total_feedbacks']}")
        print(f"接受数: {stats['acceptances']}")
        print(f"拒绝数: {stats['rejections']}")
        print(f"接受率: {stats['acceptance_rate']:.1%}")
    else:
        print("用户未提供反馈")