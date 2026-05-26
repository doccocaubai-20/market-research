import { useState, useEffect } from 'react';
import { getHistory, deleteReport } from '../api/researchApi';

export default function HistoryList({ onSelect }) {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            const data = await getHistory();
            setHistory(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id, e) => {
        e.stopPropagation();
        if (!window.confirm('Xóa báo cáo này?')) return;
        await deleteReport(id);
        setHistory(history.filter(h => h.id !== id));
    };

    if (loading) return <div className="card">Đang tải lịch sử...</div>;
    if (history.length === 0) return null;

    return (
        <div className="card history-card">
            <div className="card-header">
                <h3>Lịch sử báo cáo</h3>
                <span>{history.length} báo cáo</span>
            </div>
            {history.map(item => (
                <div
                    key={item.id}
                    onClick={() => onSelect(item.id)}
                    className="history-item"
                >
                    <div className="history-item-left">
                        <div className="history-topic">{item.topic}</div>
                        <div className="history-date">🕐 {item.created_at}</div>
                    </div>
                    <div className="history-actions">
                        <button
                            onClick={() => onSelect(item.id)}
                            className="ghost-button"
                        >
                            Xem
                        </button>
                        <button
                            onClick={(e) => handleDelete(item.id, e)}
                            className="danger-button"
                        >
                            Xóa
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
}
