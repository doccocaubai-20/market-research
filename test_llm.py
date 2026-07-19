import asyncio
import json
import os
import sys
from openai import AsyncOpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    
    # Let's recreate the manager prompt and the context to see what happens
    topic = "Phân tích ma trận SWOT của thị trường kẹo mút vị mắm tôm tại Nam Cực"
    
    manager_prompt = f"""
Bạn là một Manager Agent (Tác nhân quản lý tổng tài) cấp cao, sở hữu tư duy logic sắc bén của một Quản lý dự án công nghệ. Nhiệm vụ tối cao của bạn là điều phối hành vi của các tác tử chuyên trách cấp dưới thông qua vòng lặp nhận thức ReAct (Reasoning and Acting) để tạo ra một báo cáo nghiên cứu thị trường toàn diện, chính xác và có tính hành động về chủ đề: "{topic}".

---
I. HỆ THỐNG CÔNG CỤ / HÀNH ĐỘNG BẠN CÓ QUYỀN ĐIỀU PHỐI:
1. "CALL_SEARCH": Kích hoạt Search Agent để thu thập dữ liệu Internet từ SerpAPI. 
   - Điều kiện: Chỉ gọi khi hệ thống chưa có dữ liệu tìm kiếm (Search Data là False) và chưa từng bị lỗi tìm kiếm.
2. "REFORMULATE_QUERY": Tự động phân tích lỗi, tối ưu và mở rộng lại từ khóa tìm kiếm khi từ khóa cũ không mang lại kết quả.
   - Điều kiện: Chỉ kích hoạt khi trong "Nhật ký hành động lịch sử" xuất hiện cờ lỗi "SEARCH_FAILED".
3. "CALL_ANALYZE_PARALLEL": Kích hoạt ĐỒNG THỜI luồng song song bất đồng bộ gồm Trend Agent (Phân tích xu hướng) và Competitor Agent (Phân tích đối thủ cạnh tranh).
   - Điều kiện: Hệ thống BẮT BUỘC phải có dữ liệu tìm kiếm (Search Data là True).
4. "CALL_REPORT": Kích hoạt Report Agent để chắt lọc, hợp nhất các bản dự thảo trung gian và render cấu trúc báo cáo chiến lược cuối cùng.
   - Điều kiện: Hệ thống ĐÃ CÓ ĐẦY ĐỦ cả dữ liệu xu hướng (Trends Data là True) và dữ liệu đối thủ (Competitors Data là True).
5. "FINISH": Kết thúc vòng lặp điều phối và đóng tiến trình khi báo cáo chiến lược cuối cùng đã được tạo lập thành công.

---
II. CÁC QUY TẮC RÀNG BUỘC LOGIC VÀ XỬ LÝ NGOẠI LỆ NGHIÊM NGẶT:
1. Chống lặp vô hạn (Infinite Loop Prevention): Kiểm tra kỹ "Nhật ký hành động lịch sử". Tuyệt đối không chọn lại một hành động `action` đã làm ở bước trước đó nếu trạng thái hệ thống không có sự biến đổi dữ liệu, nhằm tránh thảm họa lặp vô hạn và cạn kiệt tài nguyên API.
2. Xử lý dữ liệu rỗng (Search Empty Handling): 
   - Nếu lượt chạy trước trả về cờ "SEARCH_FAILED", điều đó chứng tỏ từ khóa '{topic}' quá hẹp, quá ngách hoặc sai lệch mốc thời gian khiến Google Search không tìm thấy bối cảnh. 
   - Lúc này, bạn KHÔNG ĐƯỢC CHỌN LẠI hành động "CALL_SEARCH" với từ khóa cũ. Bạn BẮT BUỘC phải chọn hành động "REFORMULATE_QUERY" để nới rộng biên độ tìm kiếm (ví dụ: lược bỏ bớt các từ khóa thuộc tính ngách quá sâu hoặc điều chỉnh mốc năm phù hợp).
3. Đóng băng tri thức tĩnh: Tuyệt đối không tự ý nhảy đến bước "FINISH" khi chưa kích hoạt "CALL_REPORT" để tự bịa ra báo cáo từ bộ nhớ huấn luyện nội tại của bạn. Mọi báo cáo phải được xây dựng dựa trên bằng chứng thu thập thực tế.

---
III. ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (JSON SCHEMA):
Bạn bắt buộc phải phản hồi bằng một đối tượng JSON duy nhất, không kèm theo bất kỳ văn bản dẫn hướng, dấu ngoặc kép bọc ngoài (như ```json) hay ký tự thừa nào khác. Cấu trúc JSON phải tuân thủ nghiêm ngặt 2 kịch bản sau:

KỊCH BẢN A: Khi thực hiện các bước điều phối thông thường (CALL_SEARCH, CALL_ANALYZE_PARALLEL, CALL_REPORT, FINISH):
{{
    "thought": "Lập luận logic bằng tiếng Việt giải thích rõ lý do tại sao dựa trên trạng thái hệ thống hiện tại bạn lại đưa ra quyết định hành động này.",
    "action": "TÊN_HÀNH_ĐỘNG_BẠN_CHỌN"
}}

KỊCH BẢN B: Khi hệ thống gặp lỗi search rỗng và bạn quyết định sửa đổi từ khóa (REFORMULATE_QUERY):
{{
    "thought": "Phân tích lý do tại sao từ khóa cũ thất bại và lập luận logic cho việc lựa chọn từ khóa bao quát mới...",
    "action": "REFORMULATE_QUERY",
    "new_topic": "Từ khóa nghiên cứu mới đã được bạn lược bỏ bớt các từ ngách quá sâu hoặc đã làm rộng ngữ cảnh"
}}
"""

    current_context = """
    Trạng thái hệ thống hiện tại:
    - Đã có dữ liệu tìm kiếm (Search Data): False
    - Đã có phân tích xu hướng (Trends Data): False
    - Đã có phân tích đối thủ (Competitors Data): False
    - Đã có báo cáo chiến lược cuối cùng: False
    - Nhật ký hành động lịch sử: []
    """

    print(f"Calling DeepSeek API with model: {DEEPSEEK_MODEL}...")
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
        print("API Call Successful!")
        content = response.choices[0].message.content
        print(f"Raw response content: {repr(content)}")
        try:
            parsed = json.loads(content)
            print("Successfully parsed as JSON:")
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        except Exception as je:
            print(f"Failed to parse JSON: {je}")
    except Exception as e:
        print(f"API Error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
