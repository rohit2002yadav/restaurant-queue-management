export default function Loader({ text = 'Loading...' }) {
    return (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-10 h-10 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin" />
            <p className="text-gray-500 text-sm">{text}</p>
        </div>
    );
}
