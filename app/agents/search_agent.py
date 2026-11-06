import asyncio
import re
from datetime import datetime
import httpx
import os
import json
import hashlib
import time
from bs4 import BeautifulSoup
import html2text
from app.config import SERP_API_KEY, MAX_TOKEN_LIMIT

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cache")

def estimate_tokens(text: str) -> int:
    """Ước tính số token cho văn bản tiếng Việt/markdown (trung bình ~2.1 ký tự/token)"""
    if not text:
        return 0
    return max(1, int(len(text) / 2.1))

def truncate_to_token_limit(text: str, max_tokens: int = MAX_TOKEN_LIMIT) -> str:
    """Giới hạn văn bản không vượt quá ngân sách token định sẵn (mặc định 300.000 tokens)"""
    if not text:
        return ""
    max_chars = int(max_tokens * 2.1)
    if len(text) > max_chars:
        return text[:max_chars] + f"\n\n...[Dữ liệu đã được cắt gọn để tuân thủ giới hạn {max_tokens:,} tokens]..."
    return text

async def crawl_with_crawl4ai(url: str, max_chars: int = 150000) -> str:
    """Sử dụng Crawl4AI (headless browser) bóc tách dữ liệu cho trang web JavaScript/SPA phức tạp."""
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler(verbose=False) as crawler:
            res = await crawler.arun(url=url, bypass_cache=True)
            if res and res.markdown:
                text = res.markdown.strip()
                if len(text) > max_chars:
                    text = text[:max_chars] + "..."
                return text
    except Exception as e:
        print(f"Crawl4AI fallback không thành công cho {url}: {e}")
    return ""

async def crawl_webpage(url: str, client: httpx.AsyncClient, max_chars: int = 150000) -> str:
    """
    Truy cập sâu vào URL trang web thực tế, bóc tách cấu trúc HTML và trích xuất nội dung văn bản bài viết cốt lõi.
    Áp dụng thuật toán chọn lọc vùng chứa văn bản phong phú nhất (Smart Container Extraction),
    loại bỏ quảng cáo rác, và fallback sang Crawl4AI nếu trang web render bằng Javascript.
    """
    if not url or not url.startswith(("http://", "https://")):
        return ""
        
    # Bỏ qua các định dạng tệp nhị phân
    if any(url.lower().endswith(ext) for ext in [".pdf", ".jpg", ".png", ".zip", ".mp4", ".mp3", ".xlsx", ".docx"]):
        return ""
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi,en-US;q=0.9,en;q=0.8"
    }
    
    clean_text = ""
    try:
        resp = await client.get(url, headers=headers, follow_redirects=True, timeout=8.0)
        if resp.status_code == 200 and resp.text:
            content_type = resp.headers.get("content-type", "").lower()
            if "text/html" in content_type or "text/plain" in content_type:
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # 1. Loại bỏ các thẻ rác, quảng cáo, điều hướng
                for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "iframe", "form", "button", "aside"]):
                    tag.decompose()
                    
                # 2. Tìm kiếm tất cả các vùng chứa tiềm năng có chứa bài viết
                candidates = []
                for tag_name in ["article", "main", "section", "div"]:
                    for el in soup.find_all(tag_name):
                        cls = " ".join(el.get("class", [])) if el.get("class") else ""
                        el_id = el.get("id", "")
                        if re.search(r'(content|article|post|detail|story|body|news|entry)', f"{cls} {el_id}", re.I):
                            t = el.get_text(strip=True)
                            if len(t) > 250:
                                candidates.append((len(t), el))
                                
                converter = html2text.HTML2Text()
                converter.ignore_links = True
                converter.ignore_images = True
                converter.ignore_emphasis = True
                converter.body_width = 0
                
                if candidates:
                    candidates.sort(key=lambda x: x[0], reverse=True)
                    best_el = candidates[0][1]
                    text = converter.handle(str(best_el))
                else:
                    ps = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40]
                    text = "\n\n".join(ps)
                    
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                clean_text = "\n".join(lines)
                
                if len(clean_text) >= 200:
                    if len(clean_text) > max_chars:
                        clean_text = clean_text[:max_chars] + "..."
                    return clean_text
    except Exception:
        pass

    # Fallback sang Crawl4AI nếu trang web render bằng JavaScript (SPA) hoặc chặn HTTP request
    c4ai_text = await crawl_with_crawl4ai(url, max_chars)
    if c4ai_text and len(c4ai_text) >= 200:
        return c4ai_text
        
    return clean_text


def extract_year(topic: str) -> int:
    match = re.search(r'\b(20\d{2})\b', topic)
    if match:
        return int(match.group(1))
    return datetime.now().year  

