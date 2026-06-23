import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, Users, LogOut, Utensils, RefreshCw, CheckCircle, Bell } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import API from '../api';
import Loader from '../components/Loader';
import Toast from '../components/Toast';

export default function CustomerDashboard() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [toast, setToast] = useState(null);

    const fetchStatus = useCallback(async () => {
        try {
            const res = await API.get('/queue/customer-status/');
            setStatus(res.data);
        } catch {
            setStatus(null);
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 10000);
        return () => clearInterval(interval);
    }, [fetchStatus]);

    const handleLeave = async () => {
        try {
            await API.post('/queue/leave-queue/', {
                token: status.queue_entry.token_number,
                restaurant_id: status.queue_entry.restaurant,
            });
            setToast({ message: 'You have left the queue.', type: 'success' });
            setStatus(null);
        } catch {
            setToast({ message: 'Failed to leave queue.', type: 'error' });
        }
    };

    const handleLogout = () => { logout(); navigate('/login'); };

    const getStatusColor = (s) => {
        if (s === 'seated') return 'text-green-500';
        if (s === 'called') return 'text-blue-500';
        return 'text-orange-500';
    };

    const getStatusIcon = (s) => {
        if (s === 'seated') return <CheckCircle className="w-8 h-8 text-green-500" />;
        if (s === 'called') return <Bell className="w-8 h-8 text-blue-500" />;
        return <Clock className="w-8 h-8 text-orange-500" />;
    };

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
                {/* Welcome */}
                <div className="mb-6">
                    <h1 className="text-2xl font-bold text-gray-900">Hello, {user?.name?.split(' ')[0]} 👋</h1>
                    <p className="text-gray-500 mt-1">Here's your queue status</p>
                </div>

                {loading ? <Loader text="Checking your status..." /> :
                 !status ? (
                    <div className="bg-white rounded-2xl border border-gray-100 p-10 text-center">
                        <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                            <Users className="w-8 h-8 text-gray-400" />
                        </div>
                        <p className="font-semibold text-gray-900 mb-1">Not in any queue</p>
                        <p className="text-sm text-gray-400 mb-6">Join a queue to track your position</p>
                        <button onClick={() => navigate('/join')}
                            className="bg-orange-500 hover:bg-orange-600 text-white font-semibold px-6 py-3 rounded-xl transition-all">
                            Join a Queue
                        </button>
                    </div>
                 ) : (
                    <div className="space-y-4">
                        {/* Token Card */}
                        <div className="bg-white rounded-2xl border border-gray-100 p-6">
                            <div className="flex items-center justify-between mb-4">
                                <p className="text-sm font-medium text-gray-500">Your Token</p>
                                {getStatusIcon(status.status)}
                            </div>
                            <p className="text-6xl font-black text-orange-500 mb-2">{status.queue_entry?.token_number}</p>
                            <p className={`text-sm font-semibold capitalize ${getStatusColor(status.status)}`}>
                                {status.status?.replace('_', ' ')}
                            </p>
                        </div>

                        {/* Status Message */}
                        {status.status === 'seated' && (
                            <div className="bg-green-50 border border-green-200 rounded-2xl p-5 text-center">
                                <CheckCircle className="w-10 h-10 text-green-500 mx-auto mb-2" />
                                <p className="font-bold text-green-800">Your table is ready!</p>
                                <p className="text-sm text-green-600 mt-1">Please proceed to your table.</p>
                            </div>
                        )}

                        {status.status === 'called' && (
                            <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 text-center">
                                <Bell className="w-10 h-10 text-blue-500 mx-auto mb-2" />
                                <p className="font-bold text-blue-800">You've been called!</p>
                                <p className="text-sm text-blue-600 mt-1">Please come to the restaurant within 10 minutes.</p>
                            </div>
                        )}

                        {status.status === 'waiting' && (
                            <>
                                {/* Stats */}
                                <div className="grid grid-cols-3 gap-3">
                                    {[
                                        { label: 'Position', value: `#${status.position}` },
                                        { label: 'Ahead', value: status.people_ahead },
                                        { label: 'Wait', value: `${status.queue_entry?.estimated_wait_mins}m` },
                                    ].map(({ label, value }) => (
                                        <div key={label} className="bg-white rounded-2xl border border-gray-100 p-4 text-center">
                                            <p className="text-2xl font-bold text-orange-500">{value}</p>
                                            <p className="text-xs text-gray-500 mt-1">{label}</p>
                                        </div>
                                    ))}
                                </div>

                                {/* Progress Bar */}
                                <div className="bg-white rounded-2xl border border-gray-100 p-5">
                                    <div className="flex justify-between text-sm mb-2">
                                        <span className="text-gray-500">Queue Progress</span>
                                        <span className="font-medium text-gray-700">Position #{status.position}</span>
                                    </div>
                                    <div className="w-full bg-gray-100 rounded-full h-2.5">
                                        <div className="bg-orange-500 h-2.5 rounded-full transition-all duration-500"
                                            style={{ width: `${Math.max(10, 100 - (status.people_ahead * 20))}%` }} />
                                    </div>
                                    <p className="text-xs text-gray-400 mt-2">We'll notify you when your table is ready</p>
                                </div>

                                <button onClick={handleLeave}
                                    className="w-full bg-red-50 hover:bg-red-100 text-red-600 font-semibold py-3.5 rounded-xl border border-red-200 transition-all">
                                    Leave Queue
                                </button>
                            </>
                        )}
                    </div>
                 )
                }
            </main>
        </div>
    );
}
