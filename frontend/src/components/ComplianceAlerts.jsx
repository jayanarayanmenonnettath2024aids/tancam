import { useState, useEffect, useContext } from 'react';
import axios from '../api/axiosConfig';
import { ENDPOINTS } from '../api/endpoints';
import { AuthContext } from '../context/AuthContext';

export default function ComplianceAlerts() {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const { user } = useContext(AuthContext);

    const fetchAlerts = async () => {
        setLoading(true);
        try {
            const res = await axios.get(ENDPOINTS.COMPLIANCE_ALERTS);
            setAlerts(res.data);
        } catch (err) {
            console.error(err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchAlerts();
    }, []);

    const handleRunChecks = async () => {
        setRunning(true);
        try {
            const res = await axios.post(ENDPOINTS.COMPLIANCE_RUN);
            alert(`Check Complete! Evaluated: ${res.data.checked} | Critical flags: ${res.data.critical}`);
            fetchAlerts();
        } catch (err) {
            alert('Failed to run checks.');
        }
        setRunning(false);
    };

    return (
        <div className="p-8 h-full bg-slate-50">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-extrabold tracking-tight text-slate-800">Compliance Center</h1>
                    <p className="text-slate-500 mt-1">Real-time alerts for GST, HS code formatting, and missing customs docs</p>
                </div>

                {user?.role === 'admin' && (
                    <button
                        onClick={handleRunChecks}
                        disabled={running}
                        className={`bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 px-6 rounded-lg shadow-lg shadow-indigo-500/20 transition-all duration-200 ${running ? 'opacity-70 cursor-not-allowed animate-pulse' : 'transform hover:-translate-y-0.5'}`}>
                        {running ? 'Running Automated Audits...' : 'Run Compliance Scan'}
                    </button>
                )}
            </div>

            <div className="space-y-4 max-w-5xl">
                {loading ? (
                    <div className="text-center py-10 text-slate-400">Loading alerts...</div>
                ) : alerts.length === 0 ? (
                    <div className="bg-emerald-50 border border-emerald-200 p-8 rounded-2xl text-center shadow-sm">
                        <div className="text-4xl mb-4">✅</div>
                        <h3 className="text-xl font-bold text-emerald-800 mb-2">Zero Compliance Alerts</h3>
                        <p className="text-emerald-600">All shipments within our platform pass the rigorous compliance audits.</p>
                    </div>
                ) : alerts.map(alt => (
                    <div key={alt.id} className={`p-5 rounded-xl border shadow-sm flex items-start gap-5 transition-all
                  ${alt.overall_status === 'critical' ? 'bg-rose-50 border-rose-200' : 'bg-amber-50 border-amber-200'}`}>

                        <div className={`p-4 rounded-full flex-shrink-0 ${alt.overall_status === 'critical' ? 'bg-rose-100 text-rose-500' : 'bg-amber-100 text-amber-500'}`}>
                            <span className="text-2xl">{alt.overall_status === 'critical' ? '🚨' : '⚠️'}</span>
                        </div>

                        <div className="flex-1 pt-1.5">
                            <div className="flex justify-between items-start mb-2">
                                <h3 className={`font-bold text-lg ${alt.overall_status === 'critical' ? 'text-rose-900' : 'text-amber-900'}`}>
                                    Shipment ID: <span className="font-mono bg-white/50 px-2 py-0.5 rounded ml-1 border border-black/5">{alt.shipment_id}</span>
                                </h3>
                                <span className={`text-[10px] uppercase font-bold tracking-wider px-2.5 py-1 rounded-full border
                              ${alt.overall_status === 'critical' ? 'bg-rose-600 text-white border-rose-700' : 'bg-amber-500 text-white border-amber-600'}`}>
                                    {alt.overall_status}
                                </span>
                            </div>

                            <div className="space-y-2 mt-4 text-sm font-medium">
                                {alt.gstin_flag && <p className="text-rose-700 bg-white/60 p-2 rounded border border-rose-100">• GSTIN Error: {alt.gstin_flag}</p>}
                                {alt.hs_code_flag && <p className="text-amber-800 bg-white/60 p-2 rounded border border-amber-100">• HS Code Warning: {alt.hs_code_flag}</p>}
                                {alt.gst_amount_flag && <p className="text-amber-800 bg-white/60 p-2 rounded border border-amber-100">• GST Calculation Warning: {alt.gst_amount_flag}</p>}
                                {alt.missing_docs && alt.missing_docs.length > 0 &&
                                    <p className={`${alt.overall_status === 'critical' ? 'text-rose-700 bg-white/60 border-rose-100' : 'text-amber-800 bg-white/60 border-amber-100'} p-2 rounded border`}>
                                        • Missing Documents: <span className="uppercase font-mono text-[11px] px-1 bg-black/5 rounded">{alt.missing_docs.join(', ')}</span>
                                    </p>
                                }
                            </div>

                            <div className="text-[10px] text-slate-400 font-mono mt-4 uppercase tracking-wider">
                                Checked Auto: {alt.checked_at?.split('T')[0]} @ {alt.checked_at?.split('T')[1].substring(0, 8)}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
