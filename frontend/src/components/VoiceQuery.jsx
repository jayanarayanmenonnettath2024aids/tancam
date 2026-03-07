import { useState } from 'react';
import axios from '../api/axiosConfig';
import { ENDPOINTS } from '../api/endpoints';

export default function VoiceQuery() {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [listening, setListening] = useState(false);

    const predefinedQueries = [
        "Total trade value this month",
        "Show me top 5 customers",
        "Any compliance alerts?",
        "How many pending shipments?"
    ];

    const handleSubmit = async (e, forcedQuery = null) => {
        e?.preventDefault();
        const q = forcedQuery || query;
        if (!q.trim()) return;
        setQuery(q);

        setLoading(true);
        setResult(null);
        try {
            const res = await axios.post(ENDPOINTS.QUERY, { query: q });
            setResult(res.data);
        } catch (err) {
            setResult({ answer: "Failed to process query. Is the backend running?" });
        }
        setLoading(false);
    };

    const handleVoice = () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return alert("Speech recognition not supported in this browser.");

        const recognition = new SpeechRecognition();
        recognition.onstart = () => setListening(true);
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            setQuery(transcript);
            setTimeout(() => handleSubmit(null, transcript), 100);
        };
        recognition.onerror = () => setListening(false);
        recognition.onend = () => setListening(false);
        recognition.start();
    };

    return (
        <div className="bg-white border-b border-slate-200 p-6 shadow-sm z-10 relative">
            <div className="max-w-4xl mx-auto">

                <div className="flex flex-wrap gap-2 mb-4 justify-center">
                    <span className="text-xs text-slate-400 py-1 uppercase font-semibold tracking-wider mr-2">Try asking:</span>
                    {predefinedQueries.map(q => (
                        <button key={q} onClick={() => handleSubmit(null, q)} className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-600 px-3 py-1 rounded-full transition-colors border border-slate-200">
                            {q}
                        </button>
                    ))}
                </div>

                <form onSubmit={(e) => handleSubmit(e)} className="flex relative items-center shadow-lg shadow-slate-200/50 rounded-full group">
                    <div className="absolute left-4 text-xl opacity-60">✨</div>
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Ask your data anything in plain English..."
                        className="w-full pl-12 pr-14 py-4 bg-white rounded-full border border-slate-200 focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 outline-none text-slate-700 text-lg transition-all"
                    />
                    <button type="button" onClick={handleVoice} title="Use Voice"
                        className={`absolute right-2 p-2.5 rounded-full transition-all ${listening ? 'bg-red-100 text-red-500 animate-pulse shadow-inner' : 'bg-slate-100 hover:bg-blue-100 text-slate-500 hover:text-blue-600'}`}>
                        🎤
                    </button>
                </form>

                {loading && (
                    <div className="mt-6 flex flex-col items-center">
                        <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
                        <p className="text-slate-500 text-sm mt-2 font-medium">Extracting intent and computing results...</p>
                    </div>
                )}

                {result && !loading && (
                    <div className="mt-6 p-5 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100/50 shadow-sm animate-in fade-in slide-in-from-top-4 duration-300">
                        <div className="flex justify-between items-start mb-3">
                            <p className="text-slate-800 font-semibold text-xl leading-relaxed">{result.answer}</p>
                            {result.intent && <span className="text-[10px] uppercase font-bold tracking-wider bg-blue-200/50 text-blue-700 px-2.5 py-1 rounded-md ml-4 shrink-0">{result.intent}</span>}
                        </div>
                        {result.sql_executed && (
                            <div className="mt-3 bg-white/60 p-3 rounded-lg border border-white">
                                <p className="text-[10px] uppercase text-slate-400 font-bold mb-1">Generated SQL</p>
                                <code className="block text-xs text-indigo-800 font-mono break-all">{result.sql_executed}</code>
                            </div>
                        )}

                        {result.data && result.data.length > 0 && typeof result.data[0] === 'object' && (
                            <div className="mt-4 overflow-x-auto">
                                <table className="w-full text-sm text-left border-collapse">
                                    <thead>
                                        <tr className="bg-slate-200/50 text-slate-500 text-xs uppercase tracking-wider">
                                            {Object.keys(result.data[0]).map(k => <th key={k} className="px-3 py-2 font-medium">{k}</th>)}
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-200/50 bg-white/40">
                                        {result.data.map((row, i) => (
                                            <tr key={i}>
                                                {Object.values(row).map((v, j) => <td key={j} className="px-3 py-2 text-slate-700">{String(v)}</td>)}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
