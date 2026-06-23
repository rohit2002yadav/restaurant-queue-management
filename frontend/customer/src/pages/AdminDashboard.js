import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Clock, CheckCircle, PhoneCall, LogOut, Utensils, RefreshCw, Bell } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import API from '../api';
import Badge from '../components/Badge';
import Loader from '../components/Loader';
import Toast from '../components/Toast';

function StatCard({ icon: Icon, label, value, color }) {
    return (
        <div className="bg-white rounded-2xl border border-gray-100 p-6 flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
                <Icon className="w-6 h-6 text-white" />
            </div>
            <div>
                <p className="text-2xl font-bold text-gray-900">{value}</p>
                <p className="text-sm text-gray-500">{label}</p>
            </div>
        </div>
    );
}

function StatusBadge({ status }) {
    const map = { waiting: 'warning', called: 'info', seated: 'success', no_show: 'danger' };
    return <Badge variant={map[status] || 'default'}>{status.replace('_', ' ')}</Badge>;
}

export default function AdminDashboard() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [queue, setQueue] = useState([]);
    const [loading, setLoading] = useState(true);
    const [toast, setToast] = useState(null);
    const [actionLoading, setActionLoading] = useState(null);
    const restaurantId = user?.restaurant_id || 1;

    const fetchQueue = useCallback(async () => {
        try {
            const res = await API.get(`/queue/restaurant-queue/${restaurantId}/`);
            setQueue(res.data);
        } catch {
            setToast({ message: 'Failed to load queue.', type: 'error' });
        }
        setLoading(false);
    }, [restaurantId]);

    useEffect(() => {
        fetchQueue();
        const interval = setInterval(fetchQueue, 10000);
        return () => clearInterval(interval);
    }, [fetchQueue]);

    const handleCall = async (id) => {
        setActionLoading(id);
        try {
            const res = await API.post('/queue/call-customer/', { queue_entry_id: id });
            setToast({ message: res.data.message || 'Customer called!', type: 'success' });
            fetchQueue();
        } catch (err) {
            setToast({ message: err.response?.data?.error || 'Failed to call customer.', type: 'error' });
        }
        setActionLoading(null);
    };

    const handleLogout = () => { logout(); navigate('/login'); };
    const waiting = queue.filter(q => q.status === 'waiting').length;
    const called = queue.filter(q => q.status === 'called').length;

    return (
        <div className="min-h-screen bg-gray-50">
            {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

            {/* Topbar */}
            <header className="bg-white border-b border-gray-100 sticky top-0 z-40">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-orange-500 rounded-xl flex items-center justify-center">
                            <Utensils className="w-4 h-4 text-white" />
                        </div>
                        <div>
                            <p className="font-bold text-gray-900 text-sm">QueueEat</p>
                            <p className="text-xs text-gray-500">{user?.restaurant_name || 'Admin Dashboard'}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button onClick={fetchQueue} className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-all">
                            <RefreshCw className="w-4 h-4" />
                        </button>
                        <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                            <span className="text-xs font-bold text-orange-600">{user?.name?.[0]?.toUpperCase()}</span>
                        </div>
                        <button onClick={handleLogout}
                            className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-500 px-3 py-2 rounded-lg hover:bg-red-50 transition-all">
                            <LogOut className="w-4 h-4" /> Logout
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-6xl mx-auto px-6 py-8">
                <div className="mb-8">
                    <h1 className="text-2xl font-bold text-gray-900">Queue Dashboard</h1>
                    <p className="text-gray-500 mt-1">Manage your restaurant queue in real-time</p>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <StatCard icon={Users} label="Waiting" value={waiting} color="bg-yellow-400" />
                    <StatCard icon={Bell} label="Called" value={called} color="bg-blue-500" />
                    <StatCard icon={CheckCircle} label="Total in Queue" value={queue.length} color="bg-orange-500" />
                    <StatCard icon={Clock} label="Avg Wait" value="30m" color="bg-green-500" />
                </div>

                {/* Queue Table */}
                <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                        <h2 className="font-semibold text-gray-900">Current Queue</h2>
                        <span className="text-sm text-gray-400">Auto-refreshes every 10s</span>
                    </div>

                    {loading ? <Loader text="Loading queue..." /> :
                     queue.length === 0 ? (
                        <div className="py-20 text-center">
                            <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                <Users className="w-8 h-8 text-gray-400" />
                            </div>
                            <p className="font-medium text-gray-900">No customers waiting</p>
                            <p className="text-sm text-gray-400 mt-1">Queue is empty right now</p>
                        </div>
                     ) : (
                        <>
                            {/* Desktop Table */}
                            <div className="hidden md:block overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="bg-gray-50 text-left">
                                            {['Token', 'Customer', 'Party', 'Wait Time', 'Status', 'Action'].map(h => (
                                                <th key={h} className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-50">
                                        {queue.map(entry => (
                                            <tr key={entry.id} className="hover:bg-gray-50 transition-colors">
                                                <td className="px-6 py-4 font-bold text-orange-500">{entry.token_number}</td>
                                                <td className="px-6 py-4">
                                                    <p className="font-medium text-gray-900">{entry.customer_name}</p>
                                                    <p className="text-xs text-gray-400">{entry.customer_phone}</p>
                                                </td>
                                                <td className="px-6 py-4 text-gray-600">{entry.party_size} guests</td>
                                                <td className="px-6 py-4 text-gray-600">{entry.estimated_wait_mins} min</td>
                                                <td className="px-6 py-4"><StatusBadge status={entry.status} /></td>
                                                <td className="px-6 py-4">
                                                    <button onClick={() => handleCall(entry.id)}
                                                        disabled={actionLoading === entry.id || entry.status !== 'waiting'}
                                                        className="flex items-center gap-1.5 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all">
                                                        <PhoneCall className="w-3.5 h-3.5" />
                                                        {actionLoading === entry.id ? 'Calling...' : 'Call'}
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {/* Mobile Cards */}
                            <div className="md:hidden divide-y divide-gray-100">
                                {queue.map(entry => (
                                    <div key={entry.id} className="p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-bold text-orange-500 text-lg">{entry.token_number}</span>
                                            <StatusBadge status={entry.status} />
                                        </div>
                                        <p className="font-medium text-gray-900">{entry.customer_name}</p>
                                        <p className="text-sm text-gray-500 mt-1">Party: {entry.party_size} · Wait: {entry.estimated_wait_mins} min</p>
                                        <button onClick={() => handleCall(entry.id)}
                                            disabled={actionLoading === entry.id || entry.status !== 'waiting'}
                                            className="mt-3 w-full flex items-center justify-center gap-2 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-sm font-semibold py-2.5 rounded-xl transition-all">
                                            <PhoneCall className="w-4 h-4" />
                                            {actionLoading === entry.id ? 'Calling...' : 'Call Customer'}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </>
                     )
                    }
                </div>
            </main>
        </div>
    );
}
