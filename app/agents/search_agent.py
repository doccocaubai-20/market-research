import asyncio
import re
from datetime import datetime
import httpx
import os
import json
import hashlib
import time
from app.config import SERP_API_KEY

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cache")

def _collect_text_pairs(node, collected: list):
    if isinstance(node, dict):
        title = node.get("title") or node.get("heading") or node.get("name")
        snippet = node.get("snippet") or node.get("text") or node.get("description")
        if title and snippet:
            collected.append(f"{title}: {snippet}")
        elif snippet:
            collected.append(snippet)
        elif title:
            collected.append(title)
        for value in node.values():
            _collect_text_pairs(value, collected)
    elif isinstance(node, list):
        for item in node:
            _collect_text_pairs(item, collected)

def _extract_block_texts(text_blocks: list) -> list:
    texts = []
    for block in text_blocks:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "list":
            items = block.get("list", [])
            for item in items:
                if not isinstance(item, dict):
                    continue
                snippet = item.get("snippet") or item.get("text") or item.get("title") or item.get("heading")
                if snippet:
                    texts.append(snippet)
        snippet = block.get("snippet") or block.get("text")
        title = block.get("title") or block.get("heading")
        if title and snippet:
            texts.append(f"{title}: {snippet}")
        elif snippet:
            texts.append(snippet)
        elif title:
            texts.append(title)
    return texts

def _extract_reference_links(text_blocks: list, references: list) -> list:
    links = []
    def _append_link(value):
        if isinstance(value, str) and value:
            links.append(value)
    def _append_link_items(items):
        for item in items:
            if isinstance(item, dict) and item.get("link"):
                links.append(item.get("link"))
            elif isinstance(item, str) and item:
                links.append(item)
    for block in text_blocks:
        if not isinstance(block, dict):
            continue
        for ref in block.get("reference_links", []) or []:
            _append_link_items([ref])
        _append_link_items(block.get("snippet_links", []) or [])
        for ref_index in block.get("reference_indexes", []) or []:
            if isinstance(ref_index, int) and 0 <= ref_index < len(references):
                ref = references[ref_index]
                _append_link_items([ref])
        if block.get("type") == "list":
            for item in block.get("list", []) or []:
                if not isinstance(item, dict):
                    continue
                for ref in item.get("reference_links", []) or []:
                    _append_link_items([ref])
                _append_link_items(item.get("snippet_links", []) or [])
                for ref_index in item.get("reference_indexes", []) or []:
                    if isinstance(ref_index, int) and 0 <= ref_index < len(references):
                        ref = references[ref_index]
                        _append_link_items([ref])
    return links

def extract_year(topic: str) -> int:
    match = re.search(r'\b(20\d{2})\b', topic)
    if match:
        return int(match.group(1))
    return datetime.now().year  

