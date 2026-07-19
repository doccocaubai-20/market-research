from openai import AsyncOpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

async def generate_report(topic: str, trends: str, competitors: str, sources: list) -> dict:
    # 1. Trích xuất và chuẩn hóa danh sách URLs candidate để trả về ở output
    url_candidates = []
    for item in sources:
        if not isinstance(item, dict):
            if isinstance(item, str) and item.startswith("http"):
                url_candidates.append(item)
            continue
        for key in ("link", "redirect_link", "displayed_link", "source", "url", "html_url"):
            value = item.get(key)
            if value:
                url_candidates.append(value)
    source_list = list(dict.fromkeys(url_candidates))

    # 2. Lọc danh sách các nguồn có link thực tế (http) và loại bỏ trùng lặp link để truyền vào Prompt
    seen_links = set()
    valid_sources = []
    for item in sources:
        if not isinstance(item, dict):
            continue
        link = item.get("link") or item.get("url") or item.get("displayed_link")
        if link and link.startswith("http") and link not in seen_links and "example.com" not in link:
            seen_links.add(link)
            valid_sources.append(item)

    # Xây dựng chuỗi text chứa thông tin nguồn thực tế (tối đa 10 nguồn có link)
    sources_text = ""
    for idx, item in enumerate(valid_sources[:10], 1):
        title = item.get("title") or "Nguồn tin cậy từ Internet"
        link = item.get("link") or item.get("url") or item.get("displayed_link")
        sources_text += f"[{idx}] {title}: {link}\n"

    prompt = f"""Dựa trên các phân tích đầu vào và danh sách liên kết dưới đây về thị trường '{topic}':

<phan_tich_xu_huong>
{trends}
</phan_tich_xu_huong>

<phan_tich_doi_thu>
{competitors}
</phan_tich_doi_thu>

<danh_sach_nguon>
{sources_text}
</danh_sach_nguon>

Hãy tổng hợp thành một Báo cáo Cố vấn Chiến lược toàn diện. 

Báo cáo phải được viết và định dạng bằng mã HTML5 sạch (clean HTML, chỉ bắt đầu trực tiếp bằng các thẻ như <h1>, <h2>, <h3>, <p>, <ul>, <li>, <table>, <blockquote>, <strong>, <em>... Tuyệt đối KHÔNG chứa các thẻ bao quanh ngoài như <html>, <head>, <body>).

Cấu trúc nội dung báo cáo cần tuân thủ các phần sau (định dạng tiêu đề bằng thẻ <h1> hoặc <h2> phù hợp):

1. TÓM TẮT THỰC THI (EXECUTIVE SUMMARY)
- Viết 1 đoạn ngắn (4-6 câu) tóm gọn cơ hội lớn nhất, rủi ro chí mạng nhất, và khuyến nghị hành động.

2. TỔNG QUAN THỊ TRƯỜNG & XU HƯỚNG TIÊU DÙNG
- Trình bày mạch lạc các xu hướng chính và sự thay đổi trong hành vi khách hàng.
- Nêu rõ các phân khúc/nhóm nhu cầu nổi bật (nếu có trong dữ liệu).

3. CẢNH QUAN CẠNH TRANH
- Tóm tắt thế trận cạnh tranh (Ai dẫn đầu? Ai đang yếu thế?). Nhấn mạnh vào chiến lược lõi của họ.
- Nêu các “khoảng trống thị trường”/điểm yếu đối thủ nếu dữ liệu có.

4. ĐÁNH GIÁ CƠ HỘI VÀ RỦI RO (BẢNG SWOT NHANH)
- Hãy xây dựng bảng SWOT dưới dạng bảng HTML <table> để trình bày trực quan và chuyên nghiệp. Bảng gồm các cột: Tiêu chí, Chi tiết (Điểm mạnh, Điểm yếu, Cơ hội, Thách thức).

5. ĐỀ XUẤT CHIẾN LƯỢC GIA NHẬP
- Đưa ra 3-5 hành động cụ thể, khả thi cho nhà đầu tư dựa trên các lỗ hổng của đối thủ hoặc nhu cầu chưa được đáp ứng.

6. GIẢ ĐỊNH & LỖ HỔNG DỮ LIỆU
- Nêu rõ các giả định bắt buộc phải đặt ra do thiếu dữ liệu.
- Liệt kê 3-5 câu hỏi cần khảo sát thêm để ra quyết định đầu tư.

7. KẾT LUẬN
- Trình bày kết luận của bài báo cáo.

8. NGUỒN THAM KHẢO VÀ LIÊN KẾT TRỰC TUYẾN
- Liệt kê danh sách các nguồn tham khảo bằng danh sách <ul>.
- Mỗi nguồn tham khảo bắt buộc phải có thẻ liên kết HTML <a> chứa đường dẫn thực tế (href) lấy từ danh sách <danh_sach_nguon> để người dùng có thể click trực tiếp kiểm chứng.
- TUYỆT ĐỐI KHÔNG sử dụng link giả định, link không tồn tại hoặc "example.com". Bạn bắt buộc phải sao chép chính xác link tương ứng được cung cấp trong <danh_sach_nguon> để đưa vào thuộc tính href (ví dụ: <a href="đường_link_chính_xác_trong_danh_sách" target="_blank">[1] Tên nguồn tham khảo</a>). Nếu <danh_sach_nguon> trống, hãy bỏ qua không tạo mục 8 này.

**YÊU CẦU NGHIÊM NGẶT:**
1. KHÔNG sử dụng kiến thức bên ngoài, CHỈ tổng hợp từ dữ liệu trong hai thẻ <phan_tich_xu_huong> và <phan_tich_doi_thu>.
2. Không lặp lại y hệt nguyên văn các bản phân tích đầu vào, hãy "tổng hợp" và "chắt lọc" ý chính.
3. Báo cáo TRẢ VỀ PHẢI LÀ MÃ HTML TRỰC TIẾP, tuyệt đối không được bao bọc bởi các khối định dạng markdown như ```html ... ``` hay bất cứ ký tự bọc ngoài nào.
4. Văn phong khách quan, súc tích, chuyên nghiệp (Consulting style).
5. Ưu tiên viết đủ ý, sâu hơn trước khi kết luận ngắn gọn.
"""

    response = await client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "Bạn là Chuyên gia Tư vấn Chiến lược Cấp cao (Senior Management Consultant). Bạn xuất sắc trong việc chắt lọc thông tin phức tạp thành các hành động kinh doanh thực tiễn. Bạn phản hồi trực tiếp bằng mã HTML không bao bọc bởi markdown code blocks."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4, 
        max_tokens=12000
    )

    report_content = response.choices[0].message.content
    if report_content:
        report_content = report_content.strip()
        if report_content.startswith("```html"):
            report_content = report_content[7:]
        elif report_content.startswith("```"):
            report_content = report_content[3:]
        if report_content.endswith("```"):
            report_content = report_content[:-3]
        report_content = report_content.strip()

    return {
        "content": report_content,
        "sources": source_list
    }