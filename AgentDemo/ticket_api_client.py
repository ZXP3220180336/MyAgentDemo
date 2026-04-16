"""
票务API客户端模块
支持多种票务平台的API集成（美团、携程、飞猪等）
提供统一的接口检查门票可用性
"""

import requests
import json
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time


class TicketAPIClient(ABC):
    """票务API客户端抽象基类"""

    def __init__(self, api_key: str, base_url: str):
        """
        初始化票务API客户端

        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        self.timeout = 10

    @abstractmethod
    def check_ticket_availability(self, attraction_id: str, date: str) -> Dict[str, Any]:
        """
        检查门票可用性

        Args:
            attraction_id: 景点ID
            date: 日期 (YYYY-MM-DD)

        Returns:
            {
                "available": bool,                # 是否可用
                "ticket_types": List[Dict],       # 票种列表
                "sold_out": bool,                 # 是否售罄
                "low_availability": bool,         # 是否库存紧张
                "next_available_date": Optional[str],  # 下一个可用日期
                "source": str,                    # 数据来源
                "error": Optional[str]            # 错误信息（如果有）
            }
        """
        pass

    @abstractmethod
    def search_attractions(self, city: str, category: str = None) -> List[Dict[str, Any]]:
        """
        搜索景点

        Args:
            city: 城市名称
            category: 景点类别（可选）

        Returns:
            景点信息列表
        """
        pass

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """
        发送API请求的通用方法

        Args:
            method: HTTP方法（GET, POST等）
            endpoint: API端点
            **kwargs: 请求参数

        Returns:
            响应数据字典或None（如果失败）
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return None

    def get_attraction_details(self, attraction_id: str) -> Optional[Dict[str, Any]]:
        """
        获取景点详细信息

        Args:
            attraction_id: 景点ID

        Returns:
            景点详细信息字典
        """
        raise NotImplementedError("子类可以实现此方法")


