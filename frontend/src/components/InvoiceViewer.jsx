import { useState, useEffect } from 'react';
import axios from '../api/axiosConfig';
import { ENDPOINTS } from '../api/endpoints';

export default function InvoiceViewer() {
    const [invoices, setInvoices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [uploading, setUploading] = useState(false);

    const fetchInvoices = async () => {
        setLoading(true);
        try {
            const res = await axios.get(ENDPOINTS.INVOICES, { params: { page, per_page: 8 } });
            setInvoices(res.data.items);
        } catch (err) {
            console.error(err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchInvoices();
    }, [page]);

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        setUploading(true);
        try {
            await axios.post(ENDPOINTS.INVOICES_UPLOAD, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            alert('Upload & Analysis Complete!');
            setPage(1);
            fetchInvoices();
        } catch (err) {
            alert('Upload failed: ' + err.message);
        }
        setUploading(false);
        e.target.value = null; // reset
    };

    return (
        <div className="p-8 container mx-auto">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-extrabold tracking-tight text-slate-800">Processed Invoices</h1>
                    <p className="text-slate-500 mt-1">AI Extracted from Emails, PDFs, and ERP Systems</p>
                </div>

                <div>
                    <label className={`cursor-pointer bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold py-2.5 px-6 rounded-lg shadow-lg shadow-blue-500/20 transition-all duration-200 transform hover:-translate-y-0.5 inline-block ${uploading ? 'opacity-70 animate-pulse pointer-events-none' : ''}`}>
                        {uploading ? 'Analyzing Document...' : '+ Upload PDF / Excel'}
                        <input type="file" className="hidden" accept=".pdf,.xlsx,.xls" onChange={handleFileUpload} disabled={uploading} />
                    </label>
                </div>
            </div>

            {loading ? (
                <div className="text-center py-12 text-slate-400">Loading invoices...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {invoices.map(inv => (
                        <div key={inv.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-xl transition-all duration-300 relative group overflow-hidden flex flex-col justify-between">
                            <div className="absolute -right-12 -top-12 w-32 h-32 bg-slate-50 rounded-full transition-transform group-hover:scale-150 -z-10"></div>

                            <div>
                                <div className="flex justify-between items-start mb-4">
                                    <span className="bg-blue-50 text-blue-600 font-mono text-xs font-bold px-2 py-1 rounded shadow-inner truncate max-w-[120px]">{inv.invoice_no}</span>
                                    <span className="bg-slate-100 text-slate-500 text-[10px] uppercase font-bold tracking-wider px-2 py-1 rounded">{inv.source}</span>
                                </div>
                                <div className="mb-4">
                                    <p className="text-xs text-slate-400 font-semibold uppercase mb-1">Buyer</p>
                                    <p className="text-sm text-slate-800 font-medium truncate" title={inv.buyer}>{inv.buyer || 'Unknown'}</p>
                                </div>
                                <div className="mb-4">
                                    <p className="text-xs text-slate-400 font-semibold uppercase mb-1">Total Value</p>
                                    <p className="text-2xl font-black text-slate-800 font-mono tracking-tight">{inv.currency} {inv.total_value?.toLocaleString() || '-'}</p>
                                </div>
                            </div>

                            <div className="pt-4 border-t border-slate-100 mt-2 flex justify-between items-center text-xs text-slate-500">
                                <span>{inv.invoice_date?.split('T')[0] || 'Unknown Date'}</span>
                                <button className="text-blue-600 hover:text-blue-700 font-semibold transition-colors">View Details →</button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <div className="mt-8 flex justify-center gap-2">
                <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-6 py-2 border border-slate-300 rounded-full bg-white text-slate-600 disabled:opacity-50 hover:bg-slate-100 transition-colors font-semibold shadow-sm">Previous</button>
                <button onClick={() => setPage(p => p + 1)} className="px-6 py-2 border border-slate-300 rounded-full bg-white text-slate-600 hover:bg-slate-100 transition-colors font-semibold shadow-sm">Next Page</button>
            </div>

        </div>
    );
}
