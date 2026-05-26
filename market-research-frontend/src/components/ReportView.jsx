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
            if (line.startsWith('# ')) return <h1 key={i} className="report-h1">{line.slice(2)}</h1>;
            if (line.startsWith('## ')) return <h2 key={i} className="report-h2">{line.slice(3)}</h2>;
            if (line.startsWith('### ')) return <h3 key={i} className="report-h3">{line.slice(4)}</h3>;
            if (line.startsWith('- ') || line.startsWith('* ')) {
                return <li key={i} className="report-li">{line.slice(2).replace(/\*\*(.*?)\*\*/g, '$1')}</li>;
            }
            if (line.trim() === '') return <br key={i} />;
            return <p key={i} className="report-p">{line.replace(/\*\*(.*?)\*\*/g, '$1')}</p>;
        });
    };

    return (
        <div className="card report-card">
            <div className="report-header">
                <div>
                    <h2 className="report-title">{topic}</h2>
                    <span className="report-date">
                        {new Date().toLocaleDateString('vi-VN', {
                            day: '2-digit', month: '2-digit', year: 'numeric',
                            hour: '2-digit', minute: '2-digit'
                        })}
                    </span>
                </div>
                <div className="report-actions">
                    <button
                        onClick={() => navigator.clipboard.writeText(report)}
                        className="ghost-button"
                    >
                        📋 Copy
                    </button>
                    <button onClick={handleExportPDF} className="primary-button">
                        ⬇️ Xuất PDF
                    </button>
                </div>
            </div>


            <div className="report-tabs">
                {tabs.map(tab => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        className={`report-tab ${activeTab === tab.key ? 'active' : ''}`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>


            <div id="report-content" className="report-content">
                {activeTab === 'report' && (
                    <div>{renderReport(report)}</div>
                )}

                {activeTab === 'trends' && (
                    <div>
                        <h3 className="report-h3">Kết quả từ Trend Agent</h3>
                        <div className="detail-box">
                            {details?.trends || 'Không có dữ liệu'}
                        </div>
                    </div>
                )}

                {activeTab === 'competitors' && (
                    <div>
                        <h3 className="report-h3">Kết quả từ Competitor Agent</h3>
                        <div className="detail-box">
                            {details?.competitors || 'Không có dữ liệu'}
                        </div>
                    </div>
                )}

                {activeTab === 'sources' && (
                    <div>
                        <h3 className="report-h3">Nguồn tham khảo ({sources?.length || 0})</h3>
                        {sources?.map((src, i) => (
                            <a
                                key={i}
                                href={src}
                                target="_blank"
                                rel="noreferrer"
                                className="source-link"
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
