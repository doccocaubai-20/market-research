import asyncio
import time
import json
from app.agents.orchestrator import run as run_multi
from app.agents.single_agent import run_single_agent as run_single

async def compare_agents(topic: str):
    print(f"=== TỪ KHÓA: {topic} ===")

    # 1. Test Multi-Agent
    print("\nĐang chạy Multi-Agent...")
    start_multi = time.time()
    res_multi = await run_multi(topic)
    time_multi = time.time() - start_multi

    # 2. Test Single-Agent
    print("\nĐang chạy Single-Agent...")
    start_single = time.time()
    res_single = await run_single(topic)
    time_single = time.time() - start_single

    # 3. Thống kê
    print("\n=== KẾT QUẢ SO SÁNH ===")
    print(f"Thời gian Multi-Agent:  {time_multi:.2f} giây")
    print(f"Thời gian Single-Agent: {time_single:.2f} giây")
    
    print(f"\nĐộ dài báo cáo Multi:  {len(res_multi.get('report', ''))} ký tự")
    print(f"Độ dài báo cáo Single: {len(res_single.get('report', ''))} ký tự")

    def _strip_raw_sources(payload: dict) -> dict:
        cleaned = dict(payload)
        details = cleaned.get("details")
        if isinstance(details, dict):
            cleaned["details"] = dict(details)
            search = cleaned["details"].get("search")
            if isinstance(search, dict):
                cleaned["details"]["search"] = dict(search)
                cleaned["details"]["search"]["sources"] = []
                cleaned["details"]["search"]["overview_sources"] = []
                cleaned["details"]["search"]["trends_sources"] = []
                cleaned["details"]["search"]["competitors_sources"] = []
        cleaned["sources"] = []
        return cleaned

    print("\n=== CHI TIẾT MULTI-AGENT (NO RAW SOURCES) ===")
    print(json.dumps(_strip_raw_sources(res_multi), ensure_ascii=False, indent=2))

    print("\n=== CHI TIẾT SINGLE-AGENT (NO RAW SOURCES) ===")
    print(json.dumps(_strip_raw_sources(res_single), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(compare_agents("Thị trường xe điện Việt Nam 2026"))