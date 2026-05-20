from openai import OpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

def analyze_competitors(topic: str, search_results) -> str:
    """
    Phân tích đối thủ cạnh tranh với Prompt tối ưu
    """
    
    if isinstance(search_results, str):
        context = search_results.strip()
    else:
        context = "\n".join([
            f"- {r.get('title', '')}: {r.get('snippet', '')}"
            for r in search_results
        ])
    if not context:
        context = "Chưa có đủ dữ liệu"


    # PROMPT NÂNG CẤP
    prompt = f"""Dựa trên tập dữ liệu thô dưới đây về thị trường '{topic}':

<data>
{context}
</data>

Hãy đóng vai trò là một Chuyên gia Phân tích Chiến lược, lập một báo cáo cạnh tranh súc tích với cấu trúc sau:

**1. Bức tranh Cạnh tranh Tổng quan**
- Nhận định ngắn gọn về mức độ khốc liệt của thị trường.
- Liệt kê Top 3-5 đối thủ/thương hiệu dẫn đầu.


**2. Chiến lược Cạnh tranh Cốt lõi**
- Các thương hiệu trên đang dùng chiến lược gì để giành khách hàng? (Ví dụ: Cạnh tranh về giá, Khác biệt hóa sản phẩm, Tập trung vào dịch vụ...)

**YÊU CẦU NGHIÊM NGẶT:**
1. TUYỆT ĐỐI CHỈ sử dụng thông tin có trong thẻ <data>.
2. KHÔNG tự bịa đặt số liệu. Nếu cột/mục nào không có thông tin, hãy điền "Chưa đủ dữ liệu".
3. Trình bày bằng tiếng Việt, văn phong doanh nghiệp, sử dụng cấu trúc Markdown chuyên nghiệp.
"""

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "Bạn là Chuyên gia Phân tích Cạnh tranh (Competitive Intelligence Analyst). Bạn nổi tiếng với các báo cáo khách quan, chính xác và sắc bén."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content