async def _process_search_response(data: dict, client: httpx.AsyncClient) -> tuple[str, list]:
    """
    Xử lý dữ liệu organic_results từ SerpAPI:
    Cào sâu nội dung các trang web thực tế, trích xuất văn bản cốt lõi và tổng hợp.
    """
    organic_results = data.get("organic_results", [])
    if not organic_results:
        return "", []
        
    # Cào sâu nội dung cho tối đa 4 link trang web hàng đầu
    items_to_crawl = organic_results[:4]
    
    async def fetch_item(item, idx):
        title = item.get("title", "")
        link = item.get("link", "")
        snippet = item.get("snippet", "")
        source_name = item.get("source", "")
        date = item.get("date", "")
        
        crawled_body = ""
        if link:
            crawled_body = await crawl_webpage(link, client)
            
        # Nếu cào sâu thành công thì dùng nội dung trang web; nếu bị chặn thì fallback về đoạn trích Google
        final_content = crawled_body if crawled_body and len(crawled_body) > 100 else snippet
        
        return {
            "position": idx,
            "title": title,
            "link": link,
            "redirect_link": "",
            "displayed_link": link,
            "date": date,
            "source": source_name,
            "snippet": final_content,
            "is_deep_crawled": bool(crawled_body and len(crawled_body) > 100)
        }
        
    crawled_sources = await asyncio.gather(*(fetch_item(item, i) for i, item in enumerate(items_to_crawl, start=1)))
    
    # Các kết quả organic còn lại (nếu có) lưu dưới dạng snippet Google
    remaining_sources = []
    for i, item in enumerate(organic_results[4:], start=len(items_to_crawl)+1):
        remaining_sources.append({
            "position": i,
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "redirect_link": "",
            "displayed_link": item.get("link", ""),
            "date": item.get("date", ""),
            "source": item.get("source", ""),
            "snippet": item.get("snippet", ""),
            "is_deep_crawled": False
        })
        
    sources = list(crawled_sources) + remaining_sources
    
    # Tạo chuỗi text tổng hợp từ nội dung cào sâu thực tế
    content_parts = []
    for s in sources:
        t = s.get("title", "")
        l = s.get("link", "")
        snip = s.get("snippet", "")
        if snip:
            tag = "[Dữ liệu cào sâu từ Website]" if s.get("is_deep_crawled") else "[Trích đoạn Google]"
            content_parts.append(f"### {tag}: {t}\nNguồn: {l}\nNội dung thực tế:\n{snip}")
            
    text = "\n\n".join(content_parts).strip()
    text = truncate_to_token_limit(text, max_tokens=MAX_TOKEN_LIMIT)
    return text, sources

