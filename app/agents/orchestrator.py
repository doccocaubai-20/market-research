import json
import asyncio
from openai import AsyncOpenAI
from app.agents.search_agent import search_market_with_queries
from app.agents.evidence_retriever import format_evidence, retrieve_evidence
from app.agents.trend_agent import analyze_trends
from app.agents.competitor_agent import analyze_competitors
from app.agents.report_agent import generate_report
from app.agents.validator_agent import validate_with_llm
from app.agents.search_query_generator import generate_search_queries
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

async def run(topic: str, callback=None) -> dict:
    """
    Proposed Orchestrator:
    - Giữ nguyên topic gốc (original_topic).
    - Sử dụng SearchQueryGenerator để mở rộng truy vấn (overview, trend, competition).
    - Validator Agent kiểm định trên topic gốc.
    - Dừng sớm với INVALID/INSUFFICIENT_EVIDENCE nếu tìm kiếm thất bại hoặc validator loại.
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

    system_state = {
        "topic": topic,
        "search_data": None,
        "trends_data": None,
        "competitors_data": None,
        "final_report": None,
        "history": []
    }

    manager_prompt = f"""
Bạn là một Manager Agent (Tác nhân quản lý tổng tài) cấp cao, sở hữu tư duy logic sắc bén của một Quản lý dự án công nghệ. Nhiệm vụ tối cao của bạn là điều phối hành vi của các tác tử chuyên trách cấp dưới thông qua vòng lặp nhận thức ReAct (Reasoning and Acting) để tạo ra một báo cáo nghiên cứu thị trường toàn diện, chính xác và có tính hành động về chủ đề: "{topic}".

---
I. HỆ THỐNG CÔNG CỤ / HÀNH ĐỘNG BẠN CÓ QUYỀN ĐIỀU PHỐI:
1. "CALL_SEARCH": Kích hoạt Search Agent để thu thập dữ liệu Internet từ SerpAPI.
   - Điều kiện: Chỉ gọi khi hệ thống chưa có dữ liệu tìm kiếm (Search Data là False).
2. "CALL_ANALYZE_PARALLEL": Kích hoạt ĐỒNG THỜI luồng song song bất đồng bộ gồm Trend Agent (Phân tích xu hướng) và Competitor Agent (Phân tích đối thủ cạnh tranh).
   - Điều kiện: Hệ thống BẮT BUỘC phải có dữ liệu tìm kiếm (Search Data là True).
3. "CALL_REPORT": Kích hoạt Report Agent để chắt lọc, hợp nhất các bản dự thảo trung gian và render cấu trúc báo cáo chiến lược cuối cùng.
   - Điều kiện: Hệ thống ĐÃ CÓ ĐẦY ĐỦ cả dữ liệu xu hướng (Trends Data là True) và dữ liệu đối thủ (Competitors Data là True).
4. "FINISH": Kết thúc vòng lặp điều phối và đóng tiến trình khi báo cáo chiến lược cuối cùng đã được tạo lập thành công.

---
II. CÁC QUY TẮC RÀNG BUỘC LOGIC VÀ XỬ LÝ NGOẠI LỆ NGHIÊM NGẶT:
1. Chống lặp vô hạn (Infinite Loop Prevention): Kiểm tra kỹ "Nhật ký hành động lịch sử". Tuyệt đối không chọn lại một hành động `action` đã làm ở bước trước đó nếu trạng thái hệ thống không có sự biến đổi dữ liệu, nhằm tránh thảm họa lặp vô hạn và cạn kiệt tài nguyên API.
2. Đóng băng tri thức tĩnh: Tuyệt đối không tự ý nhảy đến bước "FINISH" khi chưa kích hoạt "CALL_REPORT" để tự bịa ra báo cáo từ bộ nhớ huấn luyện nội tại của bạn. Mọi báo cáo phải được xây dựng dựa trên bằng chứng thu thập thực tế.

