import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, MessageSquare, Utensils, CheckCircle, Clock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import API from '../api';
import Input from '../components/Input';
import Button from '../components/Button';

export default function JoinQueue() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [form, setForm] = useState({ name: '', phone: '', party_size: '', special_request: '' });
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const restaurantId = user?.restaurant_id || 1;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const payload = {
                name: user ? user.name : form.name,
                phone: user ? user.phone : form.phone,
                party_size: parseInt(form.party_size),
                special_request: form.special_request,
                restaurant_id: restaurantId,
            };
            const res = await API.post('/queue/join-queue/', payload);
            localStorage.setItem('queue_token', res.data.token);
            localStorage.setItem('queue_restaurant_id', restaurantId);
            setResult(res.data);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to join queue.');
        }
        setLoading(false);
    };

    if (result) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-orange-50 to-white flex items-center justify-center px-4">
                <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
                    <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                        <CheckCircle className="w-8 h-8 text-green-500" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900 mb-1">You're in!</h1>
                    <p className="text-gray-500 mb-6">Your queue entry has been confirmed.</p>

                    <div className="bg-orange-50 rounded-2xl p-6 mb-6">
                        <p className="text-sm text-gray-500 mb-1">Your Token</p>
                        <p className="text-5xl font-black text-orange-500">{result.token}</p>
                    </div>

                    {result.status === 'seated' ? (
                        <div className="bg-green-50 rounded-xl p-4 mb-6">
                            <p className="font-bold text-green-700 text-lg">✅ Table Assigned!</p>
                            <p className="text-green-600 mt-1">Table: <strong>{result.table}</strong></p>
                            <p className="text-sm text-green-600 mt-1">Please proceed to your table.</p>
                        </div>
                    ) : (
                        <div className="bg-blue-50 rounded-xl p-4 mb-6 flex items-center justify-center gap-3">
                            <Clock className="w-5 h-5 text-blue-500" />
                            <div className="text-left">
                                <p className="font-semibold text-blue-700">Added to queue</p>
                                <p className="text-sm text-blue-600">Estimated wait: <strong>{result.wait_time} mins</strong></p>
                            </div>
                        </div>
                    )}

                    <Button fullWidth onClick={() => navigate('/customer/dashboard')}>
                        View My Status
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-orange-50 to-white flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-14 h-14 bg-orange-500 rounded-2xl mb-4 shadow-lg shadow-orange-200">
                        <Utensils className="w-7 h-7 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900">Join the Queue</h1>
                    <p className="text-gray-500 mt-1">Enter your details to get a token</p>
                </div>

                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {!user && (
                            <>
                                <Input label="Your Name" placeholder="Full name"
                                    value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
                                <Input label="Phone Number" placeholder="10-digit mobile number"
                                    value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} required />
                            </>
                        )}

                        <Input label="Party Size" type="number" icon={Users}
                            placeholder="How many people?" min="1" max="20"
                            value={form.party_size} onChange={e => setForm({ ...form, party_size: e.target.value })} required />

                        <Input label="Special Request (optional)" icon={MessageSquare}
                            placeholder="e.g. window seat, high chair..."
                            value={form.special_request} onChange={e => setForm({ ...form, special_request: e.target.value })} />

                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
                                {error}
                            </div>
                        )}

                        <Button type="submit" fullWidth loading={loading}>
                            Join Queue
                        </Button>
                    </form>

                    {!user && (
                        <p className="text-center mt-6 text-sm text-gray-500">
                            Have an account?{' '}
                            <button onClick={() => navigate('/login')} className="text-orange-500 font-medium hover:underline">
                                Login
                            </button>
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}
