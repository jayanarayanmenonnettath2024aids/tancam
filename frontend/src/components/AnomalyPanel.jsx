import { useState, useEffect, useContext } from 'react';
import axios from '../api/axiosConfig';
import { ENDPOINTS } from '../api/endpoints';
import { AuthContext } from '../context/AuthContext';

export default function AnomalyPanel() {
    const [anomalies, setAnomalies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [detecting, setDetecting] = useState(false);
    const { user } = useContext(AuthContext);

    const fetchAnomalies = async () => {
        setLoading(true);
        try {
            const res = await axios.get(ENDPOINTS.ANOMALIES, { params: { min_score: 0 } });
            setAnomalies(res.data);
        } catch (err) {
            console.error(err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchAnomalies();
    }, []);

    const handleDetect = async () => {
        setDetecting(true);
        try {
            const res = await axios.post(ENDPOINTS.ANOMALIES_DETECT);
            alert(`Analysis Complete! Scanned: ${res.data.scanned} records | Found ${res.data.anomalies_found} Anomalies.`);
            fetchAnomalies();
        } catch (err) {
            alert('Failed to detect anomalies.');
        }
        setDetecting(false);
    };

    const getScoreColor = (score) => {
        if (score > 0.7) return 'bg-rose-500';
        if (score > 0.4) return 'bg-amber-500';
        return 'bg-emerald-500';
    };

    const getScoreBg = (score) => {
        if (score > 0.7) return 'bg-rose-100 text-rose-800 border-rose-200';
        if (score > 0.4) return 'bg-amber-100 text-amber-800 border-amber-200';
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    };

    return (
        <div className="p-8 h-full bg-slate-50">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-extrabold tracking-tight text-slate-800">Anomaly Detection Engine</h1>
                    <p className="text-slate-500 mt-1">Machine Learning Analysis using Isolation Forests</p>
                </div>

                {user?.role === 'admin' && (
                    <button
                        onClick={handleDetect}
                        disabled={detecting}
                        className={`flex gap-2 items-center bg-fuchsia-600 hover:bg-fuchsia-700 text-white font-semibold py-2.5 px-6 rounded-lg shadow-lg shadow-fuchsia-500/20 transition-all duration-200 ${detecting ? 'opacity-70 cursor-not-allowed animate-pulse' : 'transform hover:-translate-y-0.5'}`}>
                        <span>{detecting ? '⚙️' : '🧠'}</span>
                        {detecting ? 'Training & Scanning DB...' : 'Run ML Detection Sweep'}
                    </button>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {loading ? (
                    <div className="col-span-full text-center py-10 text-slate-400">Loading structural integrity records...</div>
                ) : anomalies.length === 0 ? (
                    <div className="col-span-full bg-white border border-slate-200 p-8 rounded-2xl text-center shadow-sm">
                        <div className="text-4xl mb-4">🛡️</div>
                        <h3 className="text-xl font-bold text-slate-800 mb-2">No Anomalies Found</h3>
                        <p className="text-slate-500">The ML engine hasn't detected any suspicious patterns yet.</p>
                    </div>
                ) : anomalies.map(ano => (
                    <div key={ano.id} className={`p-6 bg-white rounded-2xl border ${ano.is_anomaly ? 'shadow-md border-rose-200' : 'shadow-sm border-slate-200'} relative overflow-hidden group`}>

                        {ano.is_anomaly && <div className="absolute top-0 right-0 w-2 h-full bg-rose-500 shadow-[0_0_15px_rgba(244,63,94,0.5)]"></div>}

                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <p className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-1 mt-1">{ano.record_type} ID</p>
                                <p className="font-mono font-medium text-slate-800 bg-slate-100 px-2 py-0.5 rounded inline-block text-sm border border-slate-200">{ano.record_id}</p>
                            </div>
                            <div className={`px-3 py-1.5 rounded-lg border flex flex-col items-center justify-center min-w-[60px] ${getScoreBg(ano.anomaly_score)}`}>
                                <span className="text-xl font-black">{Math.round(ano.anomaly_score * 100)}</span>
                                <span className="text-[9px] uppercase font-bold opacity-80 mt-0.5">SCORE</span>
                            </div>
                        </div>

                        <div className="mb-5">
                            <div className="flex justify-between text-xs mb-1.5 font-bold text-slate-500 uppercase">
                                <span>Confidence Meter</span>
                            </div>
                            <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden border border-slate-200 shadow-inner">
                                <div className={`h-full ${getScoreColor(ano.anomaly_score)} transition-all duration-1000`} style={{ width: `${ano.anomaly_score * 100}%` }}></div>
                            </div>
                        </div>

                        <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 mb-4">
                            <p className={`text-sm font-semibold mb-2 ${ano.is_anomaly ? 'text-rose-700' : 'text-slate-600'}`}>
                                {ano.is_anomaly ? '🚨 ' : ''}{ano.description}
                            </p>
                            <div className="grid grid-cols-2 gap-2 text-xs text-slate-500 mt-2 font-mono">
                                {Object.entries(ano.feature_values || {}).map(([k, v]) => (
                                    <div key={k} className="bg-white px-2 py-1 rounded border border-slate-200 truncate" title={String(v)}>
                                        <span className="opacity-60 block text-[9px] uppercase tracking-wider">{k}</span>
                                        <span className="font-semibold text-slate-700">{v}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <p className="text-[10px] text-slate-400 font-mono text-center uppercase tracking-wider">
                            Detected: {ano.detected_at?.replace('T', ' ').substring(0, 19)}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    );
}
