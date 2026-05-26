export default function ProgressBar({ doneSteps, activeSteps }) {
    const allSteps = [
        { key: 'search', label: '🔍 Search Agent', desc: 'Tìm kiếm thông tin' },
        { key: 'trend', label: '📈 Trend Agent', desc: 'Phân tích xu hướng' },
        { key: 'competitor', label: '🏆 Competitor Agent', desc: 'Phân tích đối thủ' },
        { key: 'report', label: '📄 Report Agent', desc: 'Tổng hợp báo cáo' }
    ];
    return (
        <div className="card progress-card">
            <div className="card-header">
                <h3>Tiến trình xử lý</h3>
                <span>{doneSteps.length}/4 hoàn thành</span>
            </div>
            {allSteps.map((step, i) => {
                const done = doneSteps.includes(step.key);
                const active = !done && activeSteps.includes(step.key);
                const statusClass = done ? 'is-done' : active ? 'is-active' : 'is-idle';
                return (
                    <div key={step.key} className={`progress-step ${statusClass}`}>
                        <div className="progress-icon">
                            {done ? '✓' : active ? '⟳' : i + 1}
                        </div>
                        <div>
                            <div className="progress-label">{step.label}</div>
                            <div className="progress-desc">{step.desc}</div>
                        </div>
                        {active && <span className="status-pill">Đang chạy...</span>}
                        {done && <span className="status-pill done">Hoàn thành</span>}
                    </div>
                );
            })}
        </div>
    );
}