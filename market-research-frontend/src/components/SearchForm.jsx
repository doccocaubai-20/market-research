import { useState } from 'react';

export default function SearchForm({ onSubmit, loading }) {
    const [topic, setTopic] = useState('');

    const handleSubmit = () => {
        if (!topic.trim() || loading) return;
        onSubmit(topic);
    };

    const suggestions = [
        'Thị trường trà sữa Việt Nam',
        'Thị trường cà phê Việt Nam',
        'Thị trường xe điện Việt Nam',
        'Ngành thương mại điện tử Việt Nam',
        'Thị trường giáo dục trực tuyến'
    ];

    return (
        <div style={styles.card}>
            <h2 style={styles.title}>🔍 Nhập chủ đề nghiên cứu</h2>
            <div style={styles.inputRow}>
                <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                    placeholder="VD: Thị trường trà sữa Việt Nam 2025"
                    style={styles.input}
                    disabled={loading}
                />
                <button
                    onClick={handleSubmit}
                    disabled={!topic.trim() || loading}
                    style={{
                        ...styles.button,
                        opacity: !topic.trim() || loading ? 0.6 : 1
                    }}
                >
                    {loading ? '⏳ Đang nghiên cứu...' : '🚀 Bắt đầu'}
                </button>
            </div>
            <div style={styles.suggestions}>
                <span style={styles.suggestionLabel}>Gợi ý:</span>
                {suggestions.map((s, i) => (
                    <span
                        key={i}
                        onClick={() => !loading && setTopic(s)}
                        style={{
                            ...styles.tag,
                            cursor: loading ? 'not-allowed' : 'pointer'
                        }}
                    >
                        {s}
                    </span>
                ))}
            </div>
        </div>
    );
}

const styles = {
    card: {
        background: '#fff',
        borderRadius: 12,
        padding: 28,
        boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
        marginBottom: 24
    },
    title: { margin: '0 0 16px', fontSize: 18, color: '#1a1a2e' },
    inputRow: { display: 'flex', gap: 12, marginBottom: 16 },
    input: {
        flex: 1,
        padding: '12px 16px',
        fontSize: 15,
        borderRadius: 8,
        border: '1.5px solid #d9d9d9',
        outline: 'none'
    },
    button: {
        background: 'linear-gradient(135deg, #667eea, #764ba2)',
        color: '#fff',
        border: 'none',
        padding: '12px 24px',
        borderRadius: 8,
        fontSize: 15,
        cursor: 'pointer',
        fontWeight: 600,
        whiteSpace: 'nowrap'
    },
    suggestions: { display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' },
    suggestionLabel: { fontSize: 13, color: '#888', marginRight: 4 },
    tag: {
        background: '#f0f2ff',
        color: '#667eea',
        padding: '4px 12px',
        borderRadius: 20,
        fontSize: 13,
        border: '1px solid #d0d5ff'
    }
};