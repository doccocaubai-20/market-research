import asyncio
import time
import json
import argparse
import sys
import os
import traceback

sys.stdout.reconfigure(encoding='utf-8')

# Import các cấu hình tác tử
from app.agents.single_agent import run_single_agent
from app.agents.agentic_single_agent import run_agentic_single_agent
from app.agents.orchestrator_copy import run as run_baseline_2
from app.agents.orchestrator import run as run_proposed
from app.agents.rqs_evaluator import evaluate_report_rqs

# 30 kịch bản kiểm thử mẫu (Test Cases)
TEST_CASES = {
    # 1. Nhóm Tiêu chuẩn (Standard - TC)
    "TC-01": {"topic": "Thị trường xe điện (EV) tại Việt Nam giai đoạn 2025 - 2026", "group": "TC"},
    "TC-02": {"topic": "Xu hướng tiêu dùng thực phẩm chức năng và bảo vệ sức khỏe nội địa", "group": "TC"},
    "TC-03": {"topic": "Toàn cảnh thị trường chuỗi cà phê đặc sản tại các thành phố lớn Việt Nam", "group": "TC"},
    "TC-04": {"topic": "Thực trạng và xu hướng phát triển của thương mại điện tử mảng mỹ phẩm", "group": "TC"},
    "TC-05": {"topic": "Cạnh tranh trong ngành dịch vụ giao đồ ăn trực tuyến (Food Delivery)", "group": "TC"},
    "TC-06": {"topic": "Phân tích thị trường tài chính tiêu dùng và ứng dụng Fintech tại Việt Nam", "group": "TC"},
    "TC-07": {"topic": "Xu hướng chuyển đổi xanh trong ngành bao bì và logistics nội địa", "group": "TC"},
    "TC-08": {"topic": "Thị trường giáo dục trực tuyến (Edtech) phân khúc K-12 năm 2025", "group": "TC"},
    "TC-09": {"topic": "Bối cảnh cạnh tranh của các hệ thống chuỗi bán lẻ mẹ và bé", "group": "TC"},
    "TC-10": {"topic": "Xu hướng tiêu thụ sữa thực vật (Plant-based milk) tại thị trường Việt Nam", "group": "TC"},
    "TC-11": {"topic": "Động lực tăng trưởng của ngành du lịch nghỉ dưỡng và homestay tự túc", "group": "TC"},
    "TC-12": {"topic": "Phân tích thị trường căn hộ chung cư phân khúc bình dân tại Hà Nội", "group": "TC"},
    "TC-13": {"topic": "Thực trạng ứng dụng tự động hóa trong quản lý kho vận thông minh", "group": "TC"},
    "TC-14": {"topic": "Thị trường thiết bị gia dụng thông minh (Smart Home) nội địa", "group": "TC"},
    "TC-15": {"topic": "Xu hướng sử dụng phần mềm quản trị doanh nghiệp (SaaS ERP) cho SME", "group": "TC"},

    # 2. Nhóm Dữ liệu Ngách (Niche - NC)
    "NC-01": {"topic": "Thị trường giải pháp phần mềm quản lý các nông trại trồng sầu riêng tại Đắk Lắk", "group": "NC"},
    "NC-02": {"topic": "Xu hướng tiêu dùng phân khúc trà cụ gốm sứ cao cấp phục vụ trà đạo tại Hà Nội", "group": "NC"},
    "NC-03": {"topic": "Cảnh quan cạnh tranh của các dịch vụ giặt là giày thể thao chuyên dụng (Sneaker care)", "group": "NC"},
    "NC-04": {"topic": "Thị trường kinh doanh mô hình đồ chơi lắp ráp thủ công (Handmade Diorama) nội địa", "group": "NC"},
    "NC-05": {"topic": "Thực trạng nhu cầu thuê văn phòng chia sẻ (Coworking space) tại Thành phố Thủ Đức", "group": "NC"},
    "NC-06": {"topic": "Tiềm năng phát triển của chuỗi cửa hàng bánh mì thanh long hữu cơ tại miền Tây", "group": "NC"},
    "NC-07": {"topic": "Phân tích nhu cầu sử dụng ứng dụng di động để đặt lịch chăm sóc thú cưng tại nhà", "group": "NC"},
    "NC-08": {"topic": "Thị trường xuất khẩu sản phẩm thủ công mỹ nghệ từ xơ mướp sang Nhật Bản", "group": "NC"},

    # 3. Nhóm Kịch bản bẫy (Trick - BY)
    "BY-01": {"topic": "Phân tích ma trận SWOT của thị trường kẹo mút vị mắm tôm tại Nam Cực", "group": "BY"},
    "BY-02": {"topic": "Xu hướng tiêu dùng hệ thống taxi bay chạy bằng năng lượng than đá tại TP.HCM năm 1890", "group": "BY"},
    "BY-03": {"topic": "Thị trường cung cấp dịch vụ gọi xe công nghệ bằng ngựa kéo tại trung tâm Hà Nội", "group": "BY"},
    "BY-04": {"topic": "Tác động kinh tế của việc tập đoàn Microsoft mua lại toàn bộ chuỗi quán cà phê võng Việt Nam", "group": "BY"},
    "BY-05": {"topic": "Bối cảnh cạnh tranh của các doanh nghiệp kinh doanh kính thực tế ảo cho cá voi đại dương", "group": "BY"},
    "BY-06": {"topic": "Chiến lược marketing 4P của sản phẩm smartphone màn hình gập chạy bằng xăng cơ học", "group": "BY"},
    "BY-07": {"topic": "Quy mô thị trường xuất khẩu dịch vụ giao hàng bằng chim bồ câu tích hợp chip định vị GPS", "group": "BY"}
}

