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
    const [progressPercent, setProgressPercent] = useState(0);
    const [result, setResult] = useState(null);
    const [topic, setTopic] = useState('');
    const [error, setError] = useState('');
    const [refreshHistory, setRefreshHistory] = useState(0);
    const eventSourceRef = useRef(null);
    const stepKeys = ['search', 'trend', 'competitor', 'report'];

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
        setProgressPercent(0);
        setResult(null);
        setError('');
        setTopic(inputTopic);

        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        const source = streamResearch(inputTopic);
        eventSourceRef.current = source;

        source.addEventListener('progress', (event) => {
            const data = JSON.parse(event.data);
            if (data?.status === 'running' && stepKeys.includes(data.agent)) {
                setActiveSteps((prev) => (prev.includes(data.agent) ? prev : [...prev, data.agent]));
            }
            if (data?.status === 'done' && stepKeys.includes(data.agent)) {
                setDoneSteps((prev) => (prev.includes(data.agent) ? prev : [...prev, data.agent]));
                setActiveSteps((prev) => prev.filter((agent) => agent !== data.agent));
            }
        });

        source.addEventListener('done', (event) => {
            const data = JSON.parse(event.data);
            setResult(data);
            setDoneSteps((prev) => (prev.includes('report') ? prev : [...prev, 'report']));
            setActiveSteps([]);
            setProgressPercent(100);
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

    useEffect(() => {
        const totalSteps = stepKeys.length;
        const activeWeight = 0.5;
        const rawPercent = ((doneSteps.length + activeSteps.length * activeWeight) / totalSteps) * 100;
        const bounded = Math.max(0, Math.min(99, Math.round(rawPercent)));
        setProgressPercent((prev) => (loading ? Math.max(prev, bounded) : prev));
    }, [doneSteps, activeSteps, loading, stepKeys.length]);
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
                <ProgressBar
                    doneSteps={doneSteps}
                    activeSteps={activeSteps}
                    progressPercent={progressPercent}
                />
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
