import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Mail, Utensils } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import API from '../api';
import Button from '../components/Button';

export default function VerifyOTP() {
    const [otp, setOtp] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [resent, setResent] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const email = location.state?.email;
    const purpose = location.state?.purpose || 'registration';

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const res = await API.post('/auth/verify-otp/', { email, otp, purpose });
            if (purpose === 'login' && res.data.tokens) {
                login(res.data.user, res.data.tokens);
                if (res.data.user.role === 'admin') navigate('/admin/dashboard');
                else navigate('/customer/dashboard');
            } else {
                navigate('/login');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Invalid OTP. Please try again.');
        }
        setLoading(false);
    };

    const handleResend = async () => {
        try {
            await API.post('/auth/resend-otp/', { email, purpose });
            setResent(true);
            setTimeout(() => setResent(false), 3000);
        } catch {
            setError('Failed to resend OTP.');
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-orange-50 to-white flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-14 h-14 bg-orange-500 rounded-2xl mb-4 shadow-lg shadow-orange-200">
                        <Utensils className="w-7 h-7 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900">Verify your email</h1>
                    <p className="text-gray-500 mt-1">We sent a code to <span className="font-medium text-gray-700">{email}</span></p>
                </div>

                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
                    <div className="flex items-center justify-center w-16 h-16 bg-orange-100 rounded-2xl mx-auto mb-6">
                        <Mail className="w-8 h-8 text-orange-500" />
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1.5">Enter OTP</label>
                            <input
                                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent text-center text-2xl font-bold tracking-widest text-gray-900"
                                placeholder="000000"
                                value={otp}
                                onChange={e => setOtp(e.target.value)}
                                maxLength={6}
                                required
                            />
                        </div>

                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
                                {error}
                            </div>
                        )}

                        {resent && (
                            <div className="bg-green-50 border border-green-200 text-green-700 text-sm px-4 py-3 rounded-xl">
                                OTP resent successfully!
                            </div>
                        )}

                        <Button type="submit" fullWidth loading={loading}>Verify Email</Button>
                    </form>

                    <p className="text-center mt-6 text-sm text-gray-500">
                        Didn't receive the code?{' '}
                        <button onClick={handleResend} className="text-orange-500 font-medium hover:underline">
                            Resend OTP
                        </button>
                    </p>
                    <p className="text-center mt-3 text-sm text-gray-400">
                        <Link to="/login" className="hover:text-orange-500">← Back to login</Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
