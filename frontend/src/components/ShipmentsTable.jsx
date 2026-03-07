import { useState, useEffect } from 'react';
import axios from '../api/axiosConfig';
import { ENDPOINTS } from '../api/endpoints';

export default function ShipmentsTable() {
    const [shipments, setShipments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [statusFilter, setStatusFilter] = useState('');
    const [search, setSearch] = useState('');

    const fetchShipments = async () => {
        setLoading(true);
        try {
            const res = await axios.get(ENDPOINTS.SHIPMENTS, {
                params: { page, per_page: 15, status: statusFilter, search }
            });
            setShipments(res.data.items);
            setTotalPages(res.data.pages);
        } catch (err) {
            console.error(err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchShipments();
    }, [page, statusFilter]);

    const handleSearch = (e) => {
        e.preventDefault();
        setPage(1);
        fetchShipments();
    };

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'cleared': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
            case 'held': return 'bg-orange-100 text-orange-700 border-orange-200';
            case 'rejected': return 'bg-rose-100 text-rose-700 border-rose-200';
            default: return 'bg-amber-100 text-amber-700 border-amber-200';
        }
    };

    return (
        <div className="p-8 h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold tracking-tight text-slate-800">Shipments</h1>

                <div className="flex gap-4">
                    <form onSubmit={handleSearch} className="flex relative">
                        <input type="text" placeholder="Search by Invoice No..." value={search} onChange={e => setSearch(e.target.value)}
                            className="border border-slate-300 rounded-l-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500 w-64" />
                        <button type="submit" className="bg-slate-100 border-y border-r border-slate-300 rounded-r-lg px-4 hover:bg-slate-200 transition-colors">🔍</button>
                    </form>
                    <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
                        className="border border-slate-300 rounded-lg px-4 py-2 text-sm bg-white focus:outline-none focus:border-blue-500">
                        <option value="">All Statuses</option>
                        <option value="pending">Pending</option>
                        <option value="cleared">Cleared</option>
                        <option value="held">Held</option>
                        <option value="rejected">Rejected</option>
                    </select>
                </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl shadow-sm flex-1 overflow-hidden flex flex-col">
                <div className="overflow-x-auto flex-1">
                    <table className="w-full text-left text-sm text-slate-600">
                        <thead className="text-xs uppercase bg-slate-50 text-slate-500 sticky top-0 shadow-sm z-10">
                            <tr>
                                <th className="px-6 py-4 font-semibold">Invoice No</th>
                                <th className="px-6 py-4 font-semibold">Value</th>
                                <th className="px-6 py-4 font-semibold">Status</th>
                                <th className="px-6 py-4 font-semibold">Source</th>
                                <th className="px-6 py-4 font-semibold">Loading Port</th>
                                <th className="px-6 py-4 font-semibold">Date</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                <tr><td colSpan="6" className="text-center py-10 text-slate-400">Loading records...</td></tr>
                            ) : shipments.length === 0 ? (
                                <tr><td colSpan="6" className="text-center py-10 text-slate-400">No shipments found.</td></tr>
                            ) : shipments.map(s => (
                                <tr key={s.id} className="hover:bg-blue-50/50 transition-colors cursor-pointer">
                                    <td className="px-6 py-4 font-medium text-blue-600">{s.invoice_no}</td>
                                    <td className="px-6 py-4 font-mono">{s.currency} {s.total_value?.toLocaleString() || '-'}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(s.status)}`}>
                                            {s.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-xs uppercase font-mono border border-slate-200">{s.source_system}</span>
                                    </td>
                                    <td className="px-6 py-4 truncate max-w-xs">{s.port_of_loading || '-'}</td>
                                    <td className="px-6 py-4">{s.shipment_date?.split('T')[0] || '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="border-t border-slate-200 p-4 bg-slate-50 flex justify-between items-center text-sm text-slate-500">
                    <div>Page {page} of {totalPages}</div>
                    <div className="flex gap-2">
                        <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-4 py-2 border border-slate-300 rounded-md bg-white disabled:opacity-50 hover:bg-slate-100 transition-colors font-medium">Previous</button>
                        <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)} className="px-4 py-2 border border-slate-300 rounded-md bg-white disabled:opacity-50 hover:bg-slate-100 transition-colors font-medium">Next</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
