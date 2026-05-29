import asyncio
import re
from datetime import datetime
import httpx
from app.config import SERP_API_KEY

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

# 1. Chuyển đổi sang hàm async và truyền AsyncClient vào để tái sử dụng connection pool
async def search(query: str, client: httpx.AsyncClient) -> dict:
    url = "https://serpapi.com/search.json"
    params = {
        "api_key": SERP_API_KEY,
        "q": query,
        "engine": "google_ai_mode"
    }
    try:
        # Thay thế requests.get bằng client.get bất đồng bộ của HTTPX
        response = await client.get(url, params=params, timeout=45)
        response.raise_for_status()
        data = response.json()
        
        search_id = data.get("search_metadata", {}).get("id")
        html_url = f"https://serpapi.com/searches/{search_id}.html" if search_id else ""
        text_blocks = data.get("text_blocks", [])
        references = data.get("references", [])
        
        if not text_blocks:
            return {"text": "", "sources": [], "html_url": html_url}
            
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
            
        return {"text": text, "sources": sources, "html_url": html_url}
        
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
                return {"text": "", "sources": [], "html_url": html_url}
                
            block_texts = _extract_block_texts(text_blocks)
            reference_links = _extract_reference_links(text_blocks, references) # Sửa lỗi thiếu references ở hàm cũ
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
                
            return {"text": text, "sources": sources, "html_url": html_url}
            
        except Exception as retry_error:
            print(f"Search Agent retry lỗi: {retry_error}")
            return {"text": "", "sources": [], "html_url": ""}

# 2. Khai báo hàm async tối cao để Orchestrator thực hiện await
async def search_market(topic: str) -> dict:
    year = extract_year(topic) 
    
    # Sử dụng context manager httpx.AsyncClient để quản lý connection pool phi nghẽn mạng
    async with httpx.AsyncClient() as client:
        # Tạo cấu trúc luồng chạy song song (Parallel tasks) cho cả 3 từ khóa
        task_overview = search(f"{topic} tổng quan thị trường", client)
        task_trends = search(f"{topic} xu hướng {year}", client)
        task_competitors = search(f"{topic} doanh nghiệp thương hiệu lớn {year}", client)
        
        # Đồng loạt phát lệnh kích hoạt mạng phi trạng thái và thu hồi kết quả cùng một lúc
        overview, trends, competitors = await asyncio.gather(
            task_overview, 
            task_trends, 
            task_competitors
        )
    
    # Tổ chức lại cấu trúc dữ liệu trả về tương thích 100% với trạng thái memory cũ
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