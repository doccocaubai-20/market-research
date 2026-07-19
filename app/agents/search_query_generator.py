import json
import asyncio
import hashlib
import os
from openai import AsyncOpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

async def generate_search_queries(original_topic: str) -> dict:
    """
    Sinh tập hợp các truy vấn tìm kiếm mở rộng (refinement/expansion) từ chủ đề gốc.
    Đầu ra tuân thủ cấu trúc JSON yêu cầu và được cache lại để đồng bộ giữa các cấu hình.
    """
    CACHE_DIR = "cache"
    h = hashlib.md5(original_topic.encode("utf-8")).hexdigest()
    query_cache_path = os.path.join(CACHE_DIR, f"queries_{h}.json")
    
    # 1. Đọc từ cache nếu có để đảm bảo 100% đồng bộ giữa các cấu hình
    if os.path.exists(query_cache_path):
        try:
            with open(query_cache_path, "r", encoding="utf-8") as f:
                cached_queries = json.load(f)
            print(f" -> [QUERY CACHE HIT] Sử dụng lại truy vấn đã sinh trước đó cho: '{original_topic}'")
            return cached_queries
        except Exception:
            pass

    prompt = f"""
Bạn là thành phần SearchQueryGenerator (Bộ sinh truy vấn tìm kiếm) trong hệ thống nghiên cứu thị trường.
Nhiệm vụ của bạn là nhận vào một chủ đề nghiên cứu gốc (original_topic) và tạo ra các truy vấn tìm kiếm (search queries) tương ứng để thu thập thông tin từ Internet.

YÊU CẦU NGHIÊM NGẶT:
1. KHÔNG ĐƯỢC THAY THẾ chủ đề, thị trường, sản phẩm, doanh nghiệp hoặc thực thể mà người dùng nhập bằng một chủ đề khác "gần giống" hoặc "hợp lý hơn". Bạn phải giữ nguyên thực thể và ý định gốc.
2. Bạn chỉ thực hiện tinh chỉnh và mở rộng truy vấn (search query refinement/expansion), bao gồm:
   - Chuẩn hóa lỗi chính tả nếu có.
   - Bổ sung địa điểm và mốc thời gian đã có trong yêu cầu gốc.
   - Tạo các truy vấn tìm kiếm tối ưu (1-2 câu truy vấn mỗi loại) phục vụ cho 3 mục đích:
     + overview (Tổng quan): Tìm kiếm định nghĩa, quy mô, báo cáo chung.
     + trend (Xu hướng): Tìm kiếm xu hướng mới, cơ hội, rủi ro, dự báo.
     + competition (Cạnh tranh): Tìm kiếm các đối thủ lớn, doanh nghiệp dẫn đầu, thị phần.
   - Thêm từ đồng nghĩa hoặc cách gọi khác của thực thể nhưng KHÔNG thay đổi ý định ban đầu.

ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (JSON SCHEMA):
Bạn bắt buộc phải trả về một đối tượng JSON duy nhất theo cấu trúc sau:
{{
  "original_topic": "{original_topic}",
  "search_queries": {{
    "overview": [
      "truy vấn tổng quan 1",
      "truy vấn tổng quan 2"
    ],
    "trend": [
      "truy vấn xu hướng 1",
      "truy vấn xu hướng 2"
    ],
    "competition": [
      "truy vấn đối thủ 1",
      "truy vấn đối thủ 2"
    ]
  }}
}}
Tuyệt đối không trả về bất kỳ văn bản giải thích hoặc định dạng markdown nào ngoài đối tượng JSON này.
"""
    fallback_queries = {
        "original_topic": original_topic,
        "search_queries": {
            "overview": [f"{original_topic} tổng quan thị trường"],
            "trend": [f"{original_topic} xu hướng năm nay"],
            "competition": [f"{original_topic} doanh nghiệp hàng đầu đối thủ cạnh tranh"]
        }
    }

    def _save_to_cache(res_dict):
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(query_cache_path, "w", encoding="utf-8") as f:
                json.dump(res_dict, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    try:
        response = await client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
            timeout=30
        )
        content = response.choices[0].message.content
        if not content:
            _save_to_cache(fallback_queries)
            return fallback_queries
        res = json.loads(content)
        
        # Kiểm tra tính hợp lệ của cấu trúc dữ liệu
        if "original_topic" in res and "search_queries" in res:
            sq = res["search_queries"]
            if isinstance(sq, dict) and "overview" in sq and "trend" in sq and "competition" in sq:
                res["original_topic"] = original_topic
                _save_to_cache(res)
                return res
        _save_to_cache(fallback_queries)
        return fallback_queries
    except Exception as e:
        print(f"[SearchQueryGenerator Alert] Lỗi sinh truy vấn: {e}. Sử dụng cấu hình dự phòng mặc định.")
        _save_to_cache(fallback_queries)
        return fallback_queries