async def search(query: str, client: httpx.AsyncClient) -> dict:
    # 1. Tạo cache key bằng MD5 hash của query
    h = hashlib.md5(query.encode("utf-8")).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"search_{h}.json")
    
    # 2. Đọc từ cache nếu có và chưa hết hạn (ví dụ: 3 ngày = 259200 giây)
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

    url = "https://serpapi.com/search.json"
    params = {
        "api_key": SERP_API_KEY,
        "q": query,
        "engine": "google_ai_mode"
    }

    # Hàm nội bộ để lưu kết quả vào cache
    def _save_to_cache(res_dict):
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(res_dict, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    try:
        response = await client.get(url, params=params, timeout=45)
        response.raise_for_status()
        data = response.json()
        
        search_id = data.get("search_metadata", {}).get("id")
        html_url = f"https://serpapi.com/searches/{search_id}.html" if search_id else ""
        text_blocks = data.get("text_blocks", [])
        references = data.get("references", [])
        
        if not text_blocks:
            res = {"text": "", "sources": [], "html_url": html_url}
            _save_to_cache(res)
            return res
            
        block_texts = _extract_block_texts(text_blocks)
        reference_links = _extract_reference_links(text_blocks, references)
        sources = []
        
        for i, block in enumerate(text_blocks, start=1):
            if not isinstance(block, dict):
                continue
            nested_texts = []
            _collect_text_pairs(block, nested_texts)
            combined_text = "\n".join([t for t in nested_texts if t]).strip()
            sources.append({
                "position": i,
                "title": block.get("title", "") or block.get("heading", ""),
                "link": block.get("link", "") or block.get("source", ""),
                "redirect_link": "",
                "displayed_link": block.get("source", ""),
                "date": "",
                "source": block.get("source", ""),
                "snippet": combined_text or block.get("text", "") or block.get("snippet", "")
            })
            
        for i, link in enumerate(reference_links, start=1):
            sources.append({
                "position": i,
                "title": "",
                "link": link,
                "redirect_link": "",
                "displayed_link": "",
                "date": "",
                "source": "",
                "snippet": ""
            })
            
        if block_texts and not any(s.get("snippet") for s in sources):
            sources = [
                {
                    "position": i,
                    "title": "",
                    "link": "",
                    "redirect_link": "",
                    "displayed_link": "",
                    "date": "",
                    "source": "",
                    "snippet": text
                }
                for i, text in enumerate(block_texts, start=1)
            ]
            
        text = "\n\n".join([s.get("snippet", "") for s in sources if s.get("snippet")]).strip()
        if not text and block_texts:
            text = "\n\n".join(block_texts).strip()
            
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
            response = await client.get(url, params=params, timeout=90)
            response.raise_for_status()
            data = response.json()
            
            search_id = data.get("search_metadata", {}).get("id")
            html_url = f"https://serpapi.com/searches/{search_id}.html" if search_id else ""
            text_blocks = data.get("text_blocks", [])
            references = data.get("references", [])
            
            if not text_blocks:
                res = {"text": "", "sources": [], "html_url": html_url}
                _save_to_cache(res)
                return res
                
            block_texts = _extract_block_texts(text_blocks)
            reference_links = _extract_reference_links(text_blocks, references)
            sources = []
            
            for i, block in enumerate(text_blocks, start=1):
                if not isinstance(block, dict):
                    continue
                nested_texts = []
                _collect_text_pairs(block, nested_texts)
                combined_text = "\n".join([t for t in nested_texts if t]).strip()
                sources.append({
                    "position": i,
                    "title": block.get("title", "") or block.get("heading", ""),
                    "link": block.get("link", "") or block.get("source", ""),
                    "redirect_link": "",
                    "displayed_link": block.get("source", ""),
                    "date": "",
                    "source": block.get("source", ""),
                    "snippet": combined_text or block.get("text", "") or block.get("snippet", "")
                })
                
            for i, link in enumerate(reference_links, start=1):
                sources.append({
                    "position": i,
                    "title": "",
                    "link": link,
                    "redirect_link": "",
                    "displayed_link": "",
                    "date": "",
                    "source": "",
                    "snippet": ""
                })
                
            if block_texts and not any(s.get("snippet") for s in sources):
                sources = [
                    {
                        "position": i,
                        "title": "",
                        "link": "",
                        "redirect_link": "",
                        "displayed_link": "",
                        "date": "",
                        "source": "",
                        "snippet": text
                    }
                    for i, text in enumerate(block_texts, start=1)
                ]
                
            text = "\n\n".join([s.get("snippet", "") for s in sources if s.get("snippet")]).strip()
            if not text and block_texts:
                text = "\n\n".join(block_texts).strip()
                
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

    overview_text = "\n\n".join([r["text"] for r in overview_results if r.get("text")]).strip()
    trend_text = "\n\n".join([r["text"] for r in trend_results if r.get("text")]).strip()
    competitors_text = "\n\n".join([r["text"] for r in competition_results if r.get("text")]).strip()

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

    # Check if we got any sources. If not, fallback to the default search_market
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