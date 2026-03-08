import { useState, useEffect } from 'react';
import { API_BASE, ENDPOINTS } from '../api/endpoints';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

export default function Dashboard() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState('');

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        const es = new EventSource(`${API_BASE}${ENDPOINTS.ANALYTICS_SUMMARY.replace('/summary', '/stream')}?token=${token}`);

        es.onmessage = (e) => {
            const parsedData = JSON.parse(e.data);
            setData(parsedData);
            setLastUpdated(new Date().toLocaleTimeString());
            setLoading(false);
        };

        es.onerror = (err) => {
            console.error("SSE stream error", err);
            es.close();
            setLoading(false);
        };

        return () => es.close();
    }, []);

    if (loading && !data) return <div className="p-8 text-center animate-pulse text-slate-500">Loading Dashboard Data...</div>;

    const valueChange = data?.mom_growth_pct || 0;

    return (
        <div className="p-8 space-y-6">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-800">Executive Dashboard</h1>
                    <p className="text-slate-500 mt-1">Real-time unification of trade operations.</p>
                </div>
                <div className="text-sm text-slate-400 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    Live Sync (Updated {lastUpdated})
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-6">

                {/* Total Trade Value */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110"></div>
                    <p className="text-sm font-semibold text-slate-500 uppercase tracking-widest mb-2">Total Trade Value</p>
                    <p className="text-3xl font-black text-slate-800 mb-2 font-mono">₹{(data?.total_trade_value_month || 0).toLocaleString()}</p>
                    <p className={`text-xs font-bold ${valueChange > 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                        {valueChange > 0 ? '↑' : '↓'} {Math.abs(valueChange)}% vs last month
                    </p>
                </div>

                {/* Active Shipments */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110"></div>
                    <p className="text-sm font-semibold text-slate-500 uppercase tracking-widest mb-2">Active Shipments</p>
                    <p className="text-3xl font-black text-slate-800 mb-2 font-mono">{data?.active_shipments || 0}</p>
                    <p className="text-xs font-semibold text-amber-600 bg-amber-100 px-2 py-1 inline-block rounded">PENDING STATUS</p>
                </div>

                {/* Compliance Rate */}
                <div className={`p-6 rounded-2xl border shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group
            ${data?.compliance_rate > 90 ? 'bg-emerald-50 border-emerald-200' : data?.compliance_rate > 70 ? 'bg-amber-50 border-amber-200' : 'bg-rose-50 border-rose-200'}`}>
                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/40 rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110"></div>
                    <p className={`text-sm font-semibold uppercase tracking-widest mb-2 
                ${data?.compliance_rate > 90 ? 'text-emerald-700' : data?.compliance_rate > 70 ? 'text-amber-700' : 'text-rose-700'}`}>Compliance Rate</p>
                    <p className={`text-3xl font-black mb-2 font-mono
                ${data?.compliance_rate > 90 ? 'text-emerald-900' : data?.compliance_rate > 70 ? 'text-amber-900' : 'text-rose-900'}`}>{data?.compliance_rate || 0}%</p>
                    <div className="w-full bg-black/10 h-1.5 rounded-full mt-2">
                        <div className={`h-1.5 rounded-full ${data?.compliance_rate > 90 ? 'bg-emerald-500' : data?.compliance_rate > 70 ? 'bg-amber-500' : 'bg-rose-500'}`} style={{ width: `${data?.compliance_rate || 0}%` }}></div>
                    </div>
                </div>

                {/* Anomalies Detected */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110"></div>
                    <p className="text-sm font-semibold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-2">
                        Anomalies
                        {data?.anomalies_detected > 0 && <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>}
                    </p>
                    <p className={`text-3xl font-black mb-2 font-mono ${data?.anomalies_detected > 0 ? 'text-rose-600' : 'text-slate-800'}`}>{data?.anomalies_detected || 0}</p>
                    <p className="text-xs font-semibold text-slate-400">REQUIRES REVIEW</p>
                </div>

                {/* Advanced Engineered Insights */}
                <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group text-white xl:col-span-1 lg:col-span-2 md:col-span-2">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110"></div>
                    <p className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-2">
                        {data?.share_of_revenue_pct > 0 ? "Platform Share" : "Concentration Risk"}
                    </p>
                    <p className="text-3xl font-black mb-2 font-mono">
                        {data?.share_of_revenue_pct > 0
                            ? `${data.share_of_revenue_pct}%`
                            : `${data?.risk_concentration_pct || 0}%`}
                    </p>
                    <p className="text-xs text-slate-400 mt-2 font-medium">
                        {data?.share_of_revenue_pct > 0
                            ? "Your weight in total volume"
                            : "Tied to Top 3 Buyers"}
                    </p>
                    <div className="flex gap-2 text-[10px] text-slate-500 mt-3 font-mono opacity-60">
                        {Object.entries(data?.source_breakdown || {}).map(([s, c]) => (
                            <span key={s} className="bg-slate-700/50 px-1.5 py-0.5 rounded">{s}:{c}</span>
                        ))}
                    </div>
                </div>

            </div>

            {/* Lower Section placeholders */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-4">
                <div className="bg-white border text-center border-slate-200 p-6 rounded-2xl min-h-[300px] flex flex-col justify-center text-slate-800">
                    <h3 className="font-bold text-lg mb-4 text-slate-600">Top 5 Customers by Value</h3>
                    {data?.top_5_customers?.length > 0 ? (
                        <div className="h-64 relative flex items-center justify-center">
                            <Pie
                                data={{
                                    labels: data.top_5_customers.map(c => c.name),
                                    datasets: [{
                                        data: data.top_5_customers.map(c => c.value),
                                        backgroundColor: ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)', 'rgba(99,102,241,0.8)', 'rgba(236,72,153,0.8)'],
                                        borderWidth: 0,
                                    }]
                                }}
                                options={{ maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } } } }}
                            />
                        </div>
                    ) : (
                        <span className="text-slate-400">No customer data available</span>
                    )}
                </div>

                <div className="bg-white border text-center border-slate-200 p-6 rounded-2xl min-h-[300px] flex flex-col justify-center text-slate-800">
                    <h3 className="font-bold text-lg mb-4 text-slate-600">Top 5 Destination Ports</h3>
                    {data?.top_5_products?.length > 0 ? (
                        <div className="h-64 relative">
                            <Bar
                                data={{
                                    labels: data.top_5_products.map(p => p.name),
                                    datasets: [{
                                        label: 'Shipments',
                                        data: data.top_5_products.map(p => p.count),
                                        backgroundColor: 'rgba(99, 102, 241, 0.8)',
                                        borderRadius: 4
                                    }]
                                }}
                                options={{
                                    maintainAspectRatio: false,
                                    plugins: { legend: { display: false } },
                                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
                                }}
                            />
                        </div>
                    ) : (
                        <span className="text-slate-400">No product data available</span>
                    )}
                </div>
            </div>

        </div>
    );
}
