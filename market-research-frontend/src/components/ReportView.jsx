import { useState } from 'react';

export default function ReportView({ topic, report, sources, details }) {
    const [activeTab, setActiveTab] = useState('report');

    if (!report) return null;

    const tabs = [
        { key: 'report', label: '📄 Báo cáo' },
        { key: 'trends', label: '📈 Xu hướng' },
        { key: 'competitors', label: '🏆 Đối thủ' },
        { key: 'sources', label: '🔗 Nguồn' }
    ];

    const handleExportPDF = () => {
        const printContent = document.getElementById('report-content');
        const originalBody = document.body.innerHTML;
        document.body.innerHTML = printContent.innerHTML;
        window.print();
        document.body.innerHTML = originalBody;
        window.location.reload();
    };

    const renderReport = (text) => {
        return text.split('\n').map((line, i) => {
            if (line.startsWith('# ')) return <h1 key={i} style={styles.h1}>{line.slice(2)}</h1>;
            if (line.startsWith('## ')) return <h2 key={i} style={styles.h2}>{line.slice(3)}</h2>;
            if (line.startsWith('### ')) return <h3 key={i} style={styles.h3}>{line.slice(4)}</h3>;
            if (line.startsWith('- ') || line.startsWith('* ')) {
                return <li key={i} style={styles.li}>{line.slice(2).replace(/\*\*(.*?)\*\*/g, '$1')}</li>;
            }
            if (line.trim() === '') return <br key={i} />;
            return <p key={i} style={styles.p}>{line.replace(/\*\*(.*?)\*\*/g, '$1')}</p>;
        });
    };

    return (
        <div style={styles.card}>
            <div style={styles.header}>
                <div>
                    <h2 style={styles.title}>📄 {topic}</h2>
                    <span style={styles.date}>
                        {new Date().toLocaleDateString('vi-VN', {
                            day: '2-digit', month: '2-digit', year: 'numeric',
                            hour: '2-digit', minute: '2-digit'
                        })}
                    </span>
                </div>
                <button
                    onClick={() => navigator.clipboard.writeText(report)}
                    style={styles.copyBtn}
                >
                    📋 Copy
                </button>
                <button onClick={handleExportPDF} style={styles.pdfBtn}>
                    ⬇️ Xuất PDF
                </button>
            </div>


            <div style={styles.tabs}>
                {tabs.map(tab => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        style={{
                            ...styles.tab,
                            background: activeTab === tab.key ? '#667eea' : '#f0f2ff',
                            color: activeTab === tab.key ? '#fff' : '#667eea'
                        }}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>


            <div id="report-content" style={styles.content}>
                {activeTab === 'report' && (
                    <div>{renderReport(report)}</div>
                )}

                {activeTab === 'trends' && (
                    <div>
                        <h3 style={styles.h3}>Kết quả từ Trend Agent</h3>
                        <div style={styles.detailBox}>
                            {details?.trends || 'Không có dữ liệu'}
                        </div>
                    </div>
                )}

                {activeTab === 'competitors' && (
                    <div>
                        <h3 style={styles.h3}>Kết quả từ Competitor Agent</h3>
                        <div style={styles.detailBox}>
                            {details?.competitors || 'Không có dữ liệu'}
                        </div>
                    </div>
                )}

                {activeTab === 'sources' && (
                    <div>
                        <h3 style={styles.h3}>🔗 Nguồn tham khảo ({sources?.length || 0})</h3>
                        {sources?.map((src, i) => (
                            <a
                                key={i}
                                href={src}
                                target="_blank"
                                rel="noreferrer"
                                style={styles.sourceLink}
                            >
                                {i + 1}. {src}
                            </a>
                        ))}
                    </div>
                )}

            </div>
        </div>
    );
}

const styles = {
    card: {
        background: '#fff',
        borderRadius: 12,
        padding: 28,
        boxShadow: '0 2px 12px rgba(0,0,0,0.08)'
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 16,
        paddingBottom: 16,
        borderBottom: '2px solid #f0f0f0'
    },
    title: { margin: 0, fontSize: 20, color: '#1a1a2e' },
    date: { fontSize: 13, color: '#888' },
    copyBtn: {
        background: '#f0f2ff',
        color: '#667eea',
        border: '1px solid #d0d5ff',
        padding: '8px 16px',
        borderRadius: 8,
        cursor: 'pointer',
        fontSize: 14
    },
    tabs: {
        display: 'flex',
        gap: 8,
        marginBottom: 20,
        flexWrap: 'wrap'
    },
    tab: {
        padding: '8px 16px',
        borderRadius: 8,
        border: 'none',
        outline: 'none', // Thêm để xóa đường viền đen focus mặc định
        cursor: 'pointer',
        fontSize: 14,
        fontWeight: 600
    },
    content: { lineHeight: 1.8, color: '#333' },
    h1: { fontSize: 22, color: '#1a1a2e', borderBottom: '2px solid #667eea', paddingBottom: 8 },
    h2: { fontSize: 18, color: '#333', marginTop: 24 },
    h3: { fontSize: 16, color: '#555' },
    p: { margin: '4px 0' },
    li: { margin: '4px 0 4px 20px' },
    detailBox: {
        background: '#f9f9f9',
        borderRadius: 8,
        padding: 16,
        whiteSpace: 'pre-wrap',
        fontSize: 14,
        lineHeight: 1.7
    },
    sourceLink: {
        display: 'block',
        color: '#667eea',
        fontSize: 13,
        marginBottom: 8,
        wordBreak: 'break-all'
    },
    pdfBtn: {
        background: '#ff4d4f',
        color: '#fff',
        border: 'none',
        padding: '8px 16px',
        borderRadius: 8,
        cursor: 'pointer',
        fontSize: 14
    }
};