import { useEffect, useRef, useState } from 'react';
import SearchForm from '../components/SearchForm';
import ProgressBar from '../components/ProgressBar';
import ReportView from '../components/ReportView';
import HistoryList from '../components/HistoryList';
import { getReportById, streamResearch } from '../api/researchApi';

export default function Dashboard() {
    const [loading, setLoading] = useState(false);
    const [doneSteps, setDoneSteps] = useState([]);
    const [activeStep, setActiveStep] = useState(null);
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
        setActiveStep(null);
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
                setActiveStep(data.agent);
            }
            if (data?.status === 'done') {
                setDoneSteps((prev) => (prev.includes(data.agent) ? prev : [...prev, data.agent]));
                setActiveStep((current) => (current === data.agent ? null : current));
            }
        });

        source.addEventListener('done', (event) => {
            const data = JSON.parse(event.data);
            setResult(data);
            setDoneSteps(stepKeys);
            setActiveStep(null);
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
        setActiveStep(null);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h1 style={styles.title}>🔬 Market Research AI Agent</h1>
                <p style={styles.subtitle}>
                    Hệ thống nghiên cứu thị trường tự động bằng Multi-Agent AI
                </p>
            </div>

            <SearchForm onSubmit={handleSubmit} loading={loading} />

            {(loading || doneSteps.length > 0 || activeStep) && (
                <ProgressBar doneSteps={doneSteps} activeStep={activeStep} />
            )}

            {error && (
                <div style={styles.error}>{error}</div>
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

const styles = {
    container: {
        maxWidth: 900,
        margin: '0 auto',
        padding: '32px 16px',
        fontFamily: "'Segoe UI', Arial, sans-serif",
        background: '#f0f2f5',
        minHeight: '100vh'
    },
    header: {
        textAlign: 'center',
        marginBottom: 32
    },
    title: {
        fontSize: 32,
        background: 'linear-gradient(135deg, #667eea, #764ba2)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        margin: '0 0 8px'
    },
    subtitle: {
        color: '#888',
        fontSize: 15,
        margin: 0
    },
    error: {
        background: '#fff2f0',
        border: '1px solid #ffccc7',
        borderRadius: 8,
        padding: 16,
        color: '#ff4d4f',
        marginBottom: 24
    }
};