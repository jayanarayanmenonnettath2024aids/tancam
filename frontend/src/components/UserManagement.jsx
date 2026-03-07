import { useState, useEffect } from 'react';
import axios from '../api/axiosConfig';
import { ENDPOINTS } from '../api/endpoints';

export default function UserManagement() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [formData, setFormData] = useState({ email: '', password: '', full_name: '', role: 'user' });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const res = await axios.get(ENDPOINTS.USERS);
            setUsers(res.data);
            setError('');
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to load users');
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        try {
            await axios.post(ENDPOINTS.USERS, formData);
            setSuccess('User created successfully');
            setFormData({ email: '', password: '', full_name: '', role: 'user' });
            fetchUsers();
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to create user');
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this user?')) return;
        try {
            await axios.delete(`${ENDPOINTS.USERS}/${id}`);
            fetchUsers();
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to delete user');
        }
    };

    return (
        <div className="p-8 h-full flex flex-col gap-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-slate-800">User Management</h1>
                <p className="text-slate-500 mt-1">Manage platform access and roles.</p>
            </div>

            {error && <div className="p-4 bg-rose-50 text-rose-700 border border-rose-200 rounded-lg">{error}</div>}
            {success && <div className="p-4 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg">{success}</div>}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1">

                {/* Create User Form */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm h-fit">
                    <h3 className="text-lg font-bold text-slate-800 mb-4">Add New User</h3>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                            <input type="text" required value={formData.full_name} onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                                className="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                            <input type="email" required value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })}
                                className="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
                            <input type="password" required value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })}
                                className="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
                            <select value={formData.role} onChange={e => setFormData({ ...formData, role: e.target.value })}
                                className="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm bg-white focus:outline-none focus:border-blue-500">
                                <option value="user">User</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>
                        <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition-colors">
                            Create User
                        </button>
                    </form>
                </div>

                {/* User List Table */}
                <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden flex flex-col">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm text-slate-600">
                            <thead className="text-xs uppercase bg-slate-50 text-slate-500">
                                <tr>
                                    <th className="px-6 py-4 font-semibold">Name</th>
                                    <th className="px-6 py-4 font-semibold">Email</th>
                                    <th className="px-6 py-4 font-semibold">Role</th>
                                    <th className="px-6 py-4 font-semibold">Last Login</th>
                                    <th className="px-6 py-4 font-semibold text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {loading ? (
                                    <tr><td colSpan="5" className="text-center py-10 text-slate-400">Loading users...</td></tr>
                                ) : users.length === 0 ? (
                                    <tr><td colSpan="5" className="text-center py-10 text-slate-400">No users found.</td></tr>
                                ) : users.map(u => (
                                    <tr key={u.id} className="hover:bg-slate-50 transition-colors bg-white">
                                        <td className="px-6 py-4 font-medium text-slate-800">{u.full_name}</td>
                                        <td className="px-6 py-4">{u.email}</td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded text-xs uppercase font-bold tracking-wider ${u.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600'}`}>
                                                {u.role}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-slate-400">{u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}</td>
                                        <td className="px-6 py-4 text-right">
                                            <button onClick={() => handleDelete(u.id)} className="text-rose-500 hover:text-rose-700 font-medium px-3 py-1 bg-rose-50 hover:bg-rose-100 rounded transition-colors text-xs">
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>
        </div>
    );
}
