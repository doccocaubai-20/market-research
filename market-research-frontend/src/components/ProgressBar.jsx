export default function ProgressBar({ doneSteps, activeSteps, progressPercent }) {
    const allSteps = [
        { key: 'search', label: '🔍 Search Agent', desc: 'Tìm kiếm thông tin' },
        { key: 'trend', label: '📈 Trend Agent', desc: 'Phân tích xu hướng' },
        { key: 'competitor', label: '🏆 Competitor Agent', desc: 'Phân tích đối thủ' },
        { key: 'report', label: '📄 Report Agent', desc: 'Tổng hợp báo cáo' }
    ];
    const clampedPercent = Math.max(0, Math.min(100, progressPercent ?? 0));
    const statusLabel = clampedPercent >= 100 ? 'hoàn thành' : 'đang xử lý';
    return (
        <div className="card progress-card">
            <div className="progress-top">
                <div>
                    <p className="progress-eyebrow">Orchestrator Loop</p>
                    <h3>Tiến trình xử lý</h3>
                </div>
                <div className="progress-percent">
                    <span>{clampedPercent}%</span>
                    <small>{statusLabel}</small>
                </div>
            </div>
            <div className="progress-orbit">
                <div className="progress-orbit-track">
                    <div className="progress-orbit-fill" style={{ width: `${clampedPercent}%` }} />
                </div>
                <div className="progress-orbit-glow" style={{ width: `${clampedPercent}%` }} />
            </div>
            <div className="progress-grid">
                {allSteps.map((step) => (
                    <div key={step.key} className="progress-agent">
                        <div className="agent-dot" />
                        <div className="agent-body">
                            <div className="agent-label">{step.label}</div>
                            <div className="agent-desc">{step.desc}</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}