"""
用户认证管理系统
处理用户注册、登录、会话管理等功能
"""

import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class AuthManager:
    """用户认证管理器"""

    def __init__(self, users_file="users.json", sessions_file="sessions.json"):
        """
        初始化认证管理器

        Args:
            users_file: 用户数据文件路径
            sessions_file: 会话数据文件路径
        """
        self.users_file = users_file
        self.sessions_file = sessions_file
        self.users = {}
        self.sessions = {}
        self._load_data()

    def _load_data(self):
        """加载用户和会话数据"""
        # 用户数据：{username: {password_hash, email, created_at, ...}}
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.users = {}
        else:
            self.users = {}

        # 会话数据：{session_token: {username, created_at, expires_at}}
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.sessions = {}
        else:
            self.sessions = {}

    def _save_data(self):
        """保存数据到文件"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)

            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"警告：保存认证数据时出错: {e}")

    def register_user(self, username: str, password: str, email: str = None) -> bool:
        """
        注册新用户

        Args:
            username: 用户名
            password: 密码
            email: 邮箱（可选）

        Returns:
            注册是否成功
        """
        # 验证输入
        if not username or not password:
            return False

        if username in self.users:
            return False

        if len(password) < 6:
            return False

        # 密码哈希
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()

        # 创建用户记录
        self.users[username] = {
            "password_hash": password_hash,
            "salt": salt,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "preferences": {}  # 用户偏好初始化为空
        }

        # 保存数据
        self._save_data()
        return True

    def login_user(self, username: str, password: str) -> Optional[str]:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            成功返回session_token，失败返回None
        """
        if username not in self.users:
            return None

        user_data = self.users[username]

        # 验证密码
        password_hash = hashlib.sha256((password + user_data["salt"]).encode()).hexdigest()

        if password_hash != user_data["password_hash"]:
            return None

        # 创建会话
        session_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()

        self.sessions[session_token] = {
            "username": username,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at
        }

        # 更新用户最后登录时间
        self.users[username]["last_login"] = datetime.now().isoformat()
        self._save_data()

        return session_token

    def validate_session(self, session_token: str) -> Optional[str]:
        """
        验证会话

        Args:
            session_token: 会话令牌

        Returns:
            有效返回用户名，无效返回None
        """
        if session_token not in self.sessions:
            return None

        session_data = self.sessions[session_token]

        try:
            expires_at = datetime.fromisoformat(session_data["expires_at"])
        except ValueError:
            # 日期格式错误，删除无效会话
            del self.sessions[session_token]
            self._save_data()
            return None

        if datetime.now() > expires_at:
            # 会话过期，删除
            del self.sessions[session_token]
            self._save_data()
            return None

        return session_data["username"]

    def logout_user(self, session_token: str) -> bool:
        """
        用户登出

        Args:
            session_token: 会话令牌

        Returns:
            登出是否成功
        """
        if session_token in self.sessions:
            del self.sessions[session_token]
            self._save_data()
            return True
        return False

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """
        获取用户信息

        Args:
            username: 用户名

        Returns:
            用户信息字典，用户不存在返回None
        """
        if username in self.users:
            return self.users[username].copy()
        return None

    def update_user_preferences(self, username: str, preferences: Dict[str, Any]) -> bool:
        """
        更新用户偏好

        Args:
            username: 用户名
            preferences: 偏好字典

        Returns:
            更新是否成功
        """
        if username not in self.users:
            return False

        # 更新偏好
        if "preferences" not in self.users[username]:
            self.users[username]["preferences"] = {}

        self.users[username]["preferences"].update(preferences)
        self._save_data()
        return True

    def delete_user(self, username: str, password: str) -> bool:
        """
        删除用户

        Args:
            username: 用户名
            password: 密码（用于确认）

        Returns:
            删除是否成功
        """
        if username not in self.users:
            return False

        # 验证密码
        user_data = self.users[username]
        password_hash = hashlib.sha256((password + user_data["salt"]).encode()).hexdigest()

        if password_hash != user_data["password_hash"]:
            return False

        # 删除用户
        del self.users[username]

        # 删除用户的所有会话
        sessions_to_delete = []
        for token, session_data in self.sessions.items():
            if session_data.get("username") == username:
                sessions_to_delete.append(token)

        for token in sessions_to_delete:
            del self.sessions[token]

        self._save_data()
        return True

    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有用户信息（不含敏感信息）

        Returns:
            用户信息字典
        """
        safe_users = {}
        for username, user_data in self.users.items():
            safe_users[username] = {
                "email": user_data.get("email"),
                "created_at": user_data.get("created_at"),
                "last_login": user_data.get("last_login"),
                "has_preferences": "preferences" in user_data and bool(user_data["preferences"])
            }
        return safe_users


def create_test_users(auth_manager: AuthManager):
    """
    创建测试用户（仅用于开发测试）

    Args:
        auth_manager: 认证管理器实例
    """
    test_users = [
        ("test_user", "password123", "test@example.com"),
        ("demo_user", "demo123", "demo@example.com"),
        ("admin", "admin123", "admin@example.com")
    ]

    for username, password, email in test_users:
        if username not in auth_manager.users:
            auth_manager.register_user(username, password, email)
            print(f"创建测试用户: {username}")


if __name__ == "__main__":
    # 测试代码
    auth = AuthManager()
    create_test_users(auth)

    # 测试登录
    token = auth.login_user("test_user", "password123")
    if token:
        print(f"登录成功，会话令牌: {token[:20]}...")

        # 验证会话
        username = auth.validate_session(token)
        print(f"会话验证: {username}")

        # 登出
        auth.logout_user(token)
        print("已登出")
    else:
        print("登录失败")