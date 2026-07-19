import json
import asyncio
from openai import AsyncOpenAI
from app.agents.search_agent import search_market
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)


async def run_single_agent(topic: str, callback=None) -> dict:
    def update(event: dict):
        if callback:
            callback(event)

    update({"agent": "single", "status": "running", "message": f"Searching for '{topic}'..."})
    search_results = await search_market(topic)

    update({
        "agent": "single",
        "status": "debug",
        "message": "Search response",
        "data": {
            "overview": search_results.get("overview", ""),
            "trends": search_results.get("trends", ""),
            "competitors": search_results.get("competitors", ""),
            "sources_count": len(search_results.get("sources", []))
        }
    })

    if not search_results.get("sources"):
        update({"agent": "single", "status": "failed", "message": "No sources found."})
        return {
            "topic": topic,
            "report": None,
            "sources": [],
            "details": {"search": search_results}
        }

    overview_text = search_results.get("overview", "")
    trends_text = search_results.get("trends", "")
    competitors_text = search_results.get("competitors", "")

    prompt = f"""
# NGỮ CẢNH
Chủ đề nghiên cứu: {topic}

# DỮ LIỆU ĐẦU VÀO
<overview>
{overview_text}
</overview>

<trends>
{trends_text}
</trends>

<competitors>
{competitors_text}
</competitors>

# NHIỆM VỤ
Thực hiện đồng thời 3 phân tích sau dựa trên Dữ liệu đầu vào:
1. Phân tích Xu hướng: Trích xuất xu hướng tiêu dùng, cơ hội, rủi ro và dự báo ngắn hạn.
2. Phân tích Đối thủ: Đánh giá tổng quan cảnh quan cạnh tranh và chiến lược cốt lõi của đối thủ.
3. Báo cáo Tổng quan: Tổng hợp thành báo cáo hoàn chỉnh định dạng Markdown với cấu trúc:
   - 1. Tóm tắt thực thi
   - 2. Tổng quan thị trường & Xu hướng
   - 3. Cảnh quan cạnh tranh
   - 4. Cơ hội và Rủi ro (SWOT nhanh)
   - 5. Đề xuất chiến lược
   - 6. Hạn chế dữ liệu
   - 7. Kết luận

# RÀNG BUỘC
- KHÔNG tự bịa đặt số liệu hoặc thông tin. Chỉ sử dụng dữ liệu từ các thẻ XML đầu vào.
- Nếu thiếu dữ liệu cho bất kỳ phần nào, ghi rõ "Chưa đủ dữ liệu".
- Văn phong: Tiếng Việt, chuẩn doanh nghiệp, khách quan, súc tích.

# ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (JSON)
{{
    "trends": "Nội dung phân tích xu hướng...",
    "competitors": "Nội dung phân tích đối thủ...",
    "report": "Nội dung báo cáo chiến lược (Markdown)..."
}}
"""

    update({"agent": "single", "status": "running", "message": "Generating report..."})

    max_retries = 3
    parsed = None
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Bạn là một AI Agent phân tích chiến lược thị trường. Luôn tuân thủ nghiêm ngặt các ràng buộc và định dạng đầu ra."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=12000
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("DeepSeek returned empty content")
            parsed = json.loads(content)
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            update({"agent": "single", "status": "warning", "message": f"Lỗi gọi LLM/Parse JSON (Lượt {attempt+1}/{max_retries}): {e}. Đang thử lại sau 2 giây..."})
            await asyncio.sleep(2)
    trends_content = parsed.get("trends", "")
    competitors_content = parsed.get("competitors", "")
    report_content = parsed.get("report", "")

    url_candidates = []
    for item in search_results.get("sources", []):
        if not isinstance(item, dict):
            continue
        for key in ("link", "redirect_link", "displayed_link", "source", "url", "html_url"):
            value = item.get(key)
            if value:
                url_candidates.append(value)
    source_list = list(dict.fromkeys(url_candidates))

    update({"agent": "single", "status": "done", "message": "Report generated."})

    return {
        "topic": topic,
        "report": report_content,
        "sources": source_list,
        "details": {
            "search": search_results,
            "trends": trends_content,
            "competitors": competitors_content
        }
    }
