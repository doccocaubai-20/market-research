import json
import asyncio
import httpx
from openai import AsyncOpenAI
from app.agents.search_agent import search
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

async def run_agentic_single_agent(topic: str, callback=None) -> dict:
    """
    Agentic Single-Agent RAG Baseline:
    - 1 Tác tử đơn duy nhất chạy vòng lặp ReAct (Tư duy - Hành động - Quan sát).
    - Tự quyết định truy vấn tìm kiếm, tự tìm kiếm trong khi xử lý qua nhiều lượt (tối đa 4).
    - Tự đánh giá bối cảnh và độ đầy đủ của dữ liệu.
    - Không có validator agent; tự chọn hành động ABORT nếu phát hiện chủ đề hư cấu.
    """
    def update(event: dict):
        print(event)
        if callback:
            callback(event)

    def _truncate(value, limit=800):
        if value is None:
            return ""
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        if len(text) <= limit:
            return text
        return text[:limit] + "..."

    update({"agent": "single", "status": "running", "message": f"Bắt đầu Agentic Single-Agent RAG cho chủ đề: '{topic}'..."})

    # Thiết lập System Prompt cho vòng lặp ReAct của Single-Agent
    react_system_prompt = f"""
Bạn là một Tác tử Nghiên cứu Thị trường Đơn lẻ hoạt động theo cơ chế ReAct (Agentic Single-Agent RAG).
Nhiệm vụ của bạn là thu thập thông tin qua công cụ tìm kiếm và tự quyết định khi nào đã có đủ thông tin để tạo ra báo cáo nghiên cứu thị trường về chủ đề: "{topic}".

Bạn hoạt động theo vòng lặp ReAct (Tư duy - Hành động - Quan sát):
1. **Thought (Tư duy)**: Đánh giá xem thông tin hiện có đã đủ để viết báo cáo chưa, hay cần tìm kiếm thêm khía cạnh nào (tổng quan, xu hướng, đối thủ).
2. **Action (Hành động)**: Chọn một trong ba hành động sau:
   - "CALL_SEARCH": Thực hiện tìm kiếm thông tin mới. Yêu cầu cung cấp tham số "query".
   - "GENERATE_REPORT": Khi thông tin đã đầy đủ để viết báo cáo chi tiết 7 phần.
   - "ABORT": Nếu bạn phát hiện chủ đề nghiên cứu là hư cấu, phi thực tế, ảo giác hoặc không tồn tại trong thực tế kinh tế (ví dụ: kẹo mút vị mắm tôm tại Nam Cực, taxi bay chạy bằng than đá năm 1890).
3. **Observation (Quan sát)**: Nhận kết quả từ công cụ tìm kiếm để tiếp tục phân tích.

QUY TẮC NGHIÊM NGẶT:
- Bạn chỉ được tìm kiếm tối đa 4 lượt.
- Bạn phải tự phản tư (self-reflect) dựa trên kết quả cào được. Nếu thông tin cào được nói rõ hoặc cho thấy đây là một chủ đề hư cấu do AI tự tạo hoặc không có thật, bạn phải lập tức chọn hành động "ABORT" để từ chối làm tiếp.

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (JSON SCHEMA):
Bạn bắt buộc phải trả về một đối tượng JSON duy nhất theo một trong các định dạng sau:

Nếu muốn tìm kiếm thêm:
{{
  "thought": "Lập luận bằng tiếng Việt giải thích thông tin nào còn thiếu và lý do tìm kiếm...",
  "action": "CALL_SEARCH",
  "query": "từ khóa tìm kiếm tối ưu bằng tiếng Việt"
}}

Nếu muốn dừng lại và viết báo cáo:
{{
  "thought": "Lập luận bằng tiếng Việt tại sao thông tin cào được đã đầy đủ...",
  "action": "GENERATE_REPORT"
}}

Nếu muốn hủy bỏ do chủ đề hư cấu:
{{
  "thought": "Lập luận bằng tiếng Việt tại sao đây là chủ đề hư cấu/ảo giác không có thật...",
  "action": "ABORT"
}}
"""

    history = []
    collected_sources = []
    all_searches = []
    
    max_loops = 4
    loop_count = 0
    action = None
    
    async with httpx.AsyncClient() as http_client:
        while loop_count < max_loops:
            loop_count += 1
            
            # Xây dựng ngữ cảnh hội thoại cho ReAct
            messages = [{"role": "system", "content": react_system_prompt}]
            for h in history:
                messages.append({"role": "user", "content": h["user"]})
                messages.append({"role": "assistant", "content": h["assistant"]})
            
            current_user_msg = f"Lượt chạy thứ {loop_count}/{max_loops}. Trạng thái lịch sử tìm kiếm: {len(all_searches)} truy vấn đã thực hiện. Hãy đưa ra quyết định hành động tiếp theo của bạn."
            messages.append({"role": "user", "content": current_user_msg})

            max_retries = 3
            decision = None
            for attempt in range(max_retries):
                try:
                    response = await client.chat.completions.create(
                        model=DEEPSEEK_MODEL,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.1
                    )
                    content = response.choices[0].message.content
                    if not content:
                        raise ValueError("DeepSeek returned empty content")
                    decision = json.loads(content)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    update({"agent": "single", "status": "warning", "message": f"Lỗi gọi LLM/Parse JSON ReAct (Lượt {attempt+1}/{max_retries}): {e}. Đang thử lại..."})
                    await asyncio.sleep(2)
            
            thought = decision.get("thought")
            action = decision.get("action")
            
            update({"agent": "single", "status": "deciding", "message": f"Vòng {loop_count} - Tư duy: {thought}"})
            
            # Ghi nhận trợ lý phản hồi vào lịch sử
            assistant_content = json.dumps(decision, ensure_ascii=False)
            
            if action == "ABORT":
                update({"agent": "single", "status": "failed", "message": f"Tác tử tự đánh giá phát hiện chủ đề hư cấu: {thought}"})
                return {
                    "topic": topic,
                    "report": None,
                    "sources": [],
                    "details": {
                        "searches": all_searches,
                        "status": "ABORTED"
                    }
                }
                
            elif action == "CALL_SEARCH":
                query = decision.get("query")
                update({"agent": "single", "status": "running", "message": f"Gọi công cụ tìm kiếm cho truy vấn: '{query}'..."})
                
                search_res = await search(query, http_client)
                text = search_res.get("text", "")
                sources = search_res.get("sources", [])
                
                all_searches.append({"query": query, "sources_count": len(sources), "text": text})
                collected_sources.extend(sources)
                
                update({"agent": "single", "status": "debug", "message": f"Kết quả tìm kiếm cho '{query}': cào được {len(sources)} nguồn."})
                
                observation_content = f"Kết quả tìm kiếm cho truy vấn '{query}':\n\n{text[:1500]}..." if len(text) > 1500 else f"Kết quả tìm kiếm cho truy vấn '{query}':\n\n{text}"
                
                # Lưu vào lịch sử ReAct
                history.append({
                    "user": current_user_msg,
                    "assistant": assistant_content
                })
                # Bước tiếp theo sẽ nhận Observation ở phần User input mới
                react_system_prompt += f"\nObservation từ truy vấn '{query}':\n{observation_content}\n"
                
            elif action == "GENERATE_REPORT":
                update({"agent": "single", "status": "running", "message": "Quyết định dừng tìm kiếm và tiến hành tổng hợp báo cáo..."})
                break
            else:
                # Default case: if unknown action is returned, break
                break

    # Tiến hành tổng hợp báo cáo kinh doanh từ dữ liệu đã cào được
    update({"agent": "single", "status": "running", "message": "Đang tổng hợp báo cáo kinh doanh cuối cùng..."})
    
    # Gom tất cả lịch sử quan sát tìm kiếm làm dữ liệu đầu vào cho báo cáo
    search_context_parts = []
    for idx, s in enumerate(all_searches):
        search_context_parts.append(f"### Lượt cào thứ {idx+1}")
        search_context_parts.append(f"Truy vấn: {s['query']}")
        search_context_parts.append(f"Nội dung cào được:\n{s.get('text', '')}")
    
    search_context_text = "\n\n".join(search_context_parts)

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

    final_sources = unique_sources(collected_sources)

    report_prompt = f"""
Dựa trên tất cả dữ liệu tìm kiếm thu thập được dưới đây, hãy viết một báo cáo nghiên cứu thị trường toàn diện, chính xác và có tính hành động về chủ đề: "{topic}".

# DỮ LIỆU TÌM KIẾM THU THẬP ĐƯỢC:
{search_context_text}

# DANH SÁCH NGUỒN THAM CHIẾU (URL):
{json.dumps(final_sources, ensure_ascii=False, indent=2)}

# NHIỆM VỤ:
Tạo báo cáo nghiên cứu thị trường định dạng Markdown với cấu trúc 7 phần cố định:
1. Tóm tắt thực thi
2. Tổng quan thị trường & Xu hướng
3. Cảnh quan cạnh tranh
4. Cơ hội và Rủi ro (SWOT nhanh)
5. Đề xuất chiến lược
6. Hạn chế dữ liệu
7. Kết luận

# RÀNG BUỘC:
- KHÔNG tự bịa đặt số liệu hoặc thông tin. Chỉ sử dụng thông tin thu thập thực tế được cung cấp trong dữ liệu tìm kiếm ở trên.
- Trích dẫn nguồn cụ thể ở phần cuối và ghim đường link thực tế từ danh sách nguồn tham chiếu vào các phần tương ứng.
- Văn phong: Tiếng Việt, chuẩn doanh nghiệp, khách quan, súc tích.

Hãy phản hồi dưới dạng JSON duy nhất chứa báo cáo:
{{
  "report": "Nội dung báo cáo chi tiết ở định dạng Markdown..."
}}
"""

    max_retries = 3
    report_content = None
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Bạn là một AI Agent phân tích chiến lược thị trường. Luôn tuân thủ nghiêm ngặt các ràng buộc và định dạng đầu ra."},
                    {"role": "user", "content": report_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=8000
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("DeepSeek returned empty content")
            report_data = json.loads(content)
            report_content = report_data.get("report")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            update({"agent": "single", "status": "warning", "message": f"Lỗi gọi LLM tổng hợp báo cáo (Lượt {attempt+1}/{max_retries}): {e}. Đang thử lại..."})
            await asyncio.sleep(2)

    # Lọc trùng các nguồn URL
    url_candidates = []
    for item in collected_sources:
        if not isinstance(item, dict):
            continue
        for key in ("link", "redirect_link", "displayed_link", "source", "url", "html_url"):
            value = item.get(key)
            if value:
                url_candidates.append(value)
    source_list = list(dict.fromkeys(url_candidates))

    update({"agent": "single", "status": "done", "message": "Đã hoàn thành báo cáo nghiên cứu thị trường."})

    return {
        "topic": topic,
        "report": report_content,
        "sources": source_list,
        "details": {
            "searches": all_searches,
            "status": "SUCCESS"
        }
    }
