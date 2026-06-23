import { useNavigate } from 'react-router-dom';
import { Utensils, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => { logout(); navigate('/login'); };

    return (
        <nav className="bg-white border-b border-gray-100 sticky top-0 z-40">
            <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
                    <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                        <Utensils className="w-4 h-4 text-white" />
                    </div>
                    <span className="font-bold text-gray-900 text-lg">QueueEat</span>
                </div>

                <div className="flex items-center gap-3">
                    {user ? (
                        <>
                            <span className="text-sm text-gray-500 hidden sm:block">{user.name}</span>
                            <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                                <span className="text-xs font-bold text-orange-600">{user.name?.[0]?.toUpperCase()}</span>
                            </div>
                            <button onClick={handleLogout}
                                className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-500 px-3 py-2 rounded-lg hover:bg-red-50 transition-all">
                                <LogOut className="w-4 h-4" /> Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <button onClick={() => navigate('/login')}
                                className="text-sm font-medium text-gray-600 hover:text-gray-900 px-4 py-2 rounded-lg hover:bg-gray-100 transition-all">
                                Login
                            </button>
                            <button onClick={() => navigate('/admin/register')}
                                className="text-sm font-semibold bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg transition-all">
                                Get Started
                            </button>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
}
