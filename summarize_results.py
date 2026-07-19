import json
import os

def main():
    results_file = "evaluation_results.json"
    if not os.path.exists(results_file):
        print(f"Error: {results_file} not found.")
        return

    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    configs = ["single_agent", "baseline_2", "proposed"]
    stats = {cfg: {"total": 0, "success": 0, "latency_sum": 0, "rqs_sum": 0, "rqs_count": 0, "by_total": 0, "by_blocked": 0} for cfg in configs}

    # Group test cases by type
    groups = {}

    for case_id, case_data in data.items():
        group = case_data.get("group", "TC")
        groups[case_id] = group
        
        runs = case_data.get("runs", {})
        for config, run_res in runs.items():
            if config not in stats:
                continue
            
            stats[config]["total"] += 1
            stats[config]["latency_sum"] += run_res.get("latency", 0.0)
            
            flow_status = run_res.get("flow_status", "FAILED")
            if flow_status == "SUCCESS":
                stats[config]["success"] += 1
                
                # Check RQS score. Since user requested to ignore early runs where RQS was low due to no sources:
                # We can print RQS generally, but let's count RQS if it is > 0 (or if it exists)
                # Let's count all non-zero RQS scores to see quality after the fix, 
                # or just count RQS scores that were evaluated.
                rqs = run_res.get("rqs_score", 0)
                if rqs > 0:
                    stats[config]["rqs_sum"] += rqs
                    stats[config]["rqs_count"] += 1
            
            # SDR calculation for BY (Trick) cases
            if group == "BY":
                stats[config]["by_total"] += 1
                validator_status = run_res.get("validator_status", "SUCCESS")
                if validator_status == "FAILED" or flow_status in ["FAILED", "SEARCH_FAILED"]:
                    stats[config]["by_blocked"] += 1

    print("=" * 60)
    print(" BÁO CÁO TỔNG HỢP CHI TIẾT SỐ LIỆU THỰC NGHIỆM ")
    print("=" * 60)

    for config in configs:
        cfg_stats = stats[config]
        total = cfg_stats["total"]
        if total == 0:
            print(f"\n[CẤU HÌNH: {config.upper()}] Chưa có dữ liệu chạy.")
            continue
            
        success = cfg_stats["success"]
        sr = (success / total) * 100
        
        by_total = cfg_stats["by_total"]
        sdr = (cfg_stats["by_blocked"] / by_total) * 100 if by_total > 0 else 0
        
        avg_latency = cfg_stats["latency_sum"] / total
        avg_rqs = (cfg_stats["rqs_sum"] / cfg_stats["rqs_count"]) if cfg_stats["rqs_count"] > 0 else 0

        print(f"\n[CẤU HÌNH: {config.upper()}]")
        print(f"- Số kịch bản đã chạy: {total}")
        print(f"- Số lượt thành công (SUCCESS): {success}/{total} ({sr:.1f}%)")
        print(f"- Tỷ lệ chặn bẫy (SDR): {sdr:.1f}% ({cfg_stats['by_blocked']}/{by_total})")
        print(f"- Thời gian chạy trung bình (Latency): {avg_latency:.2f} giây")
        print(f"- Điểm RQS trung bình (Đã lọc bỏ case RQS=0): {avg_rqs:.1f}/100 (Dựa trên {cfg_stats['rqs_count']} case)")
    print("=" * 60)

if __name__ == "__main__":
    main()
