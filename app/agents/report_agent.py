from openai import AsyncOpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

async def generate_report(topic: str, trends: str, competitors: str, sources: list) -> dict:

    prompt = f"""Dựa trên các phân tích đầu vào dưới đây về thị trường '{topic}':

<phan_tich_xu_huong>
{trends}
</phan_tich_xu_huong>

<phan_tich_doi_thu>
{competitors}
</phan_tich_doi_thu>

Hãy tổng hợp thành một Báo cáo Cố vấn Chiến lược toàn diện. Báo cáo cần tuân thủ cấu trúc Markdown sau:

**1. TÓM TẮT THỰC THI (EXECUTIVE SUMMARY)**
- Viết 1 đoạn ngắn (4-6 câu) tóm gọn cơ hội lớn nhất, rủi ro chí mạng nhất, và khuyến nghị hành động.

**2. TỔNG QUAN THỊ TRƯỜNG & XU HƯỚNG TIÊU DÙNG**
- Trình bày mạch lạc các xu hướng chính và sự thay đổi trong hành vi khách hàng.
- Nêu rõ các phân khúc/nhóm nhu cầu nổi bật (nếu có trong dữ liệu).

**3. CẢNH QUAN CẠNH TRANH**
- Tóm tắt thế trận cạnh tranh (Ai dẫn đầu? Ai đang yếu thế?). Nhấn mạnh vào chiến lược lõi của họ.
- Nêu các “khoảng trống thị trường”/điểm yếu đối thủ nếu dữ liệu có.

**4. ĐÁNH GIÁ CƠ HỘI VÀ RỦI RO (SWOT NHANH)**
- Trình bày dạng Bullet point rõ ràng các cơ hội thâm nhập và rủi ro cần phòng tránh.

**5. ĐỀ XUẤT CHIẾN LƯỢC GIA NHẬP**
- Đưa ra 3-5 hành động cụ thể, khả thi cho nhà đầu tư dựa trên các lỗ hổng của đối thủ hoặc nhu cầu chưa được đáp ứng.

**6. GIẢ ĐỊNH & LỖ HỔNG DỮ LIỆU**
- Nêu rõ các giả định bắt buộc phải đặt ra do thiếu dữ liệu.
- Liệt kê 3-5 câu hỏi cần khảo sát thêm để ra quyết định đầu tư.
**7. KẾT LUẬN**
- Trình bày kết luận của bài báo cáo.

**YÊU CẦU NGHIÊM NGẶT:**
1. KHÔNG sử dụng kiến thức bên ngoài, CHỈ tổng hợp từ dữ liệu trong hai thẻ <phan_tich_xu_huong> và <phan_tich_doi_thu>.
2. Không lặp lại y hệt nguyên văn các bản phân tích đầu vào, hãy "tổng hợp" và "chắt lọc" ý chính.
3. Văn phong khách quan, súc tích, chuyên nghiệp (Consulting style).
4. Ưu tiên viết đủ ý, sâu hơn trước khi kết luận ngắn gọn.
"""

    response = await client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "Bạn là Chuyên gia Tư vấn Chiến lược Cấp cao (Senior Management Consultant). Bạn xuất sắc trong việc chắt lọc thông tin phức tạp thành các hành động kinh doanh thực tiễn."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4, 
        max_tokens=12000
    )

    report_content = response.choices[0].message.content

    url_candidates = []
    for item in sources:
        if not isinstance(item, dict):
            continue
        for key in ("link", "redirect_link", "displayed_link", "source", "url", "html_url"):
            value = item.get(key)
            if value:
                url_candidates.append(value)
    source_list = list(dict.fromkeys(url_candidates))

    return {
        "content": report_content,
        "sources": source_list
    }