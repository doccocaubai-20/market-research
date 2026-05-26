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
        <div className="card search-card">
            <div className="card-header">
                <h2>Khởi tạo nghiên cứu</h2>
                <span>Chọn chủ đề, hệ thống sẽ tự động xử lý đa tác tử</span>
            </div>
            <div className="search-input-row">
                <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                    placeholder="VD: Thị trường trà sữa Việt Nam 2025"
                    className="search-input"
                    disabled={loading}
                />
                <button
                    onClick={handleSubmit}
                    disabled={!topic.trim() || loading}
                    style={{
                        background: 'var(--gradient-primary)',
                        opacity: !topic.trim() || loading ? 0.6 : 1
                    }}
                    className="primary-button"
                >
                    {loading ? '⏳ Đang nghiên cứu...' : '🚀 Bắt đầu'}
                </button>
            </div>
            <div className="search-suggestions">
                <span>Gợi ý nhanh:</span>
                {suggestions.map((s, i) => (
                    <span
                        key={i}
                        onClick={() => !loading && setTopic(s)}
                        style={{
                            cursor: loading ? 'not-allowed' : 'pointer'
                        }}
                        className="pill-tag"
                    >
                        {s}
                    </span>
                ))}
            </div>
        </div>
    );
}
