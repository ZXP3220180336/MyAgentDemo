"""
用户状态管理系统
管理用户偏好、交互历史、拒绝统计和学习到的偏好
与AuthManager协同工作，提供完整的用户状态管理
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import hashlib


class UserStateManager:
    """用户状态管理器"""

    def __init__(self, storage_dir: str = "user_states"):
        """
        初始化用户状态管理器

        Args:
            storage_dir: 状态存储目录
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def get_user_state(self, username: str) -> Dict[str, Any]:
        """
        获取用户状态，如果不存在则创建默认状态

        Args:
            username: 用户名

        Returns:
            用户状态字典
        """
        file_path = self._get_state_file_path(username)

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)

                # 确保状态包含所有必需字段
                state = self._ensure_state_structure(state, username)
                return state
            except (json.JSONDecodeError, IOError) as e:
                print(f"警告：加载用户状态失败 ({username})，创建新状态: {e}")
                return self._create_default_state(username)
        else:
            return self._create_default_state(username)

    def save_user_state(self, username: str, state: Dict[str, Any]):
        """
        保存用户状态

        Args:
            username: 用户名
            state: 用户状态字典
        """
        file_path = self._get_state_file_path(username)

        # 添加/更新元数据
        state["username"] = username
        state["updated_at"] = datetime.now().isoformat()

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"错误：保存用户状态失败 ({username}): {e}")

    def extract_preferences_from_text(self, text: str) -> Dict[str, Any]:
        """
        从用户输入文本中提取偏好信息

        Args:
            text: 用户输入文本

        Returns:
            提取的偏好字典
        """
        preferences = {
            "category_preferences": {},
            "budget_range": None,
            "explicit_preferences": {},
            "extracted_keywords": []
        }

        text_lower = text.lower()

        # 1. 提取预算信息
        budget_patterns = [
            (r'预算(?:大约|大概|左右)?\s*(\d+)[元块]', 'budget_exact'),
            (r'(\d+)[元块](?:左右|以内|以下)?\s*的?预算', 'budget_exact'),
            (r'价格(?:在|不要超过|不超过)\s*(\d+)[元块]', 'budget_max'),
            (r'(\d+)[\-~]\s*(\d+)[元块]', 'budget_range'),
            (r'便宜\s*点', 'budget_cheap'),
            (r'经济\s*实惠', 'budget_economical'),
            (r'高端|豪华', 'budget_luxury')
        ]

        for pattern, budget_type in budget_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                if budget_type == 'budget_range' and len(matches[0]) == 2:
                    min_val, max_val = matches[0]
                    preferences["budget_range"] = f"{min_val}-{max_val}元"
                    preferences["extracted_keywords"].append(f"预算{min_val}-{max_val}元")
                elif budget_type in ['budget_exact', 'budget_max']:
                    amount = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    if budget_type == 'budget_max':
                        preferences["budget_range"] = f"0-{amount}元"
                    else:
                        preferences["budget_range"] = f"{amount}元左右"
                    preferences["extracted_keywords"].append(f"预算{amount}元")
                elif budget_type == 'budget_cheap':
                    preferences["budget_range"] = "经济型"
                    preferences["extracted_keywords"].append("便宜")
                elif budget_type == 'budget_economical':
                    preferences["budget_range"] = "经济实惠"
                    preferences["extracted_keywords"].append("经济实惠")
                elif budget_type == 'budget_luxury':
                    preferences["budget_range"] = "高端豪华"
                    preferences["extracted_keywords"].append("高端")
                break

        # 2. 提取兴趣类别偏好
        category_keywords = {
            "历史文化": ["历史", "文化", "古迹", "博物馆", "遗址", "文物", "古建筑", "庙宇", "寺庙"],
            "自然风光": ["自然", "风景", "山水", "公园", "花园", "湖泊", "山川", "海滩", "森林"],
            "主题乐园": ["乐园", "游乐", "娱乐", "主题公园", "游乐园", "儿童", "亲子"],
            "美食购物": ["美食", "购物", "小吃", "特产", "商业街", "夜市", "餐馆", "餐厅"],
            "现代建筑": ["现代", "建筑", "高楼", "大厦", "地标", "现代艺术", "展览馆"],
            "休闲度假": ["休闲", "度假", "温泉", "spa", "放松", "度假村"],
            "户外运动": ["户外", "运动", "爬山", "徒步", "骑行", "探险"]
        }

        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # 更新类别偏好分数 (0-1)
                    if category not in preferences["category_preferences"]:
                        preferences["category_preferences"][category] = 0.5
                    else:
                        preferences["category_preferences"][category] = min(
                            1.0, preferences["category_preferences"][category] + 0.2
                        )

                    if keyword not in preferences["extracted_keywords"]:
                        preferences["extracted_keywords"].append(keyword)

        # 3. 提取其他偏好
        other_preferences = {
            "人少": ["人少", "安静", "清静", "不拥挤"],
            "交通方便": ["交通方便", "交通便利", "地铁", "公交", "方便到达"],
            "适合拍照": ["拍照", "摄影", "风景美", "好看"],
            "适合家庭": ["家庭", "亲子", "带孩子", "小孩", "儿童"],
            "适合情侣": ["情侣", "约会", "浪漫", "两人"],
            "有讲解": ["讲解", "导游", "解说", "导览"]
        }

        for pref_key, pref_keywords in other_preferences.items():
            for keyword in pref_keywords:
                if keyword in text_lower:
                    preferences["explicit_preferences"][pref_key] = True
                    if keyword not in preferences["extracted_keywords"]:
                        preferences["extracted_keywords"].append(keyword)

        # 4. 提取时间偏好
        time_keywords = {
            "上午": ["早上", "上午", "早晨"],
            "下午": ["下午", "午后"],
            "晚上": ["晚上", "傍晚", "夜晚", "夜景"],
            "全天": ["全天", "一整天"]
        }

        for time_key, time_words in time_keywords.items():
            for word in time_words:
                if word in text_lower:
                    preferences["explicit_preferences"]["preferred_time"] = time_key
                    break

        # 5. 提取距离偏好
        if "附近" in text_lower or "不远" in text_lower or "就近" in text_lower:
            preferences["explicit_preferences"]["prefer_nearby"] = True
            preferences["extracted_keywords"].append("附近")

        if "远一点" in text_lower or "远处" in text_lower:
            preferences["explicit_preferences"]["prefer_far"] = True
            preferences["extracted_keywords"].append("远处")

        return preferences

    def update_user_preferences(self, username: str, new_preferences: Dict[str, Any]):
        """
        更新用户偏好（合并而不是替换）

        Args:
            username: 用户名
            new_preferences: 新的偏好信息
        """
        state = self.get_user_state(username)

        # 合并类别偏好
        if "category_preferences" in new_preferences:
            current_categories = state["preferences"].get("category_preferences", {})
            new_categories = new_preferences["category_preferences"]

            for category, score in new_categories.items():
                if category in current_categories:
                    # 加权平均：旧分数权重0.7，新分数权重0.3
                    current_categories[category] = current_categories[category] * 0.7 + score * 0.3
                else:
                    current_categories[category] = score

            state["preferences"]["category_preferences"] = current_categories

        # 更新其他偏好
        if "budget_range" in new_preferences and new_preferences["budget_range"]:
            state["preferences"]["budget_range"] = new_preferences["budget_range"]

        if "explicit_preferences" in new_preferences:
            current_explicit = state["preferences"].get("explicit_preferences", {})
            current_explicit.update(new_preferences["explicit_preferences"])
            state["preferences"]["explicit_preferences"] = current_explicit

        # 记录提取时间
        state["preferences"]["last_extracted"] = datetime.now().isoformat()

        # 保存更新后的状态
        self.save_user_state(username, state)

    def record_interaction(self, username: str, interaction_type: str, data: Dict[str, Any], state: Dict[str, Any] = None):
        """
        记录用户交互

        Args:
            username: 用户名
            interaction_type: 交互类型 ("query", "recommendation_view", "feedback")
            data: 交互数据
            state: 可选的状态字典。如果提供，将修改此字典并保存；否则加载状态。
        """
        if state is None:
            state = self.get_user_state(username)

        interaction = {
            "type": interaction_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        # 添加到交互历史
        state["interaction_history"].append(interaction)

        # 限制历史记录数量（保留最近100条）
        if len(state["interaction_history"]) > 100:
            state["interaction_history"] = state["interaction_history"][-100:]

        self.save_user_state(username, state)

    def record_feedback(self, username: str, feedback_type: str, recommendation: Dict[str, Any], reason: str = None):
        """
        记录用户反馈

        Args:
            username: 用户名
            feedback_type: 反馈类型 ("accept", "reject")
            recommendation: 推荐信息
            reason: 拒绝原因（可选）
        """
        state = self.get_user_state(username)

        # 更新统计信息
        if feedback_type == "accept":
            state["acceptance_stats"]["total"] += 1
            state["acceptance_stats"]["recent_acceptances"].append({
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat()
            })
            # 只保留最近10个接受记录
            if len(state["acceptance_stats"]["recent_acceptances"]) > 10:
                state["acceptance_stats"]["recent_acceptances"] = state["acceptance_stats"]["recent_acceptances"][-10:]

            # 重置连续拒绝计数
            state["rejection_stats"]["consecutive"] = 0

        elif feedback_type == "reject":
            state["rejection_stats"]["total"] += 1
            state["rejection_stats"]["consecutive"] += 1
            state["rejection_stats"]["last_rejection_time"] = datetime.now().isoformat()

            # 按原因统计
            if reason:
                if reason not in state["rejection_stats"]:
                    state["rejection_stats"][reason] = 0
                state["rejection_stats"][reason] += 1

        # 记录交互
        self.record_interaction(
            username,
            "feedback",
            {
                "feedback_type": feedback_type,
                "recommendation": recommendation,
                "reason": reason,
                "consecutive_rejections": state["rejection_stats"]["consecutive"]
            },
            state  # 传递当前状态对象
        )

        # 检查是否需要策略调整
        if (feedback_type == "reject" and
            state["rejection_stats"]["consecutive"] >= 3):
            self._trigger_strategy_adjustment(username, state)

        self.save_user_state(username, state)

    def get_user_insights(self, username: str) -> Dict[str, Any]:
        """
        获取用户行为洞察

        Args:
            username: 用户名

        Returns:
            用户洞察字典
        """
        state = self.get_user_state(username)

        insights = {
            "preference_strength": {},
            "rejection_patterns": {},
            "recommendation_success_rate": 0,
            "active_time_periods": [],
            "preferred_categories": []
        }

        # 分析偏好强度
        category_prefs = state["preferences"].get("category_preferences", {})
        if category_prefs:
            insights["preferred_categories"] = sorted(
                category_prefs.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]  # 取前3个

        # 计算推荐成功率
        total_feedback = state["acceptance_stats"]["total"] + state["rejection_stats"]["total"]
        if total_feedback > 0:
            insights["recommendation_success_rate"] = (
                state["acceptance_stats"]["total"] / total_feedback
            )

        # 分析拒绝模式
        rejection_stats = state["rejection_stats"]
        if rejection_stats["total"] > 0:
            # 找出主要拒绝原因
            reason_counts = {k: v for k, v in rejection_stats.items()
                           if k not in ["total", "consecutive", "last_rejection_time"]}
            if reason_counts:
                main_reason = max(reason_counts.items(), key=lambda x: x[1])
                insights["rejection_patterns"]["main_reason"] = main_reason

        # 分析活跃时间段（简化）
        # 实际实现中应该分析interaction_history的时间戳

        return insights

    def _trigger_strategy_adjustment(self, username: str, state: Dict[str, Any]):
        """
        触发策略调整（当连续拒绝3次时）
        """
        print(f"[警告] 用户 {username} 连续拒绝了3个推荐，正在调整推荐策略...")

        # 分析拒绝模式
        recent_rejections = [
            interaction for interaction in state["interaction_history"][-10:]
            if (interaction.get("type") == "feedback" and
                interaction.get("data", {}).get("feedback_type") == "reject")
        ][-3:]  # 最近3次拒绝

        adjustment = {
            "triggered_at": datetime.now().isoformat(),
            "consecutive_rejections": state["rejection_stats"]["consecutive"],
            "adjustments": []
        }

        # 分析拒绝原因并制定调整策略
        reasons = []
        for rejection in recent_rejections:
            reason = rejection.get("data", {}).get("reason")
            if reason:
                reasons.append(reason)

        from collections import Counter
        reason_counter = Counter(reasons)

        if reason_counter:
            most_common_reason = reason_counter.most_common(1)[0][0]

            if most_common_reason == "价格太高":
                adjustment["adjustments"].append({
                    "type": "budget_adjustment",
                    "description": "降低预算范围或推荐更经济的选项",
                    "action": "apply_lower_budget_filter"
                })
            elif most_common_reason == "距离太远":
                adjustment["adjustments"].append({
                    "type": "location_adjustment",
                    "description": "优先推荐距离更近的景点",
                    "action": "prioritize_nearby_attractions"
                })
            elif most_common_reason == "不感兴趣":
                adjustment["adjustments"].append({
                    "type": "category_adjustment",
                    "description": "尝试不同的景点类别",
                    "action": "explore_new_categories"
                })
            elif most_common_reason == "已经去过":
                adjustment["adjustments"].append({
                    "type": "novelty_adjustment",
                    "description": "推荐用户可能没去过的新景点",
                    "action": "prioritize_new_attractions"
                })

        # 记录调整策略
        if "strategy_adjustments" not in state:
            state["strategy_adjustments"] = []

        state["strategy_adjustments"].append(adjustment)

        # 限制调整记录数量
        if len(state["strategy_adjustments"]) > 10:
            state["strategy_adjustments"] = state["strategy_adjustments"][-10:]

        print(f"[调整] 策略调整完成: {adjustment}")

    def _get_state_file_path(self, username: str) -> str:
        """获取状态文件路径"""
        # 使用用户名哈希作为文件名，避免特殊字符问题
        username_hash = hashlib.md5(username.encode('utf-8')).hexdigest()[:16]
        return os.path.join(self.storage_dir, f"{username_hash}.json")

    def _create_default_state(self, username: str) -> Dict[str, Any]:
        """创建默认用户状态"""
        return {
            "username": username,
            "preferences": {
                "category_preferences": {},
                "budget_range": None,
                "explicit_preferences": {},
                "last_extracted": None
            },
            "interaction_history": [],
            "rejection_stats": {
                "total": 0,
                "consecutive": 0,
                "last_rejection_time": None
            },
            "acceptance_stats": {
                "total": 0,
                "recent_acceptances": []
            },
            "strategy_adjustments": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def _ensure_state_structure(self, state: Dict[str, Any], username: str) -> Dict[str, Any]:
        """确保状态字典包含所有必需字段"""
        default_state = self._create_default_state(username)

        # 递归合并，确保所有字段都存在
        def merge_dicts(dest, src):
            for key, value in src.items():
                if key not in dest:
                    dest[key] = value
                elif isinstance(value, dict) and isinstance(dest[key], dict):
                    merge_dicts(dest[key], value)
            return dest

        return merge_dicts(state.copy(), default_state)


# 测试代码
if __name__ == "__main__":
    print("测试用户状态管理器...")

    manager = UserStateManager()

    # 测试1: 创建和获取用户状态
    print("\n1. 测试用户状态创建:")
    test_user = "test_user_001"
    state = manager.get_user_state(test_user)
    print(f"用户状态创建成功: {state.get('username')}")
    print(f"创建时间: {state.get('created_at')}")

    # 测试2: 偏好提取
    print("\n2. 测试偏好提取:")
    test_text = "我想去北京玩，预算500元左右，喜欢历史文化和自然风光，希望交通方便点"
    preferences = manager.extract_preferences_from_text(test_text)
    print(f"提取的偏好: {preferences}")

    # 测试3: 更新用户偏好
    print("\n3. 测试偏好更新:")
    manager.update_user_preferences(test_user, preferences)
    updated_state = manager.get_user_state(test_user)
    print(f"更新后的偏好: {updated_state['preferences']}")

    # 测试4: 记录交互和反馈
    print("\n4. 测试交互记录:")
    recommendation = {"id": "test_rec_001", "name": "故宫博物院", "category": "历史文化"}

    manager.record_interaction(test_user, "query", {"query": "北京景点推荐"})
    manager.record_feedback(test_user, "reject", recommendation, "价格太高")
    manager.record_feedback(test_user, "reject", recommendation, "距离太远")
    manager.record_feedback(test_user, "reject", recommendation, "不感兴趣")

    final_state = manager.get_user_state(test_user)
    print(f"拒绝总数: {final_state['rejection_stats']['total']}")
    print(f"连续拒绝次数: {final_state['rejection_stats']['consecutive']}")

    # 测试5: 获取用户洞察
    print("\n5. 测试用户洞察:")
    insights = manager.get_user_insights(test_user)
    print(f"用户洞察: {insights}")

    print("\n[完成] 用户状态管理器测试完成")