import requests
import re
from datetime import datetime
from app.config import SERP_API_KEY

def extract_year(topic: str) -> int:
    match = re.search(r'\b(20\d{2})\b', topic)
    if match:
        return int(match.group(1))
    return datetime.now().year  

def search(query: str, num_results: int = 10) -> list:
    url = "https://serpapi.com/search"
    params = {
        "api_key": SERP_API_KEY,
        "q": query,
        "num": num_results,
        "hl": "vi",
        "gl": "vn",
        "engine": "google"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "organic_results" not in data:
            return []
        return [
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            }
            for item in data["organic_results"]
        ]
    except Exception as e:
        print(f"Search Agent lỗi: {e}")
        return []

def search_market(topic: str) -> dict:
    year = extract_year(topic) 
    
    results = {}
    results["overview"] = search(f"{topic} tổng quan thị trường")
    results["trends"] = search(f"{topic} xu hướng {year}")
    results["competitors"] = search(f"{topic} doanh nghiệp thương hiệu lớn {year}")
    return results