async def search(query: str, client: httpx.AsyncClient) -> dict:
    # 1. Tạo cache key bằng MD5 hash của query
    h = hashlib.md5(query.encode("utf-8")).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"search_{h}.json")
    
    # 2. Đọc từ cache nếu có và chưa hết hạn (3 ngày = 259200 giây)
    if os.path.exists(cache_path):
        try:
            file_mtime = os.path.getmtime(cache_path)
            if (time.time() - file_mtime) < 259200:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached_res = json.load(f)
                print(f" -> [CACHE HIT] Đọc kết quả từ bộ đệm cho: '{query}'")
                return cached_res
        except Exception:
            pass

    # Sử dụng Google Search tiêu chuẩn thay vì google_ai_mode để lấy link thật và cào sâu
    url = "https://serpapi.com/search.json"
    params = {
        "api_key": SERP_API_KEY,
        "q": query,
        "engine": "google",
        "gl": "vn",
        "hl": "vi",
        "num": 5
    }

    def _save_to_cache(res_dict):
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(res_dict, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    try:
        response = await client.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        search_id = data.get("search_metadata", {}).get("id")
        html_url = f"https://serpapi.com/searches/{search_id}.html" if search_id else ""
        
        text, sources = await _process_search_response(data, client)
        res = {"text": text, "sources": sources, "html_url": html_url}
        _save_to_cache(res)
        return res
        
    except Exception as e:
        error_body = ""
        if hasattr(e, "response") and e.response is not None:
            try:
                error_body = e.response.text
            except Exception:
                error_body = ""
        print(f"Search Agent lỗi: {e} {error_body}")
        
        # Cơ chế Retry bất đồng bộ
        try:
            response = await client.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            search_id = data.get("search_metadata", {}).get("id")
            html_url = f"https://serpapi.com/searches/{search_id}.html" if search_id else ""
            
            text, sources = await _process_search_response(data, client)
            res = {"text": text, "sources": sources, "html_url": html_url}
            _save_to_cache(res)
            return res
            
        except Exception as retry_error:
            print(f"Search Agent retry lỗi: {retry_error}")
            return {"text": "", "sources": [], "html_url": ""}

async def search_market(topic: str) -> dict:
    year = extract_year(topic) 
    
    async with httpx.AsyncClient() as client:
        task_overview = search(f"{topic} tổng quan thị trường", client)
        task_trends = search(f"{topic} xu hướng {year}", client)
        task_competitors = search(f"{topic} doanh nghiệp thương hiệu lớn {year}", client)
        
        overview, trends, competitors = await asyncio.gather(
            task_overview, 
            task_trends, 
            task_competitors
        )
    
    results = {}
    results["overview"] = overview["text"]
    results["trends"] = trends["text"]
    results["competitors"] = competitors["text"]
    results["overview_sources"] = overview["sources"]
    results["trends_sources"] = trends["sources"]
    results["competitors_sources"] = competitors["sources"]
    results["sources"] = (
        overview["sources"] +
        trends["sources"] +
        competitors["sources"]
    )
    results["html_pages"] = [
        {"label": "Overview", "url": overview.get("html_url", "")},
        {"label": "Trends", "url": trends.get("html_url", "")},
        {"label": "Competitors", "url": competitors.get("html_url", "")}
    ]
    return results

async def search_market_with_queries(original_topic: str, queries: dict) -> dict:
    overview_queries = queries.get("overview", [])
    trend_queries = queries.get("trend", [])
    competition_queries = queries.get("competition", [])

    if not overview_queries:
        overview_queries = [f"{original_topic} tổng quan thị trường"]
    if not trend_queries:
        trend_queries = [f"{original_topic} xu hướng"]
    if not competition_queries:
        competition_queries = [f"{original_topic} doanh nghiệp hàng đầu đối thủ cạnh tranh"]

    async with httpx.AsyncClient() as client:
        overview_tasks = [search(q, client) for q in overview_queries]
        trend_tasks = [search(q, client) for q in trend_queries]
        competition_tasks = [search(q, client) for q in competition_queries]

        all_results = await asyncio.gather(*(overview_tasks + trend_tasks + competition_tasks))

    num_overview = len(overview_tasks)
    num_trend = len(trend_tasks)

    overview_results = all_results[:num_overview]
    trend_results = all_results[num_overview:num_overview + num_trend]
    competition_results = all_results[num_overview + num_trend:]

    overview_text = truncate_to_token_limit("\n\n".join([r["text"] for r in overview_results if r.get("text")]).strip(), max_tokens=MAX_TOKEN_LIMIT)
    trend_text = truncate_to_token_limit("\n\n".join([r["text"] for r in trend_results if r.get("text")]).strip(), max_tokens=MAX_TOKEN_LIMIT)
    competitors_text = truncate_to_token_limit("\n\n".join([r["text"] for r in competition_results if r.get("text")]).strip(), max_tokens=MAX_TOKEN_LIMIT)

    overview_sources = []
    for r in overview_results:
        overview_sources.extend(r.get("sources", []))

    trend_sources = []
    for r in trend_results:
        trend_sources.extend(r.get("sources", []))

    competitors_sources = []
    for r in competition_results:
        competitors_sources.extend(r.get("sources", []))

    def unique_sources(sources_list):
        seen_links = set()
        unique_list = []
        for s in sources_list:
            if not isinstance(s, dict):
                continue
            link = s.get("link") or s.get("url") or s.get("html_url")
            if link and link not in seen_links:
                seen_links.add(link)
                unique_list.append(s)
        return unique_list

    overview_sources = unique_sources(overview_sources)
    trend_sources = unique_sources(trend_sources)
    competitors_sources = unique_sources(competitors_sources)
    all_sources = unique_sources(overview_sources + trend_sources + competitors_sources)

    # Nếu không tìm thấy nguồn cho các truy vấn mở rộng, fallback về search_market mặc định
    if not all_sources:
        print(f" -> [Search Fallback] Không tìm thấy nguồn cho các truy vấn mở rộng. Chuyển sang tìm kiếm mặc định...")
        return await search_market(original_topic)

    results = {
        "overview": overview_text,
        "trends": trend_text,
        "competitors": competitors_text,
        "overview_sources": overview_sources,
        "trends_sources": trend_sources,
        "competitors_sources": competitors_sources,
        "sources": all_sources,
        "html_pages": [
            {"label": "Overview", "url": overview_results[0].get("html_url", "") if overview_results else ""},
            {"label": "Trends", "url": trend_results[0].get("html_url", "") if trend_results else ""},
            {"label": "Competitors", "url": competition_results[0].get("html_url", "") if competition_results else ""}
        ]
    }
    return results