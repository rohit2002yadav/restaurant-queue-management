export default function Button({ children, variant = 'primary', size = 'md', loading, fullWidth, onClick, type = 'button', disabled }) {
    const base = 'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed';
    const variants = {
        primary: 'bg-orange-500 hover:bg-orange-600 text-white shadow-sm',
        secondary: 'bg-white hover:bg-gray-50 text-gray-700 border border-gray-200',
        danger: 'bg-red-500 hover:bg-red-600 text-white',
        ghost: 'hover:bg-gray-100 text-gray-600',
    };
    const sizes = {
        sm: 'px-4 py-2 text-sm',
        md: 'px-6 py-3 text-sm',
        lg: 'px-8 py-4 text-base',
    };

    return (
        <button type={type} onClick={onClick} disabled={disabled || loading}
            className={`${base} ${variants[variant]} ${sizes[size]} ${fullWidth ? 'w-full' : ''}`}>
            {loading ? (
                <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Loading...
                </span>
            ) : children}
        </button>
    );
}
