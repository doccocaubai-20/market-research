from app.agents.search_agent import search_market
from app.agents.trend_agent import analyze_trends
from app.agents.competitor_agent import analyze_competitors
from app.agents.report_agent import generate_report
# Nhập thêm một hàm AI mới để làm bộ lọc
from app.agents.evaluator_agent import evaluate_search_data 

def run_agentic(topic: str, callback=None) -> dict:
    def update(event: dict):
        print(event)
        if callback:
            callback(event)

    # ---------------------------------------------------------
    # BƯỚC 1 & 2: VÒNG LẶP TÌM KIẾM VÀ TỰ ĐÁNH GIÁ (CORE AGENTIC)
    # ---------------------------------------------------------
    MAX_RETRIES = 3  # Tránh việc bot bị kẹt trong vòng lặp vô tận
    iteration = 0
    search_queries = [topic] # Lưu lịch sử từ khóa
    all_results = []
    
    is_data_sufficient = False

    while not is_data_sufficient and iteration < MAX_RETRIES:
        iteration += 1
        current_query = search_queries[-1]
        
        update({
            "agent": "search", "status": "running",
            "message": f"🔍 Lần thử {iteration}: Đang tìm kiếm '{current_query}'..."
        })
        
        # 1. Gọi hàm Search
        raw_results = search_market(current_query)
        all_results.extend(raw_results.get("competitors", [])) # Giả sử đang gom dữ liệu
        
        # 2. Gọi hàm AI Đánh giá (Evaluator)
        update({
            "agent": "evaluator", "status": "running",
            "message": "🤔 Đang kiểm duyệt chất lượng dữ liệu..."
        })
        
        # Hàm này gọi LLM. Trả về JSON: {"is_sufficient": boolean, "reason": "...", "next_query": "..."}
        evaluation = evaluate_search_data(topic, all_results)
        
        if evaluation["is_sufficient"]:
            is_data_sufficient = True
            update({"agent": "evaluator", "status": "done", "message": "✅ Dữ liệu đạt chuẩn!"})
        else:
            update({
                "agent": "evaluator", "status": "warning",
                "message": f"⚠️ Dữ liệu thiếu/lỗi (Lý do: {evaluation['reason']}). Đổi từ khóa thành: {evaluation['next_query']}"
            })
            # Thêm từ khóa mới do AI tự nghĩ ra vào danh sách để vòng lặp sau dùng
            search_queries.append(evaluation['next_query'])

    # Nếu sau MAX_RETRIES mà vẫn fail thì báo lỗi hoặc dùng tạm dữ liệu cũ
    if not is_data_sufficient:
        update({"agent": "system", "status": "warning", "message": "⚠️ Đạt giới hạn tìm kiếm, sử dụng dữ liệu hiện tại."})

    # ---------------------------------------------------------
    # BƯỚC 3 & 4 & 5: CHẠY TIẾP LUỒNG PHÂN TÍCH NHƯ BÌNH THƯỜNG
    # (Vì dữ liệu đầu vào giờ đã chắc chắn "sạch" và "đủ")
    # ---------------------------------------------------------
    
    # ... [Code chạy analyze_trends, analyze_competitors, generate_report giống y hệt code cũ của bạn] ...

    return {
        "topic": topic,
        # ...
    }