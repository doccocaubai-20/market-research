import json
import asyncio
from openai import AsyncOpenAI
from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

async def validate_with_llm(topic: str, search_results: dict) -> bool:
    sources = search_results.get("sources", [])
    if not sources:
        return False

    context_parts = [
        search_results.get("overview", ""),
        search_results.get("trends", ""),
        search_results.get("competitors", "")
    ]
    context_text = "\n\n".join([part for part in context_parts if part])

    if not context_text:
        context_text = "\n".join([
            f"Title: {s.get('title')}\nSnippet: {s.get('snippet')}"
            for s in sources[:5]
        ])

    if context_text:
        third_len = max(1, len(context_text) // 3)
        context_text = context_text[:third_len]

    validator_prompt = f"""
    Bạn là Tác tử Thẩm định Ngữ nghĩa (Validator Agent). Nhiệm vụ của bạn là phân tích đoạn văn bản <context> được cào từ Internet về và đối chiếu với chủ đề nghiên cứu <topic>.

    <topic>
    {topic}
    </topic>

    <context>
    {context_text}
    </context>

    Hãy lập luận logic dựa trên tiêu chí sau:
    Nội dung trong <context> có thực sự chứng minh <topic> này là một thị trường/sản phẩm có thật, đang tồn tại trong thực tế kinh tế không? Hay đây chỉ là bài viết mang tính giả định, hư cấu, châm biếm, giải trí hoặc do AI tự nội suy, tự bịa ra nội dung (ví dụ: quy mô 0 USD, phân khúc khách hàng là động vật, ma trận SWOT cho sản phẩm không tưởng)?

    Trả về kết quả bắt buộc dưới cấu trúc JSON nghiêm ngặt sau:
    {{
        "status": "SUCCESS" hoặc "FAILED",
        "reason": "Lý do cụ thể tại sao bạn đưa ra kết luận này"
    }}
    Tuyệt đối không trả thêm bất kỳ lời thoại nào ngoài JSON.
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[{"role": "user", "content": validator_prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("DeepSeek returned empty content")
            res_data = json.loads(content)

            if res_data.get("status") == "FAILED":
                print(f"Phát hiện dữ liệu ảo giác từ Search AI: {res_data.get('reason')}")
                return False

            return True
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Lỗi hệ thống kiểm duyệt sau {max_retries} lần thử: {e}")
                return True
            print(f"Lỗi hệ thống kiểm duyệt (Lượt {attempt+1}/{max_retries}): {e}. Đang thử lại sau 2 giây...")
            await asyncio.sleep(2)
