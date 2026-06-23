import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Clock, Users, Bell, LogOut, Utensils, RefreshCw } from 'lucide-react';
import API from '../api';
import Loader from '../components/Loader';
import Toast from '../components/Toast';
import Button from '../components/Button';
import Badge from '../components/Badge';

export default function CustomerDashboard() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [toast, setToast] = useState(null);

    const token = localStorage.getItem('queue_token');
    const restaurantId = localStorage.getItem('queue_restaurant_id');

    const fetchStatus = useCallback(async () => {
        if (!token) { setLoading(false); return; }
        try {
            const res = await API.get(`/queue/queue-status/${token}/`);
            setStatus(res.data);
        } catch {
            setStatus(null);
        }
        setLoading(false);
    }, [token]);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 10000);
        return () => clearInterval(interval);
    }, [fetchStatus]);

    const handleLeave = async () => {
        try {
            await API.post('/queue/leave-queue/', { token, restaurant_id: restaurantId });
            localStorage.removeItem('queue_token');
            localStorage.removeItem('queue_restaurant_id');
            setToast({ message: 'You have left the queue.', type: 'success' });
            setTimeout(() => navigate('/join'), 1500);
        } catch {
            setToast({ message: 'Failed to leave queue.', type: 'error' });
        }
    };

    const handleLogout = () => { logout(); navigate('/login'); };

    const entry = status?.queue_entry;

    return (
        <div className="min-h-screen bg-gray-50">
            {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

            {/* Topbar */}
            <header className="bg-white border-b border-gray-100 sticky top-0 z-40">
                <div className="max-w-lg mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                            <Utensils className="w-4 h-4 text-white" />
                        </div>
                        <span className="font-bold text-gray-900">QueueEat</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <button onClick={fetchStatus} className="p-2 rounded-lg hover:bg-gray-100 text-gray-500">
                            <RefreshCw className="w-4 h-4" />
                        </button>
                        <button onClick={handleLogout}
                            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-500 px-3 py-2 rounded-lg hover:bg-red-50 transition-all">
                            <LogOut className="w-4 h-4" /> Logout
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-lg mx-auto px-6 py-8">
                {loading ? <Loader text="Loading your status..." /> :
                 !token || !status ? (
                    <div className="bg-white rounded-2xl border border-gray-100 p-10 text-center">
                        <div className="w-16 h-16 bg-orange-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                            <Utensils className="w-8 h-8 text-orange-400" />
                        </div>
                        <p className="font-semibold text-gray-900 mb-1">No active queue entry</p>
                        <p className="text-sm text-gray-500 mb-6">You're not in any queue right now.</p>
                        <Button onClick={() => navigate('/join')}>Join a Queue</Button>
                    </div>
                 ) : (
                    <div className="space-y-4">
                        {/* Token Card */}
                        <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
                            <p className="text-sm text-gray-500 mb-1">Your Token</p>
                            <p className="text-6xl font-black text-orange-500 mb-3">{entry.token_number}</p>
                            <Badge variant={
                                entry.status === 'waiting' ? 'warning' :
                                entry.status === 'called' ? 'info' :
                                entry.status === 'seated' ? 'success' : 'default'
                            }>
                                {entry.status.replace('_', ' ')}
                            </Badge>
                        </div>

                        {/* Status-specific content */}
                        {entry.status === 'seated' && (
                            <div className="bg-green-50 border border-green-200 rounded-2xl p-6 text-center">
                                <p className="text-2xl mb-2">✅</p>
                                <p className="font-bold text-green-800 text-lg">Table Assigned!</p>
                                <p className="text-green-700 text-sm mt-1">Please proceed to your table.</p>
                            </div>
                        )}

                        {entry.status === 'called' && (
                            <div className="bg-orange-50 border border-orange-200 rounded-2xl p-6 text-center">
                                <p className="text-2xl mb-2">📢</p>
                                <p className="font-bold text-orange-800 text-lg">You've Been Called!</p>
                                <p className="text-orange-700 text-sm mt-1">Please come to the restaurant within 10 minutes.</p>
                            </div>
                        )}

                        {entry.status === 'waiting' && (
                            <>
                                {/* Stats */}
                                <div className="grid grid-cols-3 gap-3">
                                    {[
                                        { icon: Users, label: 'Position', value: `#${status.position}`, color: 'bg-orange-500' },
                                        { icon: Bell, label: 'Ahead', value: status.people_ahead, color: 'bg-blue-500' },
                                        { icon: Clock, label: 'Est. Wait', value: `${entry.estimated_wait_mins}m`, color: 'bg-green-500' },
                                    ].map(({ icon: Icon, label, value, color }) => (
                                        <div key={label} className="bg-white rounded-2xl border border-gray-100 p-4 text-center">
                                            <div className={`w-8 h-8 ${color} rounded-lg flex items-center justify-center mx-auto mb-2`}>
                                                <Icon className="w-4 h-4 text-white" />
                                            </div>
                                            <p className="text-xl font-bold text-gray-900">{value}</p>
                                            <p className="text-xs text-gray-500">{label}</p>
                                        </div>
                                    ))}
                                </div>

                                <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 text-center text-sm text-blue-700">
                                    We'll notify you when your table is ready. You can wait anywhere!
                                </div>

                                <Button variant="danger" fullWidth onClick={handleLeave}>
                                    Leave Queue
                                </Button>
                            </>
                        )}

                        {/* Party info */}
                        <div className="bg-white rounded-2xl border border-gray-100 px-6 py-4 flex items-center justify-between text-sm text-gray-600">
                            <span>Party size</span>
                            <span className="font-semibold text-gray-900">{entry.party_size} guests</span>
                        </div>
                        {entry.special_request && (
                            <div className="bg-white rounded-2xl border border-gray-100 px-6 py-4 text-sm text-gray-600">
                                <span className="font-medium">Special request: </span>{entry.special_request}
                            </div>
                        )}
                    </div>
                 )
                }
            </main>
        </div>
    );
}
