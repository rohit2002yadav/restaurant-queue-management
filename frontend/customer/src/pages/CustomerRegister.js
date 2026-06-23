import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, User, Phone, Utensils } from 'lucide-react';
import API from '../api';
import Input from '../components/Input';
import Button from '../components/Button';

export default function CustomerRegister() {
    const [form, setForm] = useState({ name: '', phone: '', email: '', password: '', confirm_password: '' });
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const validate = () => {
        const e = {};
        if (!form.name) e.name = 'Name is required';
        if (!form.phone) e.phone = 'Phone number is required';
        if (!form.email) e.email = 'Email is required';
        if (form.password.length < 8) e.password = 'Password must be at least 8 characters';
        if (form.password !== form.confirm_password) e.confirm_password = 'Passwords do not match';
        return e;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const e2 = validate();
        if (Object.keys(e2).length) { setErrors(e2); return; }
        setLoading(true);
        setErrors({});
        try {
            await API.post('/auth/customer/register/', form);
            navigate('/verify-otp', { state: { email: form.email, purpose: 'registration' } });
        } catch (err) {
            setErrors({ general: err.response?.data?.error || 'Registration failed. Try again.' });
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-orange-50 to-white flex items-center justify-center px-4 py-10">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-14 h-14 bg-orange-500 rounded-2xl mb-4 shadow-lg shadow-orange-200">
                        <Utensils className="w-7 h-7 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900">Create your account</h1>
                    <p className="text-gray-500 mt-1">Join the queue smarter</p>
                </div>

                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <Input label="Full Name" icon={User} placeholder="Your full name"
                            value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                            error={errors.name} required />
                        <Input label="Phone Number" icon={Phone} placeholder="10-digit mobile number"
                            value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })}
                            error={errors.phone} required />
                        <Input label="Email Address" type="email" icon={Mail} placeholder="you@example.com"
                            value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}
                            error={errors.email} required />
                        <Input label="Password" type="password" icon={Lock} placeholder="Min 8 characters"
                            value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
                            error={errors.password} required />
                        <Input label="Confirm Password" type="password" icon={Lock} placeholder="Repeat password"
                            value={form.confirm_password} onChange={e => setForm({ ...form, confirm_password: e.target.value })}
                            error={errors.confirm_password} required />

                        {errors.general && (
                            <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
                                {errors.general}
                            </div>
                        )}

                        <Button type="submit" fullWidth loading={loading}>Create Account</Button>
                    </form>

                    <p className="text-center mt-6 text-sm text-gray-500">
                        Already have an account? <Link to="/login" className="text-orange-500 font-medium hover:underline">Sign in</Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