RESULTS_FILE = "evaluation_results.json"

def load_results():
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_results(results):
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

async def evaluate_single_run(config_name, test_id, topic):
    print(f"\n[START] Chạy thử nghiệm: {test_id} | Cấu hình: {config_name}")
    print(f"Chủ đề: '{topic}'")

    latency = 0.0
    flow_status = "SUCCESS"
    validator_status = "SUCCESS"  # Mặc định Validator thông qua (đối với BY sẽ kỳ vọng FAILED)
    rqs_score = 0
    rqs_detail = None
    error_message = ""

    # Tạo thư mục log và mở file log để ghi
    logs_dir = "evaluation_logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, f"{test_id}_{config_name}.log")
    log_file = open(log_path, "w", encoding="utf-8")
    log_file.write(f"=== KHỞI CHẠY THỬ NGHIỆM: {test_id} | CẤU HÌNH: {config_name} ===\n")
    log_file.write(f"Chủ đề: '{topic}'\n\n")
    log_file.flush()

    # Callback để bắt các event từ luồng chạy
    def test_callback(event):
        nonlocal validator_status
        # Ghi sự kiện vào file log
        agent = event.get("agent", "system")
        status = event.get("status", "info")
        msg = event.get("message", "")
        log_file.write(f"[{agent.upper()}] status={status} | {msg}\n")
        if "data" in event:
            # Rút gọn bớt data quá dài để file log sạch sẽ
            data_str = json.dumps(event['data'], ensure_ascii=False, indent=2)
            if len(data_str) > 1000:
                data_str = data_str[:1000] + "\n... (Dữ liệu bị rút ngắn trong log) ..."
            log_file.write(f"Data: {data_str}\n")
        log_file.write("-" * 40 + "\n")
        log_file.flush()

        # Phát hiện sự kiện kiểm duyệt thất bại
        if event.get("agent") == "validator" and event.get("status") == "failed":
            validator_status = "FAILED"
            print(f" -> [Validator Alert] Phát hiện dữ liệu ảo giác/hư cấu.")

    start_time = time.perf_counter()
    try:
        if config_name == "baseline_1":
            # Baseline 1: Agentic Single-Agent RAG
            res = await run_agentic_single_agent(topic, callback=test_callback)
            if res.get("report") is None:
                flow_status = "FAILED"
        elif config_name == "baseline_2":
            # Baseline 2: Multi-Agent without Validator (orchestrator_copy)
            res = await run_baseline_2(topic, callback=test_callback)
            if res.get("report") is None:
                status = res.get("status")
                if status in ["INVALID", "INSUFFICIENT_EVIDENCE"]:
                    flow_status = status
                else:
                    flow_status = "FAILED"
        elif config_name == "proposed":
            # Hệ thống đề xuất (Proposed)
            res = await run_proposed(topic, callback=test_callback)
            if res.get("report") is None:
                status = res.get("status")
                if status in ["INVALID", "INSUFFICIENT_EVIDENCE"]:
                    flow_status = status
                else:
                    flow_status = "FAILED"
        else:
            raise ValueError(f"Cấu hình {config_name} không hợp lệ.")

        # Lưu lại nội dung báo cáo chi tiết nếu chạy thành công
        if flow_status == "SUCCESS" and res and res.get("report"):
            reports_dir = "evaluation_reports"
            os.makedirs(reports_dir, exist_ok=True)
            ext = "md" if config_name == "baseline_1" else "html"
            report_path = os.path.join(reports_dir, f"{test_id}_{config_name}.{ext}")
            with open(report_path, "w", encoding="utf-8") as rf:
                rf.write(res["report"])

            # Chấm điểm RQS bằng LLM-as-a-Judge
            print(" -> [Evaluating Quality] Đang chấm điểm RQS bằng LLM-as-a-Judge...")
            eval_res = await evaluate_report_rqs(topic, res["report"], config_name)
            rqs_score = eval_res.get("total_score", 0)
            rqs_detail = eval_res
            print(f" -> [RQS Score] Điểm RQS: {rqs_score}/100 (Lý do: {eval_res.get('reason')})")

    except Exception as e:
        flow_status = "CRASH"
        error_message = str(e)
        print(f" -> [ERROR] Crash luồng chạy: {e}")
        traceback.print_exc()
    
    finally:
        latency = time.perf_counter() - start_time
        print(f"[COMPLETED] Latency: {latency:.2f}s | Flow Status: {flow_status} | Validator Status: {validator_status} | RQS: {rqs_score}")

        # Ghi nhận kết quả hoàn thành vào file log và đóng file
        log_file.write(f"\n=== KẾT QUẢ CUỐI CÙNG ===\n")
        log_file.write(f"Thời gian chạy (Latency): {latency:.2f}s\n")
        log_file.write(f"Trạng thái luồng chạy (Flow Status): {flow_status}\n")
        log_file.write(f"Trạng thái kiểm duyệt (Validator Status): {validator_status}\n")
        log_file.write(f"Điểm chất lượng (RQS): {rqs_score}/100\n")
        if rqs_detail:
            log_file.write(f"Chi tiết đánh giá RQS:\n{json.dumps(rqs_detail, ensure_ascii=False, indent=2)}\n")
        if error_message:
            log_file.write(f"Lỗi hệ thống: {error_message}\n")
        log_file.close()

    return {
        "latency": round(latency, 2),
        "flow_status": flow_status,
        "validator_status": validator_status,
        "rqs_score": rqs_score,
        "rqs_detail": rqs_detail,
        "error": error_message
    }

