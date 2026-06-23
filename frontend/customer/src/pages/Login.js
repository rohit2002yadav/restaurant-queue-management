import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, Utensils } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import API from '../api';
import Input from '../components/Input';
import Button from '../components/Button';

export default function Login() {
    const [form, setForm] = useState({ email: '', password: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const res = await API.post('/auth/login/', form);
            login(res.data.user, res.data.tokens);
            if (res.data.user.role === 'admin') navigate('/admin/dashboard');
            else navigate('/customer/dashboard');
        } catch (err) {
            setError(err.response?.data?.error || 'Invalid email or password.');
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-orange-50 to-white flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-14 h-14 bg-orange-500 rounded-2xl mb-4 shadow-lg shadow-orange-200">
                        <Utensils className="w-7 h-7 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900">Welcome back</h1>
                    <p className="text-gray-500 mt-1">Sign in to your account</p>
                </div>

                {/* Card */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <Input label="Email Address" type="email" icon={Mail}
                            placeholder="you@example.com" value={form.email}
                            onChange={e => setForm({ ...form, email: e.target.value })} required />
                        <Input label="Password" type="password" icon={Lock}
                            placeholder="Enter your password" value={form.password}
                            onChange={e => setForm({ ...form, password: e.target.value })} required />

                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
                                {error}
                            </div>
                        )}

                        <Button type="submit" fullWidth loading={loading}>Sign In</Button>
                    </form>

                    <div className="mt-6 pt-6 border-t border-gray-100 space-y-3 text-center text-sm text-gray-500">
                        <p>Are you a restaurant admin? <Link to="/admin/register" className="text-orange-500 font-medium hover:underline">Register here</Link></p>
                        <p>New customer? <Link to="/customer/register" className="text-orange-500 font-medium hover:underline">Create account</Link></p>
                    </div>
                </div>

                <p className="text-center mt-6 text-sm text-gray-400">
                    <Link to="/" className="hover:text-orange-500 transition-colors">← Back to home</Link>
                </p>
            </div>
        </div>
    );
}
