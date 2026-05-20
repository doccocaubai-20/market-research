from openai import OpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

def analyze_trends(topic: str, search_results) -> str:

    if isinstance(search_results, str):
        context = search_results.strip()
    else:
        context = "\n".join([
            f"- {r['title']}: {r['snippet']}"
            for r in search_results
        ])
    if not context:
        context = "Chưa có đủ thông tin"


    prompt = f"""Dựa trên các bài viết sau về {topic}:
{context}

Phân tích dưới góc nhìn của một nhà đầu tư đang cân nhắc gia nhập thị trường này:

1. XU HƯỚNG TIÊU DÙNG NỔI BẬT
   - Nhóm khách hàng mục tiêu chính là ai?
   - Họ đang tìm kiếm gì ở sản phẩm/dịch vụ?
   - Hành vi mua hàng đang thay đổi như thế nào?

2. CƠ HỘI CHƯA ĐƯỢC KHAI THÁC
   - Phân khúc khách hàng nào đang bị bỏ ngỏ?
   - Nhu cầu nào chưa được đáp ứng tốt?

3. RỦI RO CẦN LƯU Ý
   - Xu hướng nào đang suy giảm?
   - Thay đổi hành vi nào có thể ảnh hưởng tiêu cực?

4. DỰ BÁO 1-2 NĂM TỚI
   - Thị trường sẽ dịch chuyển theo hướng nào?

Chỉ phân tích dựa trên thông tin có trong bài viết.
Nếu không có đủ dữ liệu, ghi rõ "Chưa có đủ thông tin".
Trả lời bằng tiếng Việt, súc tích, có thể dùng ngay để ra quyết định kinh doanh."""

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "Bạn là chuyên gia phân tích thị trường Việt Nam."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content