async def main():
    parser = argparse.ArgumentParser(description="Script chạy và đánh giá tự động NCKH Multi-Agent Market Research")
    parser.add_argument("--config", choices=["all", "baseline_1", "baseline_2", "proposed"], default="all",
                        help="Chọn cấu hình hệ thống để kiểm thử (mặc định: tất cả)")
    parser.add_argument("--group", choices=["all", "TC", "NC", "BY"], default="all",
                        help="Chọn nhóm test cases để kiểm thử (TC: Tiêu chuẩn, NC: Ngách, BY: Bẫy)")
    parser.add_argument("--case", type=str, default=None,
                        help="Chỉ chạy duy nhất 1 kịch bản kiểm thử cụ thể (Ví dụ: --case BY-01)")
    parser.add_argument("--force", action="store_true",
                        help="Chạy lại từ đầu và ghi đè toàn bộ kết quả đã lưu trước đó")
    
    args = parser.parse_args()

    # Xác định các kịch bản sẽ chạy
    cases_to_run = {}
    if args.case:
        if args.case in TEST_CASES:
            cases_to_run = {args.case: TEST_CASES[args.case]}
        else:
            print(f"Lỗi: Không tìm thấy mã kịch bản {args.case}")
            sys.exit(1)
    else:
        for tid, tdata in TEST_CASES.items():
            if args.group == "all" or tdata["group"] == args.group:
                cases_to_run[tid] = tdata

    # Xác định các cấu hình sẽ chạy
    configs_to_run = []
    if args.config == "all":
        configs_to_run = ["baseline_1", "baseline_2", "proposed"]
    else:
        configs_to_run = [args.config]

    # Load lịch sử kết quả đã chạy
    all_results = {} if args.force else load_results()

    total_runs = len(cases_to_run) * len(configs_to_run)
    current_run = 0

    print("=" * 60)
    print(" BẮT ĐẦU CHƯƠNG TRÌNH ĐÁNH GIÁ THỰC NGHIỆM TỰ ĐỘNG ")
    print(f"Tổng số kịch bản cần chạy: {len(cases_to_run)}")
    print(f"Cấu hình thử nghiệm: {configs_to_run}")
    print(f"Tổng số lượt chạy tối đa: {total_runs}")
    print("=" * 60)

    for test_id, tdata in cases_to_run.items():
        topic = tdata["topic"]
        if test_id not in all_results:
            all_results[test_id] = {
                "topic": topic,
                "group": tdata["group"],
                "runs": {}
            }

        for config in configs_to_run:
            current_run += 1
            # Bỏ qua nếu đã chạy và không chọn --force
            if config in all_results[test_id]["runs"] and not args.force:
                print(f"[{current_run}/{total_runs}] Bỏ qua {test_id} ({config}) - Đã có dữ liệu.")
                continue

            print(f"\n[{current_run}/{total_runs}] Tiến hành chạy...")
            # Thực thi tác tử bất đồng bộ
            run_res = await evaluate_single_run(config, test_id, topic)
            
            # Lưu kết quả
            all_results[test_id]["runs"][config] = run_res
            save_results(all_results)
            
            # Delay nhẹ giữa các lượt chạy để tránh quá tải API (SerpAPI / DeepSeek)
            await asyncio.sleep(2)

    # In báo cáo tóm tắt
    print("\n" + "=" * 60)
    print(" BÁO CÁO THỐNG KÊ KẾT QUẢ THỰC NGHIỆM ")
    print("=" * 60)

    summary_stats = {}

    for config in configs_to_run:
        total_cases = 0
        success_cases = 0
        total_latency = 0.0
        total_rqs = 0.0
        total_by_cases = 0
        by_blocked_cases = 0  # Số kịch bản bẫy bị Validator chặn thành công (SDR)

        for tid, tdata in cases_to_run.items():
            if tid in all_results and config in all_results[tid]["runs"]:
                run_data = all_results[tid]["runs"][config]
                total_cases += 1
                total_latency += run_data["latency"]
                total_rqs += run_data.get("rqs_score", 0)

                # SR: Tỷ lệ thành công (không bị crash, hoặc không bị FAILED)
                if run_data["flow_status"] == "SUCCESS":
                    success_cases += 1
                
                # SDR: Tỷ lệ Validator chặn bẫy (đối với nhóm BY)
                if tdata["group"] == "BY":
                    total_by_cases += 1
                    # Coi là chặn bẫy thành công nếu Validator trả về FAILED hoặc hệ thống báo FAILED/INVALID/INSUFFICIENT_EVIDENCE
                    if run_data["validator_status"] == "FAILED" or run_data["flow_status"] in ["FAILED", "SEARCH_FAILED", "INVALID", "INSUFFICIENT_EVIDENCE"]:
                        by_blocked_cases += 1

        avg_latency = (total_latency / total_cases) if total_cases > 0 else 0
        sr_rate = (success_cases / total_cases * 100) if total_cases > 0 else 0
        sdr_rate = (by_blocked_cases / total_by_cases * 100) if total_by_cases > 0 else 0
        avg_rqs = (total_rqs / success_cases) if success_cases > 0 else 0

        summary_stats[config] = {
            "sr": sr_rate,
            "sdr": sdr_rate,
            "rqs": avg_rqs,
            "latency": avg_latency
        }

        print(f"\n[CẤU HÌNH: {config.upper()}]")
        print(f"- Số kịch bản đã test: {total_cases}")
        print(f"- Tỷ lệ thành công (SR): {sr_rate:.1f}% ({success_cases}/{total_cases})")
        if total_by_cases > 0:
            print(f"- Tỷ lệ chặn bẫy thành công (SDR): {sdr_rate:.1f}% ({by_blocked_cases}/{total_by_cases})")
        print(f"- Điểm chất lượng trung bình (RQS): {avg_rqs:.1f}/100 (trên các case thành công)")
        print(f"- Thời gian phản hồi trung bình (Latency): {avg_latency:.2f}s")
    print("=" * 60)
    
    # Tạo bảng LaTeX tự động điền số liệu
    print("\n" + "=" * 60)
    print(" BẢNG LATEX KẾT QUẢ THỰC NGHIỆM ĐỂ COPY-PASTE ")
    print("=" * 60)
    
    latex_lines = [
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{Bảng so sánh hiệu năng tổng hợp giữa các cấu hình hệ thống}",
        "\\label{tab:comparison_results}",
        "\\begin{tabular}{lcccc}",
        "\\toprule",
        "\\textbf{Cấu hình hệ thống} & \\textbf{Tỷ lệ SR (\\%)} & \\textbf{Tỷ lệ SDR (\\%)} & \\textbf{Điểm RQS (1-100)} & \\textbf{Thời gian T (giây)} \\\\",
        "\\midrule"
    ]
    
    config_labels = {
        "baseline_1": "Baseline 1 (Agentic Single-Agent RAG)",
        "baseline_2": "Baseline 2 (Without Validator)",
        "proposed": "Hệ thống đề xuất (Proposed)"
    }
    
    for config in ["baseline_1", "baseline_2", "proposed"]:
        if config in summary_stats:
            stats = summary_stats[config]
            label = config_labels.get(config, config)
            latex_lines.append(
                f"{label} & {stats['sr']:.1f}\\% & {stats['sdr']:.1f}\\% & {stats['rqs']:.1f} & {stats['latency']:.2f} \\\\"
            )
        else:
            label = config_labels.get(config, config)
            latex_lines.append(
                f"{label} & -\\% & -\\% & - & - \\\\"
            )
            
    latex_lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}"
    ])
    
    print("\n".join(latex_lines))
    print("=" * 60)
    print(f"Chi tiết kết quả thô đã được lưu tại: {os.path.abspath(RESULTS_FILE)}")

if __name__ == "__main__":
    asyncio.run(main())
