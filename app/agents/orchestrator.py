from app.agents.search_agent import search_market
from app.agents.trend_agent import analyze_trends
from app.agents.competitor_agent import analyze_competitors
from app.agents.report_agent import generate_report
def run(topic: str, callback=None) -> dict:

    def update(event: dict):
        print(event)
        if callback:
            callback(event)

    # Bước 1 — Tìm kiếm dữ liệu
    update({
        "agent": "search",
        "status": "running",
        "message": f"🔍 Đang tìm kiếm '{topic}'..."
    })

    search_results = search_market(topic)
    all_results = search_results.get("sources", [])
    overview_word_count = len(search_results.get("overview", "").split()) if search_results.get("overview") else 0
    trends_word_count = len(search_results.get("trends", "").split()) if search_results.get("trends") else 0
    competitors_word_count = len(search_results.get("competitors", "").split()) if search_results.get("competitors") else 0

    update({
        "agent": "search",
        "status": "done",
        "message": f"✅ Tổng {len(all_results)} kết quả",
        "output": {
            "total": len(all_results),
            "overview": overview_word_count,
            "trends": trends_word_count,
            "competitors": competitors_word_count
        }
    })

    # Bước 2 — Trend Agent
    update({
        "agent": "trend",
        "status": "running",
        "message": "📈 Đang phân tích xu hướng...",
        "input": f"Phân tích {len(search_results.get('trends_sources', []))} nguồn về xu hướng"
    })
    trends = analyze_trends(topic, search_results.get("trends", ""))
    update({
        "agent": "trend",
        "status": "done",
        "message": "✅ Phân tích xu hướng hoàn thành",
        "output": trends
    })

    # Bước 3 — Competitor Agent
    update({
        "agent": "competitor",
        "status": "running",
        "message": "🏆 Đang phân tích đối thủ cạnh tranh...",
        "input": f"Phân tích {len(search_results.get('competitors_sources', []))} nguồn về đối thủ"
    })
    competitors = analyze_competitors(topic, search_results.get("competitors", ""))
    update({
        "agent": "competitor",
        "status": "done",
        "message": "✅ Phân tích đối thủ hoàn thành",
        "output": competitors
    })

    # Bước 4 — Report Agent
    update({
        "agent": "report",
        "status": "running",
        "message": "📄 Đang tổng hợp báo cáo cuối cùng...",
        "input": {
            "trends_length": len(trends),
            "competitors_length": len(competitors)
        }
    })
    report = generate_report(topic, trends, competitors, all_results)
    update({
        "agent": "report",
        "status": "done",
        "message": "✅ Báo cáo hoàn thành!",
        "output": report["content"][:200] + "..."
    })

    return {
        "topic": topic,
        "report": report["content"],
        "sources": report["sources"],
        "details": {
            "search": search_results,
            "trends": trends,
            "competitors": competitors
        }
    }