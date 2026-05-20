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

    if (loading) return <div style={styles.card}>Đang tải lịch sử...</div>;
    if (history.length === 0) return null;

    return (
        <div style={styles.card}>
            <h3 style={styles.title}>📚 Lịch sử báo cáo ({history.length})</h3>
            {history.map(item => (
                <div
                    key={item.id}
                    onClick={() => onSelect(item.id)}
                    style={styles.item}
                >
                    <div style={styles.itemLeft}>
                        <div style={styles.itemTopic}>{item.topic}</div>
                        <div style={styles.itemDate}>🕐 {item.created_at}</div>
                    </div>
                    <div style={styles.itemRight}>
                        <button
                            onClick={() => onSelect(item.id)}
                            style={styles.viewBtn}
                        >
                            Xem
                        </button>
                        <button
                            onClick={(e) => handleDelete(item.id, e)}
                            style={styles.deleteBtn}
                        >
                            Xóa
                        </button>
                    </div>
                </div>
            ))}
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
    title: { margin: '0 0 16px', fontSize: 16, color: '#1a1a2e' },
    item: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '12px 0',
        borderBottom: '1px solid #f0f0f0',
        cursor: 'pointer',
        borderRadius: 8,
        transition: 'background 0.2s'
    },
    itemLeft: { flex: 1 },
    itemTopic: { fontWeight: 600, fontSize: 14, color: '#333' },
    itemDate: { fontSize: 12, color: '#888', marginTop: 4 },
    itemRight: { display: 'flex', gap: 8 },
    viewBtn: {
        background: '#f0f2ff',
        color: '#667eea',
        border: '1px solid #d0d5ff',
        padding: '4px 12px',
        borderRadius: 6,
        cursor: 'pointer',
        fontSize: 13
    },
    deleteBtn: {
        background: '#fff2f0',
        color: '#ff4d4f',
        border: '1px solid #ffccc7',
        padding: '4px 12px',
        borderRadius: 6,
        cursor: 'pointer',
        fontSize: 13
    }
};