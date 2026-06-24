import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Landing from './pages/Landing';
import Login from './pages/Login';
import AdminRegister from './pages/AdminRegister';
import CustomerRegister from './pages/CustomerRegister';
import VerifyOTP from './pages/VerifyOTP';
import AdminDashboard from './pages/AdminDashboard';
import CustomerDashboard from './pages/CustomerDashboard';
import JoinQueue from './pages/JoinQueue';

function ProtectedRoute({ children, role }) {
    const { user } = useAuth();
    if (!user) return <Navigate to="/login" />;
    if (role && user.role !== role) return <Navigate to="/login" />;
    return children;
}

export default function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Landing />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/admin/register" element={<AdminRegister />} />
                    <Route path="/customer/register" element={<CustomerRegister />} />
                    <Route path="/verify-otp" element={<VerifyOTP />} />
                    <Route path="/join" element={<JoinQueue />} />
                    <Route path="/admin/dashboard" element={
                        <ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>
                    } />
                    <Route path="/customer/dashboard" element={
                        <ProtectedRoute role="customer"><CustomerDashboard /></ProtectedRoute>
                    } />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}
