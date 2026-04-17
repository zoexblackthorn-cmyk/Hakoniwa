from typing import List, Dict, Any
import requests

from services.settings import settings_service


class SearchService:
    """搜索服务 - 目前支持 Brave Search"""

    def search(self, query: str) -> List[Dict[str, str]]:
        cfg = settings_service.settings.api.search
        if not cfg.api_key:
            raise ValueError("请先在设置中配置 Search API Key")

        provider = (cfg.provider or "brave").lower()
        if provider == "brave":
            return self._search_brave(query)
        else:
            raise ValueError(f"不支持的 Search Provider: {provider}")

    def _search_brave(self, query: str) -> List[Dict[str, str]]:
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "X-Subscription-Token": settings_service.settings.api.search.api_key,
            "Accept": "application/json",
        }
        params = {
            "q": query,
            "count": 10,
        }
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
            })
        return results


# 单例
search_service = SearchService()
