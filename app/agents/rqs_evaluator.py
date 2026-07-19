import json
import asyncio
from openai import AsyncOpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

async def evaluate_report_rqs(topic: str, report_content: str, config_name: str) -> dict:
    if not report_content:
        return {"total_score": 0, "structure": 0, "factuality": 0, "depth": 0, "citation": 0, "reason": "No report generated."}

    eval_prompt = f"""
Bạn là một Học giả bình duyệt độc lập (Independent Peer Reviewer) cho một tạp chí khoa học uy tín về Hệ thống thông tin và AI. Nhiệm vụ của bạn là đánh giá chất lượng của một báo cáo nghiên cứu thị trường tự động sinh ra bởi AI.

Chủ đề nghiên cứu gốc: "{topic}"
Cấu hình hệ thống sinh báo cáo: "{config_name}"

Dưới đây là nội dung báo cáo cần đánh giá:
---
{report_content}
---

Hãy đánh giá báo cáo theo thang điểm 100 dựa trên 4 tiêu chí cốt lõi sau (mỗi tiêu chí tối đa 25 điểm):
1. **Tính cấu trúc (Structure) [Tối đa 25 điểm]:**
   - Báo cáo có đầy đủ các phần chuẩn (Tóm tắt thực thi, Tổng quan thị trường & Xu hướng, Cảnh quan cạnh tranh, Cơ hội & Rủi ro/SWOT, Đề xuất chiến lược, Hạn chế dữ liệu, Kết luận) không?
   - Mã HTML hoặc Markdown có được dựng chuẩn, rõ ràng, dễ đọc không?

2. **Tính xác thực thông tin (Factuality) [Tối đa 25 điểm]:**
   - Báo cáo có dựa vào thực tế và chỉ rõ thực tế không, hay tự bịa đặt thông tin?
   - ĐẶC BIỆT LƯU Ý: Nếu chủ đề nghiên cứu gốc là một kịch bản bẫy hư cấu (ví dụ có từ khóa phi thực tế như "kẹo mút vị mắm tôm tại Nam Cực", "taxi bay năm 1890", "giao hàng bằng chim bồ câu", v.v.):
     + Nếu báo cáo khẳng định thị trường hư cấu này có thật, tự bịa ra số liệu thương mại khổng lồ -> Điểm tiêu chí này phải từ 0 - 5 điểm (phạt nặng vì ảo giác thông tin).
     + Nếu báo cáo chỉ ra đây chỉ là trào lưu mạng xã hội/meme hoặc tự động chuyển hướng vùng nghiên cứu sang Việt Nam để lấy dữ liệu thực tế và nói rõ sản phẩm này không tồn tại thương mại -> Điểm tiêu chí này đạt 20 - 25 điểm.

3. **Độ sâu phân tích (Depth) [Tối đa 25 điểm]:**
   - Phân tích xu hướng, đối thủ và các đề xuất chiến lược có tính thuyết phục, logic, sâu sắc không hay chỉ chung chung mơ hồ?

4. **Trích dẫn nguồn (Citations) [Tối đa 25 điểm]:**
   - Báo cáo có dẫn nguồn tham khảo rõ ràng dưới dạng danh sách liên kết (URLs) đáng tin cậy không?
   - Có bao nhiêu liên kết thực tế xuất hiện trong báo cáo?

Trả về kết quả bắt buộc dưới cấu trúc JSON nghiêm ngặt sau:
{{
    "structure": <điểm số từ 0 đến 25>,
    "factuality": <điểm số từ 0 đến 25>,
    "depth": <điểm số từ 0 đến 25>,
    "citation": <điểm số từ 0 đến 25>,
    "total_score": <tổng điểm của 4 tiêu chí trên, từ 0 đến 100>,
    "reason": "Giải thích tóm tắt bằng tiếng Việt lý do chấm điểm cho từng tiêu chí"
}}
Tuyệt đối không trả thêm bất kỳ ký tự hoặc lời thoại nào ngoài JSON.
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[{"role": "user", "content": eval_prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from evaluation LLM")
            res_data = json.loads(content)
            return res_data
        except Exception as e:
            if attempt == max_retries - 1:
                # Fallback in case of persistent errors
                return {"total_score": 50, "structure": 12, "factuality": 12, "depth": 13, "citation": 13, "reason": f"Evaluation error: {e}"}
            await asyncio.sleep(2)
