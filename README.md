# Multi-Agent Market Intelligence Automation

Dự án này nghiên cứu và phát triển một hệ thống đa tác tử (Multi-Agent System) chuyên biệt nhằm tự động hóa quy trình thu thập, phân tích và tổng hợp tri thức thị trường tiếng Việt từ nguồn Internet thời gian thực.

Hệ thống giải quyết triệt để các giới hạn của kiến trúc đơn tác tử (Single-Agent) truyền thống nhờ vào việc phân rã chức năng thành các tác tử chuyên trách, kết hợp cơ chế **Lightweight RAG** để triệt tiêu hiện tượng ảo giác thông tin (*hallucination*).

---

## Core Features

1. **Manager Agent:** Sử dụng mô hình ngôn ngữ lớn DeepSeek làm bộ não nhận thức, vận hành dựa trên vòng lặp **ReAct (Reasoning and Acting)** để tự động lập kế hoạch, rẽ nhánh logic và ủy quyền tác vụ dựa trên trạng thái tập trung (`System State`).
2. **Search Query Generator & Expansion:** Tiền xử lý truy vấn tìm kiếm trước khi gọi Search Agent. Tránh thay thế chủ đề gốc của người dùng, thực hiện tinh chỉnh chính tả, giữ nguyên thực thể, địa điểm, mốc thời gian và mở rộng các truy vấn phụ (overview, trend, competition) giúp tìm kiếm tối ưu.
3. **Kiểm soát bối cảnh bằng Lightweight RAG:** Loại bỏ các tầng Vector Database và Embedding cồng kềnh. Hệ thống đóng gói dữ liệu trực tuyến qua thẻ cấu trúc XML `<data>` để tạo ranh giới ngữ nghĩa nghiêm ngặt, ép LLM chỉ suy luận dựa trên bằng chứng thu thập thực tế.
4. **Báo cáo chuẩn hóa:** Tự động tổng hợp và render báo cáo chiến lược kinh doanh hoàn chỉnh dưới định dạng Markdown có cấu trúc 7 phần cố định, kèm danh sách URL nguồn trích dẫn minh bạch.

---

## System Architecture

```text
Manager Agent -> Search Agent (SearchQueryGenerator) -> (Trend Agent && Competitor Agent) -> Report Agent.
```
*Hệ thống giữ nguyên chủ đề gốc (original_topic) xuyên suốt quy trình để các tác tử chuyên trách phân tích và Validator kiểm chứng.*

## Cấu hình so sánh (Baselines)
1. **Baseline 1 (Single-Agent):** Chạy tuyến tính đơn giản (Search một lượt -> Tạo báo cáo).
2. **Baseline 2 (Without Validator):** Quy trình Multi-Agent đề xuất nhưng lược bỏ Validator Agent, chuyển tiếp trực tiếp kết quả tìm kiếm sang các tác tử phân tích.
3. **Baseline 3 (Agentic Single-Agent RAG):** Tác tử đơn chạy vòng lặp ReAct, tự quyết định truy vấn cào dữ liệu qua nhiều lượt và tự phản tư dừng sớm (ABORT) nếu phát hiện bẫy hư cấu.
4. **Proposed System (Proposed):** Hệ thống đa tác tử đề xuất hoàn chỉnh với SearchQueryGenerator, Validator kiểm duyệt sớm và song song hóa Trend/Competitor/Report Agents.

## Tech Stack

* **Backend:** Python 3.10+, FastAPI, Uvicorn, Asyncio, HTTPX
* **Frontend:** ReactJS, TailwindCSS, Axios
* **AI Model & API:** DeepSeek API (`deepseek-v4-flash`), SerpAPI (Google Search API)
* **Database:** MySQL 8.0, SQLAlchemy ORM

## Installation & Setup
--- 
### Backend
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Điền thông số env
uvicorn app.main:app --reload --port 8080
```

---
### Frontend
```bash
cd market-research-frontend
npm install
npm start
```