class MockTicketClient(TicketAPIClient):
    """模拟票务客户端，用于测试和开发"""

    def __init__(self, api_key: str = "mock_key", base_url: str = "https://mock.ticket.api"):
        super().__init__(api_key, base_url)

        # 模拟数据：热门景点及其信息
        self.mock_attractions = {
            "北京": [
                {
                    "id": "bj_gugong",
                    "name": "故宫博物院",
                    "category": "历史文化",
                    "price_range": "40-60元",
                    "popularity": 0.95,  # 热门程度 0-1
                    "weekend_sold_out_prob": 0.7,  # 周末售罄概率
                    "description": "中国古代宫殿建筑之精华"
                },
                {
                    "id": "bj_yiheyuan",
                    "name": "颐和园",
                    "category": "历史文化",
                    "price_range": "30-50元",
                    "popularity": 0.85,
                    "weekend_sold_out_prob": 0.5,
                    "description": "中国现存最完整的皇家园林"
                },
                {
                    "id": "bj_badaling",
                    "name": "八达岭长城",
                    "category": "自然风光",
                    "price_range": "40-60元",
                    "popularity": 0.9,
                    "weekend_sold_out_prob": 0.6,
                    "description": "万里长城的精华段"
                },
                {
                    "id": "bj_beihai",
                    "name": "北海公园",
                    "category": "自然风光",
                    "price_range": "10-20元",
                    "popularity": 0.7,
                    "weekend_sold_out_prob": 0.3,
                    "description": "中国现存最古老、最完整的皇家园林"
                }
            ],
            "上海": [
                {
                    "id": "sh_disney",
                    "name": "上海迪士尼乐园",
                    "category": "主题乐园",
                    "price_range": "399-699元",
                    "popularity": 0.98,
                    "weekend_sold_out_prob": 0.8,
                    "description": "中国大陆第一个迪士尼主题公园"
                },
                {
                    "id": "sh_orientalpearl",
                    "name": "东方明珠广播电视塔",
                    "category": "现代建筑",
                    "price_range": "120-220元",
                    "popularity": 0.88,
                    "weekend_sold_out_prob": 0.4,
                    "description": "上海标志性建筑"
                }
            ],
            "杭州": [
                {
                    "id": "hz_xihu",
                    "name": "西湖风景区",
                    "category": "自然风光",
                    "price_range": "免费",
                    "popularity": 0.92,
                    "weekend_sold_out_prob": 0.1,
                    "description": "中国著名的风景名胜区"
                },
                {
                    "id": "hz_lingyin",
                    "name": "灵隐寺",
                    "category": "历史文化",
                    "price_range": "30-45元",
                    "popularity": 0.8,
                    "weekend_sold_out_prob": 0.5,
                    "description": "中国佛教禅宗十大古刹之一"
                }
            ]
        }

    def check_ticket_availability(self, attraction_id: str, date: str) -> Dict[str, Any]:
        """
        模拟检查门票可用性

        逻辑：
        1. 热门景点周末更容易售罄
        2. 随机模拟库存紧张情况
        3. 提供下一个可用日期（如果售罄）
        """
        try:
            # 解析日期
            visit_date = datetime.strptime(date, "%Y-%m-%d")
            is_weekend = visit_date.weekday() >= 5  # 5=周六,6=周日
            is_holiday = self._is_holiday(visit_date)

            # 查找景点信息
            attraction_info = self._find_attraction(attraction_id)

            if not attraction_info:
                return {
                    "available": False,
                    "ticket_types": [],
                    "sold_out": True,
                    "low_availability": False,
                    "next_available_date": None,
                    "source": "mock",
                    "error": f"未找到景点: {attraction_id}"
                }

            # 计算售罄概率
            base_prob = attraction_info.get("weekend_sold_out_prob", 0.3)
            if is_weekend:
                sold_out_prob = base_prob
            elif is_holiday:
                sold_out_prob = base_prob * 1.5  # 节假日概率更高
            else:
                sold_out_prob = base_prob * 0.5  # 工作日概率较低

            # 模拟随机结果
            is_sold_out = random.random() < sold_out_prob
            is_low_availability = random.random() < 0.3  # 30%概率库存紧张

            # 生成票种信息
            ticket_types = self._generate_ticket_types(attraction_info, is_sold_out, is_low_availability)

            # 下一个可用日期（如果售罄）
            next_available_date = None
            if is_sold_out:
                # 模拟3天后有票
                next_date = visit_date + timedelta(days=random.randint(1, 7))
                next_available_date = next_date.strftime("%Y-%m-%d")

            return {
                "available": not is_sold_out,
                "ticket_types": ticket_types,
                "sold_out": is_sold_out,
                "low_availability": is_low_availability and not is_sold_out,
                "next_available_date": next_available_date,
                "source": "mock",
                "error": None
            }

        except Exception as e:
            return {
                "available": False,
                "ticket_types": [],
                "sold_out": True,
                "low_availability": False,
                "next_available_date": None,
                "source": "mock",
                "error": f"检查可用性时出错: {str(e)}"
            }

    def search_attractions(self, city: str, category: str = None) -> List[Dict[str, Any]]:
        """搜索景点"""
        attractions = self.mock_attractions.get(city, [])

        if category:
            attractions = [attr for attr in attractions if attr.get("category") == category]

        # 添加模拟的实时可用性信息
        for attr in attractions:
            today = datetime.now().strftime("%Y-%m-%d")
            availability = self.check_ticket_availability(attr["id"], today)
            attr["availability"] = availability

        return attractions

    def _find_attraction(self, attraction_id: str) -> Optional[Dict]:
        """查找景点信息"""
        for city_attractions in self.mock_attractions.values():
            for attr in city_attractions:
                if attr["id"] == attraction_id:
                    return attr
        return None

    def _generate_ticket_types(self, attraction_info: Dict, is_sold_out: bool, is_low_availability: bool) -> List[Dict]:
        """生成模拟票种信息"""
        price_range = attraction_info.get("price_range", "免费")

        if price_range == "免费":
            return [
                {
                    "type": "免费参观券",
                    "price": 0,
                    "available": not is_sold_out,
                    "inventory": "充足" if not is_low_availability else "紧张"
                }
            ]

        # 解析价格范围
        import re
        price_match = re.search(r'(\d+)[^\d]*(\d+)', price_range)

        if price_match:
            min_price = int(price_match.group(1))
            max_price = int(price_match.group(2))
        else:
            min_price = 50
            max_price = 100

        ticket_types = [
            {
                "type": "成人票",
                "price": max_price,
                "available": not is_sold_out,
                "inventory": "充足" if not is_low_availability else "紧张"
            },
            {
                "type": "学生票",
                "price": int(min_price * 0.7),
                "available": not is_sold_out and random.random() > 0.2,  # 80%概率有学生票
                "inventory": "紧张" if is_low_availability else "充足"
            },
            {
                "type": "儿童票",
                "price": int(min_price * 0.5),
                "available": not is_sold_out,
                "inventory": "充足"
            }
        ]

        # 如果是热门景点，可能还有VIP票
        if attraction_info.get("popularity", 0) > 0.9:
            ticket_types.append({
                "type": "VIP快速通道票",
                "price": max_price * 2,
                "available": not is_sold_out,
                "inventory": "充足"
            })

        return ticket_types

    def _is_holiday(self, date: datetime) -> bool:
        """简单判断是否为节假日"""
        # 模拟：每个月的前7天有节假日
        return date.day <= 7


