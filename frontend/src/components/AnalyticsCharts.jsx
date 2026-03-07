import { useState, useEffect } from 'react';
import axios from '../api/axiosConfig';
import { ENDPOINTS } from '../api/endpoints';
import { useNavigate } from 'react-router-dom';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler
);

export default function AnalyticsCharts() {
    const [trends, setTrends] = useState([]);
    const [sources, setSources] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const [resTrends, resSources] = await Promise.all([
                    axios.get(ENDPOINTS.ANALYTICS_TRENDS).catch(() => ({ data: [] })),
                    axios.get(ENDPOINTS.ANALYTICS_SOURCES).catch(() => ({ data: [] }))
                ]);
                setTrends(resTrends.data);
                setSources(resSources.data);
            } catch (err) {
                console.error("Chart data fetch failed");
            }
            setLoading(false);
        };
        fetchData();
    }, []);

    if (loading) return <div className="p-10 text-center text-slate-400">Loading complex visualizations...</div>;

    const trendData = {
        labels: trends.map(t => t.month),
        datasets: [{
            label: 'Trade Value (₹)',
            data: trends.map(t => t.value),
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.4
        }]
    };

    const volumeData = {
        labels: trends.map(t => t.month),
        datasets: [{
            label: 'Shipment Volume',
            data: trends.map(t => t.volume),
            backgroundColor: 'rgb(99, 102, 241)',
            borderRadius: 4
        }]
    };

    const sourceData = {
        labels: sources.map(s => s.source.toUpperCase()),
        datasets: [{
            data: sources.map(s => s.count),
            backgroundColor: [
                'rgba(59, 130, 246, 0.8)',
                'rgba(16, 185, 129, 0.8)',
                'rgba(245, 158, 11, 0.8)',
                'rgba(99, 102, 241, 0.8)',
                'rgba(236, 72, 153, 0.8)',
            ],
            borderWidth: 0,
        }]
    };

    return (
        <div className="p-8 space-y-8 bg-slate-50 min-h-full">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-slate-800">Analytics Insights</h1>
                <p className="text-slate-500 mt-1">Deep dive into historical trends and source distributions</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-6">Trade Value Trends (12 Months)</h3>
                    <div className="h-80">
                        <Line data={trendData} options={{ maintainAspectRatio: false, plugins: { legend: { display: false } } }} />
                    </div>
                </div>

                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-6">Ingestion Source Split</h3>
                    <div className="h-64 flex justify-center mt-8">
                        <Pie data={sourceData} options={{ maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }} />
                    </div>
                </div>

                <div className="lg:col-span-3 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm mt-4">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest">Shipment Volume Trajectory</h3>
                        <button onClick={() => window.print()} className="px-3 py-1.5 text-xs font-semibold bg-slate-100 text-slate-600 rounded whitespace-nowrap border border-slate-200 hover:bg-slate-200 transition-colors">
                            🖨️ Export PDF
                        </button>
                    </div>
                    <div className="h-72">
                        <Bar
                            data={volumeData}
                            options={{
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } },
                                onClick: (event, elements) => {
                                    if (elements.length > 0) {
                                        const label = volumeData.labels[elements[0].index];
                                        // Optional routing here if they wanted month routing. User requested Top Products routing
                                        // But the user's example explicitly applied it here, we will apply it below when we add products chart later or just here since it's the only bar chart currently
                                        navigate(`/shipments?search=${encodeURIComponent(label)}`);
                                    }
                                }
                            }}
                        />
                    </div>
                </div>

            </div>
        </div>
    );
}
