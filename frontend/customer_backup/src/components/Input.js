import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

export default function Input({ label, type = 'text', error, icon: Icon, ...props }) {
    const [show, setShow] = useState(false);
    const isPassword = type === 'password';

    return (
        <div className="w-full">
            {label && <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>}
            <div className="relative">
                {Icon && <Icon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />}
                <input
                    type={isPassword && show ? 'text' : type}
                    className={`w-full px-4 py-3 rounded-xl border transition-all duration-200 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent
                        ${Icon ? 'pl-10' : ''}
                        ${isPassword ? 'pr-10' : ''}
                        ${error ? 'border-red-400 bg-red-50' : 'border-gray-200 bg-white'}`}
                    {...props}
                />
                {isPassword && (
                    <button type="button" onClick={() => setShow(!show)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                        {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                )}
            </div>
            {error && <p className="mt-1.5 text-sm text-red-500">{error}</p>}
        </div>
    );
}
