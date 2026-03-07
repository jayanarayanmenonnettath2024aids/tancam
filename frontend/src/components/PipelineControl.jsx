import { useState, useEffect, useContext } from 'react';
import axios from '../api/axiosConfig';
import { ENDPOINTS } from '../api/endpoints';
import { AuthContext } from '../context/AuthContext';

export default function PipelineControl() {
    const [statusList, setStatusList] = useState([]);
    const [scheduleList, setScheduleList] = useState([]);
    const [loading, setLoading] = useState(true);
    const [triggering, setTriggering] = useState(false);
    const { user } = useContext(AuthContext);

    const fetchData = async () => {
        try {
            const [resStatus, resSchedule] = await Promise.all([
                axios.get(ENDPOINTS.PIPELINE_STATUS).catch(() => ({ data: [] })),
                axios.get(ENDPOINTS.PIPELINE_SCHEDULE).catch(() => ({ data: [] }))
            ]);
            setStatusList(resStatus.data);
            setScheduleList(resSchedule.data);
        } catch (err) {
            console.error(err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    const handleTrigger = async (source) => {
        setTriggering(true);
        try {
            const res = await axios.post(`${ENDPOINTS.PIPELINE_TRIGGER}/${source}`);
            alert(`Trigger successful: ${JSON.stringify(res.data)}`);
            fetchData();
        } catch (err) {
            alert('Trigger failed: ' + (err.response?.data?.message || err.message));
        }
        setTriggering(false);
    };

    const getNextRun = (source) => {
        const jobMap = { 'erp': 'job_erp', 'portal': 'job_portal', 'email': 'job_email', 'run-all': 'job_run_all' };
        const jobId = jobMap[source];
        if (!jobId) return 'manual only';

        const job = scheduleList.find(j => j.id === jobId);
        if (!job) return 'not scheduled';

        const nextRunDate = new Date(job.next_run_time);
        const diffMin = Math.round((nextRunDate - new Date()) / 60000);

        if (diffMin <= 0) return 'Running soon...';
        return `in ${diffMin} min`;
    };

    const getTimeAgo = (isoString) => {
        if (!isoString) return 'never';
        const diffSec = Math.round((new Date() - new Date(isoString)) / 1000);
        if (diffSec < 60) return `${diffSec}s ago`;
        if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
        return `${Math.floor(diffSec / 3600)}h ago`;
    };

    return (
        <div className="p-8 bg-slate-900 min-h-full text-slate-200">
            <div className="flex justify-between items-end mb-8 border-b border-slate-700 pb-6">
                <div>
                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full text-xs font-bold uppercase tracking-widest mb-4 mt-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                        System Online
                    </div>
                    <h1 className="text-4xl font-black tracking-tight text-white mb-2">Pipeline Control Center</h1>
                    <p className="text-slate-400">Real-time supervision of active ingestion engines.</p>
                </div>

                <button
                    onClick={() => handleTrigger('run-all')}
                    disabled={triggering}
                    className={`bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-8 rounded-lg shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all duration-300 transform hover:-translate-y-1 ${triggering ? 'opacity-50 cursor-not-allowed animate-pulse' : ''}`}>
                    {triggering ? 'Executing Global Run...' : '⚡ TRIGGER ALL PIPELINES NOW'}
                </button>
            </div>

            <div className="bg-slate-800 rounded-xl border border-slate-700 shadow-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-slate-950/50 text-slate-400 text-xs font-bold uppercase tracking-widest">
                            <tr>
                                <th className="px-6 py-5">Source Node</th>
                                <th className="px-6 py-5 border-l border-slate-800/50">Last Active</th>
                                <th className="px-6 py-5 border-l border-slate-800/50">Txns Processed</th>
                                <th className="px-6 py-5 border-l border-slate-800/50">Health Status</th>
                                <th className="px-6 py-5 border-l border-slate-800/50 text-center">Next Auto Run</th>
                                <th className="px-6 py-5 border-l border-slate-800/50 text-right">Manual Override</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/50">
                            {loading ? (
                                <tr><td colSpan="6" className="text-center py-12 text-slate-500 font-mono animate-pulse">Establishing uplink to nodes...</td></tr>
                            ) : statusList.map(s => (
                                <tr key={s.source} className="hover:bg-slate-700/30 transition-colors group">
                                    <td className="px-6 py-5">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs
                                          ${s.source === 'erp' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30' :
                                                    s.source === 'portal' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' :
                                                        s.source === 'email' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                                                            s.source === 'excel' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                                                                s.source === 'pdf' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                                                                    'bg-slate-500/20 text-slate-400 border border-slate-500/30'}`}>
                                                {s.source.substring(0, 2).toUpperCase()}
                                            </div>
                                            <span className="font-medium text-slate-200 uppercase tracking-wide">{s.source} INGESTION</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5 font-mono text-slate-400 border-l border-slate-800/50">
                                        {getTimeAgo(s.triggered_at)}
                                        <div className="text-[10px] text-slate-600 mt-1">{s.duration_ms || 0} ms duration</div>
                                    </td>
                                    <td className="px-6 py-5 border-l border-slate-800/50">
                                        <div className="flex items-baseline gap-2">
                                            <span className="text-2xl font-black text-slate-200 font-mono bg-slate-900/50 px-3 py-1 rounded border border-slate-800">{s.records_affected}</span>
                                            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">rcds</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5 border-l border-slate-800/50">
                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border
                                      ${s.status === 'ok' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                                                s.status === 'never_run' ? 'bg-slate-500/10 text-slate-400 border-slate-500/30' :
                                                    'bg-rose-500/10 text-rose-400 border-rose-500/30'}`}>
                                            {s.status === 'ok' ? '✅ OK' : s.status === 'failed' ? '❌ FAILED' : '⏸️ IDLE'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-5 border-l border-slate-800/50 text-center text-sm font-mono text-cyan-400/80">
                                        {getNextRun(s.source)}
                                    </td>
                                    <td className="px-6 py-5 border-l border-slate-800/50 text-right">
                                        <button onClick={() => handleTrigger(s.source)} disabled={triggering || s.source === 'run-all'}
                                            className={`bg-slate-700 hover:bg-slate-600 border border-slate-600 hover:border-slate-500 text-white text-xs font-bold uppercase tracking-wider py-2 px-4 rounded transition-all
                                      ${s.source === 'run-all' ? 'hidden' : ''} ${triggering ? 'opacity-50 cursor-not-allowed' : ''}`}>
                                            Force Run 🚀
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="mt-8 text-center text-xs font-mono text-slate-600">
                NODE SYNCHRONIZATION: ONLINE • ENCRYPTION: SECURE
            </div>
        </div>
    );
}
