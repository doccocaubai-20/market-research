import { useEffect, useRef, useState } from 'react';
import SearchForm from '../components/SearchForm';
import ProgressBar from '../components/ProgressBar';
import ReportView from '../components/ReportView';
import HistoryList from '../components/HistoryList';
import { getReportById, streamResearch } from '../api/researchApi';

export default function Dashboard() {
    const [loading, setLoading] = useState(false);
    const [doneSteps, setDoneSteps] = useState([]);
    const [activeSteps, setActiveSteps] = useState([]);
    const [result, setResult] = useState(null);
    const [topic, setTopic] = useState('');
    const [error, setError] = useState('');
    const [refreshHistory, setRefreshHistory] = useState(0);
    const eventSourceRef = useRef(null);

    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    const handleSubmit = async (inputTopic) => {
        setLoading(true);
        setDoneSteps([]);
        setActiveSteps([]);
        setResult(null);
        setError('');
        setTopic(inputTopic);

        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        const stepKeys = ['search', 'trend', 'competitor', 'report'];
        const source = streamResearch(inputTopic);
        eventSourceRef.current = source;

        source.addEventListener('progress', (event) => {
            const data = JSON.parse(event.data);
            if (data?.status === 'running') {
                setActiveSteps((prev) => (prev.includes(data.agent) ? prev : [...prev, data.agent]));
            }
            if (data?.status === 'done') {
                setDoneSteps((prev) => (prev.includes(data.agent) ? prev : [...prev, data.agent]));
                setActiveSteps((prev) => prev.filter((agent) => agent !== data.agent));
            }
        });

        source.addEventListener('done', (event) => {
            const data = JSON.parse(event.data);
            setResult(data);
            setDoneSteps(stepKeys);
            setActiveSteps([]);
            setRefreshHistory((r) => r + 1);
            setLoading(false);
            source.close();
        });

        source.addEventListener('error', () => {
            setError('❌ Có lỗi xảy ra. Vui lòng thử lại.');
            setLoading(false);
            source.close();
        });
    };
    const handleSelectHistory = async (id) => {
        const data = await getReportById(id);
        setTopic(data.topic);
        setResult({
            report: data.report,
            sources: data.sources,
            details: {
                trends: data.trends,
                competitors: data.competitors
            }
        });
        setDoneSteps([]);
        setActiveSteps([]);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <div className="app-shell">
            <div className="app-hero">
                <div>
                    <p className="app-eyebrow">Market Intelligence Studio</p>
                    <h1 className="app-title">Market Research AI Agent</h1>
                    <p className="app-subtitle">
                        Hệ thống nghiên cứu thị trường đa tác tử, tổng hợp dữ liệu và tạo báo cáo chiến lược tức thì.
                    </p>
                </div>
            </div>

            <SearchForm onSubmit={handleSubmit} loading={loading} />

            {(loading || doneSteps.length > 0 || activeSteps.length > 0) && (
                <ProgressBar doneSteps={doneSteps} activeSteps={activeSteps} />
            )}

            {error && (
                <div className="app-alert">{error}</div>
            )}

            {result && (
                <ReportView
                    topic={topic}
                    report={result.report}
                    sources={result.sources}
                    details={result.details}
                />
            )}
            <HistoryList
                key={refreshHistory}
                onSelect={handleSelectHistory}
            />
        </div>
    );
}