---
III. ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (JSON SCHEMA):
Bạn bắt buộc phải phản hồi bằng một đối tượng JSON duy nhất, không kèm theo bất kỳ văn bản dẫn hướng, dấu ngoặc kép bọc ngoài (như ```json) hay ký tự thừa nào khác. Cấu trúc JSON phải tuân thủ nghiêm ngặt định dạng sau:
{{
    "thought": "Lập luận logic bằng tiếng Việt giải thích rõ lý do tại sao dựa trên trạng thái hệ thống hiện tại bạn lại đưa ra quyết định hành động này.",
    "action": "TÊN_HÀNH_ĐỘNG_BẠN_CHỌN"
}}
"""

    max_steps = 6
    step = 0
    while step < max_steps:
        step += 1
        
        current_context = f"""
        Trạng thái hệ thống hiện tại:
        - Đã có dữ liệu tìm kiếm (Search Data): {system_state['search_data'] is not None}
        - Đã có phân tích xu hướng (Trends Data): {system_state['trends_data'] is not None}
        - Đã có phân tích đối thủ (Competitors Data): {system_state['competitors_data'] is not None}
        - Đã có báo cáo chiến lược cuối cùng: {system_state['final_report'] is not None}
        - Nhật ký hành động lịch sử: {system_state['history']}
        """

        max_retries = 3
        decision = None
        for attempt in range(max_retries):
            try:
                response = await client.chat.completions.create(
                    model=DEEPSEEK_MODEL,
                    messages=[
                        {"role": "system", "content": manager_prompt},
                        {"role": "user", "content": current_context}
                    ],
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
                update({"agent": "orchestrator", "status": "warning", "message": f"Lỗi gọi LLM/Parse JSON (Lượt {attempt+1}/{max_retries}): {e}. Đang thử lại sau 2 giây..."})
                await asyncio.sleep(2)
        
        action = decision.get("action")
        thought = decision.get("thought")
        
        system_state['history'].append(action)
        
        if action == "CALL_SEARCH":
            update({"agent": "orchestrator", "status": "deciding", "message": f"Tư duy: {thought}"})
            
            # Tiền xử lý sinh truy vấn mở rộng
            update({"agent": "orchestrator", "status": "running", "message": "Đang phân tích mở rộng truy vấn tìm kiếm..."})
            query_gen_res = await generate_search_queries(topic)
            
            # Ghi lại log phục vụ tái lập thực nghiệm
            update({
                "agent": "orchestrator",
                "status": "query_generation",
                "message": f"Đã sinh tập truy vấn tìm kiếm cho: '{topic}'",
                "data": query_gen_res
            })
            
            search_queries = query_gen_res.get("search_queries", {})
            update({"agent": "search", "status": "running", "message": f"Đang tiến hành tìm kiếm song song cho '{topic}'..."})
            search_results = await search_market_with_queries(topic, search_queries)
            
            update({
                "agent": "search",
                "status": "debug",
                "message": "Search response (truncated)",
                "data": {
                    "overview": _truncate(search_results.get("overview")),
                    "trends": _truncate(search_results.get("trends")),
                    "competitors": _truncate(search_results.get("competitors")),
                    "sources_count": len(search_results.get("sources", [])),
                    "html_pages": search_results.get("html_pages", [])
                }
            })

            # Kiểm tra nguồn tìm kiếm trống (Insufficient Evidence)
            if not search_results.get("sources"):
                update({"agent": "orchestrator", "status": "failed", "message": "INSUFFICIENT_EVIDENCE"})
                return {
                    "topic": topic,
                    "report": None,
                    "sources": [],
                    "status": "INSUFFICIENT_EVIDENCE",
                    "details": {
                        "search": search_results,
                        "trends": None,
                        "competitors": None
                    }
                }

            # Thẩm định ngữ nghĩa trên topic gốc
            update({"agent": "validator", "status": "running", "message": "Đang thẩm định tính hợp lệ của dữ liệu..."})
            is_valid = await validate_with_llm(topic, search_results)
            if is_valid:
                update({"agent": "validator", "status": "done", "message": "Dữ liệu hợp lệ."})
            else:
                update({"agent": "validator", "status": "failed", "message": "INVALID"})
                return {
                    "topic": topic,
                    "report": None,
                    "sources": [],
                    "status": "INVALID",
                    "details": {
                        "search": search_results,
                        "trends": None,
                        "competitors": None
                    }
                }
                
            system_state["search_data"] = search_results
            update({"agent": "search", "status": "done", "message": "Thu thập dữ liệu Internet thành công."})
            
        elif action == "CALL_ANALYZE_PARALLEL":
            update({"agent": "orchestrator", "status": "deciding", "message": f"Tư duy: {thought}"})
            update({"agent": "orchestrator", "status": "running", "message": f"Kích hoạt luồng song song: Trend Agent & Competitor Agent..."})
            
            search_data = system_state["search_data"] or {}
            evidence = retrieve_evidence(topic, search_data.get("sources", []))
            if evidence:
                trend_context = format_evidence(evidence["trend"])
                competitor_context = format_evidence(evidence["competitor"])
                update({
                    "agent": "search",
                    "status": "debug",
                    "message": "Lightweight RAG: các đoạn được BM25 chọn theo tác tử.",
                    "data": {
                        role: [
                            {
                                "id": passage.id,
                                "url": passage.url,
                                "source_type": passage.source_type,
                                "excerpt": _truncate(passage.text, limit=240),
                            }
                            for passage in passages
                        ]
                        for role, passages in evidence.items()
                    },
                })
            else:
                # Older cache entries can have aggregate text without source-level excerpts.
                trend_context = search_data.get("trends", "")
                competitor_context = search_data.get("competitors", "")
                update({
                    "agent": "search",
                    "status": "debug",
                    "message": "Không có đoạn văn gắn URL để chạy BM25. Dùng ngữ cảnh tìm kiếm sẵn có.",
                })

            task_trend = analyze_trends(topic, trend_context)
            task_competitor = analyze_competitors(topic, competitor_context)
            
            trends_res, competitors_res = await asyncio.gather(task_trend, task_competitor)

            update({
                "agent": "trend",
                "status": "debug",
                "message": "Trend response (truncated)",
                "data": _truncate(trends_res)
            })
            update({
                "agent": "competitor",
                "status": "debug",
                "message": "Competitor response (truncated)",
                "data": _truncate(competitors_res)
            })
            
            system_state["trends_data"] = trends_res
            system_state["competitors_data"] = competitors_res
            update({"agent": "orchestrator", "status": "done", "message": "Luồng song song hoàn thành cấu trúc nháp."})

        elif action == "CALL_REPORT":
            update({"agent": "orchestrator", "status": "deciding", "message": f"Tư duy: {thought}"})
            update({"agent": "report", "status": "running", "message": "Report Agent đang tổng hợp báo cáo chiến lược cuối cùng..."})
            
            search_data = system_state["search_data"] or {}
            report = await generate_report(
                topic, 
                system_state["trends_data"], 
                system_state["competitors_data"], 
                search_data.get("sources", [])
            )

            update({
                "agent": "report",
                "status": "debug",
                "message": "Report response (truncated)",
                "data": {
                    "content": _truncate(report.get("content")),
                    "sources_count": len(report.get("sources", []))
                }
            })
            
            system_state["final_report"] = report
            update({"agent": "report", "status": "done", "message": "Báo cáo kinh doanh đã được tạo dựng."})

        elif action == "FINISH":
            update({"agent": "orchestrator", "status": "completed", "message": "Finish Task!"})
            break

    return {
        "topic": topic,
        "report": system_state["final_report"]["content"] if system_state["final_report"] else None,
        "sources": system_state["final_report"]["sources"] if system_state["final_report"] else [],
        "details": {
            "search": system_state["search_data"],
            "trends": system_state["trends_data"],
            "competitors": system_state["competitors_data"]
        }
    }