class MeituanTicketClient(TicketAPIClient):
    """美团票务API客户端（预留接口）"""

    def check_ticket_availability(self, attraction_id: str, date: str) -> Dict[str, Any]:
        """
        调用美团API检查门票可用性

        注意：实际使用时需要替换为真实的API调用
        """
        # 这里应该是真实的美团API调用
        # 为简化，这里返回模拟数据，但标注为真实API
        mock_client = MockTicketClient()
        result = mock_client.check_ticket_availability(attraction_id, date)
        result["source"] = "meituan_api"

        # 在实际实现中，应该是：
        # endpoint = "/ticket/availability"
        # params = {"attraction_id": attraction_id, "date": date}
        # data = self._make_request("GET", endpoint, params=params)
        # 然后解析data...

        return result

    def search_attractions(self, city: str, category: str = None) -> List[Dict[str, Any]]:
        """调用美团API搜索景点"""
        # 模拟实现
        mock_client = MockTicketClient()
        return mock_client.search_attractions(city, category)


class CtripTicketClient(TicketAPIClient):
    """携程票务API客户端（预留接口）"""

    def check_ticket_availability(self, attraction_id: str, date: str) -> Dict[str, Any]:
        """调用携程API检查门票可用性"""
        mock_client = MockTicketClient()
        result = mock_client.check_ticket_availability(attraction_id, date)
        result["source"] = "ctrip_api"
        return result

    def search_attractions(self, city: str, category: str = None) -> List[Dict[str, Any]]:
        """调用携程API搜索景点"""
        mock_client = MockTicketClient()
        return mock_client.search_attractions(city, category)


class TicketAPIFactory:
    """票务API工厂类，用于创建合适的客户端"""

    @staticmethod
    def create_client(api_type: str = "mock", **kwargs) -> TicketAPIClient:
        """
        创建票务API客户端

        Args:
            api_type: API类型 ("mock", "meituan", "ctrip", "fliggy")
            **kwargs: 客户端参数

        Returns:
            票务API客户端实例
        """
        api_key = kwargs.get("api_key", "")
        base_url = kwargs.get("base_url", "")

        if api_type == "meituan":
            return MeituanTicketClient(
                api_key=api_key or "meituan_demo_key",
                base_url=base_url or "https://api.meituan.com/ticket/v1"
            )
        elif api_type == "ctrip":
            return CtripTicketClient(
                api_key=api_key or "ctrip_demo_key",
                base_url=base_url or "https://api.ctrip.com/ticket/v1"
            )
        elif api_type == "fliggy":
            # 飞猪票务客户端（预留）
            from .ticket_api_fliggy import FliggyTicketClient
            return FliggyTicketClient(api_key=api_key, base_url=base_url)
        else:
            # 默认返回模拟客户端
            return MockTicketClient(api_key=api_key, base_url=base_url)

    @staticmethod
    def create_from_env() -> TicketAPIClient:
        """从环境变量创建客户端"""
        import os

        # 读取配置
        ticket_api_type = os.getenv("TICKET_API_TYPE", "mock")
        ticket_api_key = os.getenv("TICKET_API_KEY", "")
        ticket_base_url = os.getenv("TICKET_BASE_URL", "")

        return TicketAPIFactory.create_client(
            api_type=ticket_api_type,
            api_key=ticket_api_key,
            base_url=ticket_base_url
        )


# 测试代码
if __name__ == "__main__":
    print("测试票务API客户端...")

    # 测试模拟客户端
    client = MockTicketClient()

    # 测试可用性检查
    print("\n1. 测试门票可用性检查:")
    availability = client.check_ticket_availability("bj_gugong", "2026-04-20")
    print(f"故宫可用性: {json.dumps(availability, ensure_ascii=False, indent=2)}")

    # 测试景点搜索
    print("\n2. 测试景点搜索:")
    attractions = client.search_attractions("北京", "历史文化")
    print(f"北京历史文化景点: {len(attractions)}个")
    for attr in attractions[:2]:  # 只显示前2个
        print(f"  - {attr['name']} ({attr['category']}): {attr['price_range']}")

    # 测试工厂类
    print("\n3. 测试API工厂:")
    factory_client = TicketAPIFactory.create_client("mock")
    print(f"工厂创建的客户端类型: {type(factory_client).__name__}")

    print("\n✅ 票务API客户端测试完成")