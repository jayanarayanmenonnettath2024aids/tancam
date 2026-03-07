import { NavLink } from 'react-router-dom';
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export default function Sidebar() {
    const { user, logout } = useContext(AuthContext);

    const links = [
        { to: "/dashboard", label: "Dashboard", icon: "📊" },
        { to: "/shipments", label: "Shipments", icon: "🚢" },
        { to: "/invoices", label: "Invoices", icon: "📄" },
        { to: "/compliance", label: "Compliance", icon: "🛡️" },
        { to: "/analytics", label: "Analytics", icon: "📈" },
        { to: "/anomalies", label: "Anomalies", icon: "⚠️" }
    ];

    if (user?.role === 'admin') {
        links.push({ to: "/pipeline", label: "Pipeline Control", icon: "⚡" });
        links.push({ to: "/users", label: "User Management", icon: "👥" });
    }

    return (
        <div className="w-64 bg-slate-950 h-screen flex flex-col border-r border-slate-800 shrink-0 shadow-xl z-20">
            <div className="p-6">
                <h1 className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500 truncate drop-shadow-md tracking-tight">UnifyOps</h1>
                <p className="text-[11px] text-slate-400 truncate tracking-wider uppercase mt-1 font-semibold">NovaCore Team</p>
            </div>
            <nav className="flex-1 px-3 space-y-1.5 overflow-y-auto mt-4">
                {links.map(l => (
                    <NavLink key={l.to} to={l.to}
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${isActive ? 'bg-blue-600/10 text-blue-400 font-semibold shadow-inner' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`
                        }>
                        <span className="text-lg opacity-80">{l.icon}</span>
                        <span>{l.label}</span>
                    </NavLink>
                ))}
            </nav>
            <div className="p-4 border-t border-slate-800/80 bg-slate-900/50">
                <div className="mb-4 flex items-center justify-between">
                    <div className="overflow-hidden">
                        <p className="text-slate-300 font-medium truncate text-sm">{user?.full_name}</p>
                        <span className="text-[10px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded inline-block uppercase tracking-wider font-bold mt-1">{user?.role}</span>
                    </div>
                </div>
                <button onClick={logout} className="w-full bg-red-500/10 text-red-400 hover:bg-red-500/20 py-2 rounded-lg text-sm font-medium transition-colors border border-red-500/20">
                    Log Out
                </button>
            </div>
        </div>
    );
}
