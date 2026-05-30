uvicorn app.main:app --reload --port 8080
# Multi-Agent Market Intelligence Automation

Dự án này nghiên cứu và phát triển một hệ thống đa tác tử (Multi-Agent System) chuyên biệt nhằm tự động hóa quy trình thu thập, phân tích và tổng hợp tri thức thị trường tiếng Việt từ nguồn Internet thời gian thực. 

Hệ thống giải quyết triệt để các giới hạn của kiến trúc đơn tác tử (Single-Agent) truyền thống nhờ vào việc phân rã chức năng thành các tác tử chuyên trách, kết hợp cơ chế **Lightweight RAG** để triệt tiêu hiện tượng ảo giác thông tin (*hallucination*).

---

## Core Features

1. **Manager Agent:** Sử dụng mô hình ngôn ngữ lớn DeepSeek làm bộ não nhận thức, vận hành dựa trên vòng lặp **ReAct (Reasoning and Acting)** để tự động lập kế hoạch, rẽ nhánh logic và ủy quyền tác vụ dựa trên trạng thái tập trung (`System State`).
2. **Query Reformulation:** Khi dữ liệu tìm kiếm bị trống (`SEARCH_FAILED`), Manager Agent tự động phản tư, bóc tách lỗi và tái cấu trúc từ khóa nghiên cứu thông minh hơn (`new_topic`) để tái vận hành luồng search dữ liệu theo thời gian thực mà không làm crash hệ thống.
3. **Kiểm soát bối cảnh bằng Lightweight RAG:** Loại bỏ các tầng Vector Database và Embedding cồng kềnh. Hệ thống đóng gói dữ liệu trực tuyến qua thẻ cấu trúc XML `<data>` để tạo ranh giới ngữ nghĩa nghiêm ngặt, ép LLM chỉ suy luận dựa trên bằng chứng thu thập thực tế.
4. **Báo cáo chuẩn hóa:** Tự động tổng hợp và render báo cáo chiến lược kinh doanh hoàn chỉnh dưới định dạng Markdown có cấu trúc 7 phần cố định, kèm danh sách URL nguồn trích dẫn minh bạch.

---

## System Architecture

Manager Agent -> Search Agent -> (Trend Agent && Competitor Agent) -> Report Agent.
                              -> || Query Reformulation.

## Tech Stack

* **Backend:** Python 3.10+, FastAPI, Uvicorn, Asyncio, HTTPX
* **Frontend:** ReactJS, TailwindCSS, Axios
* **AI Model & API:** DeepSeek API (`deepseek-v4-flash`), SerpAPI (Google Search API)
* **Database:** MySQL 8.0, SQLAlchemy ORM

## Installation & Setup
--- 
Backend
python -bin venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
// Điền thông số env
uvicorn main:app --reload --port 8000

---
Frontend

cd market-research-frontend
npm install
npm start