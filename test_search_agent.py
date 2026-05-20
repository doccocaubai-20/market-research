import json
from app.agents.search_agent import search_market


def main():
    topic = "thi truong ca phe Viet Nam"
    results = search_market(topic)
    overview_count = len(results.get("overview", "").splitlines()) if results.get("overview") else 0
    trends_count = len(results.get("trends", "").splitlines()) if results.get("trends") else 0
    competitors_count = len(results.get("competitors", "").splitlines()) if results.get("competitors") else 0
    print(f"overview_text_lines: {overview_count}")
    print(f"trends_text_lines: {trends_count}")
    print(f"competitors_text_lines: {competitors_count}")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
