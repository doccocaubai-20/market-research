from openai import OpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

# def generate_report(topic: str, trends: str, competitors: str, sources: list) -> dict:
#     """
#     Tổng hợp tất cả thành báo cáo hoàn chỉnh
#     """
#     prompt = f"""Bạn là chuyên gia tư vấn kinh doanh.
# Tổng hợp báo cáo nghiên cứu thị trường về: {topic}

# PHÂN TÍCH XU HƯỚNG:
# {trends}

# PHÂN TÍCH ĐỐI THỦ:
# {competitors}

# Hãy viết báo cáo hoàn chỉnh gồm:

# 1. TỔNG QUAN THỊ TRƯỜNG
# 2. XU HƯỚNG TIÊU DÙNG  
# 3. PHÂN TÍCH ĐỐI THỦ CẠNH TRANH
# 4. CƠ HỘI VÀ RỦI RO
# 5. ĐỀ XUẤT CHIẾN LƯỢC

# Viết bằng tiếng Việt, chuyên nghiệp, có số liệu cụ thể nếu có."""

#     response = client.chat.completions.create(
#         model=DEEPSEEK_MODEL,
#         messages=[
#             {"role": "system", "content": "Bạn là chuyên gia tư vấn kinh doanh cấp cao."},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.3,
#         max_tokens=10000
#     )

#     report_content = response.choices[0].message.content

#     # Lấy danh sách nguồn tham khảo
#     source_list = list(set([s["link"] for s in sources if s.get("link")]))

#     return {
#         "content": report_content,
#         "sources": source_list[:10]  
#     }

def generate_report(topic: str, trends: str, competitors: str, sources: list) -> dict:
    """
    Tổng hợp tất cả thành báo cáo hoàn chỉnh (Đã tối ưu Prompt & Logic)
    """
    prompt = f"""Dựa trên các phân tích đầu vào dưới đây về thị trường '{topic}':

<phan_tich_xu_huong>
{trends}
</phan_tich_xu_huong>

<phan_tich_doi_thu>
{competitors}
</phan_tich_doi_thu>

Hãy tổng hợp thành một Báo cáo Cố vấn Chiến lược toàn diện. Báo cáo cần tuân thủ cấu trúc Markdown sau:

**1. TÓM TẮT THỰC THI (EXECUTIVE SUMMARY)**
- Viết 1 đoạn ngắn (3-4 câu) tóm gọn cơ hội lớn nhất và rủi ro chí mạng nhất của thị trường này.

**2. TỔNG QUAN THỊ TRƯỜNG & XU HƯỚNG TIÊU DÙNG**
- Trình bày mạch lạc các xu hướng chính và sự thay đổi trong hành vi khách hàng.

**3. CẢNH QUAN CẠNH TRANH**
- Tóm tắt thế trận cạnh tranh (Ai dẫn đầu? Ai đang yếu thế?). Nhấn mạnh vào chiến lược lõi của họ.

**4. ĐÁNH GIÁ CƠ HỘI VÀ RỦI RO (SWOT NHANH)**
- Trình bày dạng Bullet point rõ ràng các cơ hội thâm nhập và rủi ro cần phòng tránh.

**5. ĐỀ XUẤT CHIẾN LƯỢC GIA NHẬP**
- Đưa ra 2-3 hành động cụ thể, khả thi cho nhà đầu tư dựa trên các lỗ hổng của đối thủ hoặc nhu cầu chưa được đáp ứng.

**YÊU CẦU NGHIÊM NGẶT:**
1. KHÔNG sử dụng kiến thức bên ngoài, CHỈ tổng hợp từ dữ liệu trong hai thẻ <phan_tich_xu_huong> và <phan_tich_doi_thu>.
2. Không lặp lại y hệt nguyên văn các bản phân tích đầu vào, hãy "tổng hợp" và "chắt lọc" ý chính.
3. Văn phong khách quan, súc tích, chuyên nghiệp (Consulting style).
"""

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "Bạn là Chuyên gia Tư vấn Chiến lược Cấp cao (Senior Management Consultant). Bạn xuất sắc trong việc chắt lọc thông tin phức tạp thành các hành động kinh doanh thực tiễn."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3, 
        max_tokens=8196
    )

    report_content = response.choices[0].message.content

    # Thêm kiểm tra kiểu dữ liệu dict để tránh lỗi nếu danh sách sources chứa định dạng lạ
    source_list = list(set([s["link"] for s in sources if isinstance(s, dict) and s.get("link")]))

    return {
        "content": report_content,
        "sources": source_list[:10]  
    }