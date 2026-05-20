export default function ProgressBar({ doneSteps, activeStep }) {
    const allSteps = [
        { key: 'search', label: '🔍 Search Agent', desc: 'Tìm kiếm thông tin' },
        { key: 'trend', label: '📈 Trend Agent', desc: 'Phân tích xu hướng' },
        { key: 'competitor', label: '🏆 Competitor Agent', desc: 'Phân tích đối thủ' },
        { key: 'report', label: '📄 Report Agent', desc: 'Tổng hợp báo cáo' }
    ];
    return (
        <div style={styles.card}>
            <h3 style={styles.title}>⚙️ Tiến trình xử lý</h3>
            {allSteps.map((step, i) => {
                const done = doneSteps.includes(step.key);
                const active = !done && activeStep === step.key;
                return (
                    <div key={step.key} style={styles.step}>
                        <div style={{
                            ...styles.icon,
                            background: done ? '#52c41a' : active ? '#1890ff' : '#f0f0f0',
                            color: done || active ? '#fff' : '#bbb'
                        }}>
                            {done ? '✓' : active ? '⟳' : i + 1}
                        </div>
                        <div>
                            <div style={styles.stepLabel}>{step.label}</div>
                            <div style={styles.stepDesc}>{step.desc}</div>
                        </div>
                        {active && <span style={styles.badge}>Đang chạy...</span>}
                        {done && <span style={{ ...styles.badge, background: '#f6ffed', color: '#52c41a', border: '1px solid #b7eb8f' }}>Hoàn thành</span>}
                    </div>
                );
            })}
        </div>
    );
}

const styles = {
    card: {
        background: '#fff',
        borderRadius: 12,
        padding: 24,
        boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
        marginBottom: 24
    },
    title: { margin: '0 0 16px', fontSize: 16 },
    step: {
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '10px 0',
        borderBottom: '1px solid #f5f5f5'
    },
    icon: {
        width: 32, height: 32,
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 700,
        fontSize: 14,
        flexShrink: 0
    },
    stepLabel: { fontWeight: 600, fontSize: 14 },
    stepDesc: { fontSize: 12, color: '#888' },
    badge: {
        marginLeft: 'auto',
        background: '#e6f7ff',
        color: '#1890ff',
        border: '1px solid #91d5ff',
        padding: '2px 10px',
        borderRadius: 10,
        fontSize: 12
    }
};