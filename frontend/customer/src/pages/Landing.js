import { useNavigate } from 'react-router-dom';
import { Clock, Users, Bell, BarChart2, CheckCircle, ArrowRight, Utensils } from 'lucide-react';

export default function Landing() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-white font-sans">

            {/* Navbar */}
            <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur border-b border-gray-100">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                            <Utensils className="w-4 h-4 text-white" />
                        </div>
                        <span className="font-bold text-gray-900 text-lg">QueueEat</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <button onClick={() => navigate('/login')}
                            className="text-sm font-medium text-gray-600 hover:text-gray-900 px-4 py-2 rounded-lg hover:bg-gray-100 transition-all">
                            Login
                        </button>
                        <button onClick={() => navigate('/admin/register')}
                            className="text-sm font-semibold bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg transition-all">
                            Get Started
                        </button>
                    </div>
                </div>
            </nav>

            {/* Hero */}
            <section className="pt-32 pb-20 px-6 bg-gradient-to-br from-orange-50 via-white to-white">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="inline-flex items-center gap-2 bg-orange-100 text-orange-700 text-sm font-medium px-4 py-1.5 rounded-full mb-6">
                        <span className="w-2 h-2 bg-orange-500 rounded-full animate-pulse" />
                        Live Queue Management
                    </div>
                    <h1 className="text-5xl md:text-6xl font-extrabold text-gray-900 leading-tight mb-6">
                        Skip the Waiting.<br />
                        <span className="text-orange-500">Join the Queue Digitally.</span>
                    </h1>
                    <p className="text-xl text-gray-500 max-w-2xl mx-auto mb-10">
                        Track your restaurant queue position in real-time and know exactly when your table is ready. No more standing outside.
                    </p>
                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <button onClick={() => navigate('/join')}
                            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-orange-500 hover:bg-orange-600 text-white font-semibold px-8 py-4 rounded-xl transition-all shadow-lg shadow-orange-200">
                            Join Queue Now <ArrowRight className="w-5 h-5" />
                        </button>
                        <button onClick={() => navigate('/admin/register')}
                            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-white hover:bg-gray-50 text-gray-700 font-semibold px-8 py-4 rounded-xl border border-gray-200 transition-all">
                            Restaurant Login
                        </button>
                    </div>
                </div>

                {/* Dashboard Preview */}
                <div className="max-w-3xl mx-auto mt-16">
                    <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
                        <div className="bg-gray-50 border-b border-gray-100 px-4 py-3 flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-400" />
                            <div className="w-3 h-3 rounded-full bg-yellow-400" />
                            <div className="w-3 h-3 rounded-full bg-green-400" />
                            <span className="ml-2 text-xs text-gray-400">Queue Dashboard</span>
                        </div>
                        <div className="p-6 grid grid-cols-3 gap-4">
                            {[['12', 'Waiting'], ['4', 'Seated'], ['28 min', 'Avg Wait']].map(([val, label]) => (
                                <div key={label} className="bg-orange-50 rounded-xl p-4 text-center">
                                    <p className="text-2xl font-bold text-orange-500">{val}</p>
                                    <p className="text-xs text-gray-500 mt-1">{label}</p>
                                </div>
                            ))}
                        </div>
                        <div className="px-6 pb-6 space-y-3">
                            {[['T-001', 'Raj Kumar', '2', 'Waiting'], ['T-002', 'Meera Singh', '4', 'Called'], ['T-003', 'Vikram Patel', '6', 'Seated']].map(([token, name, guests, status]) => (
                                <div key={token} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                                    <span className="font-bold text-orange-500 text-sm">{token}</span>
                                    <span className="text-sm text-gray-700">{name}</span>
                                    <span className="text-xs text-gray-400">{guests} guests</span>
                                    <span className={`text-xs font-medium px-2 py-1 rounded-full ${status === 'Waiting' ? 'bg-yellow-100 text-yellow-700' : status === 'Called' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'}`}>{status}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* How it Works */}
            <section className="py-20 px-6 bg-white">
                <div className="max-w-5xl mx-auto">
                    <div className="text-center mb-14">
                        <h2 className="text-3xl font-bold text-gray-900 mb-4">How It Works</h2>
                        <p className="text-gray-500 max-w-xl mx-auto">Three simple steps to skip the line and enjoy your meal stress-free.</p>
                    </div>
                    <div className="grid md:grid-cols-3 gap-8">
                        {[
                            { step: '01', icon: Users, title: 'Join Digitally', desc: 'Scan the QR code at the entrance or visit the website to join the queue from your phone.' },
                            { step: '02', icon: Clock, title: 'Track in Real-Time', desc: 'See your position, estimated wait time, and how many people are ahead of you.' },
                            { step: '03', icon: Bell, title: 'Get Notified', desc: 'Receive instant notification when your table is ready. No more waiting outside.' },
                        ].map(({ step, icon: Icon, title, desc }) => (
                            <div key={step} className="relative p-6 bg-gray-50 rounded-2xl">
                                <span className="text-5xl font-black text-orange-100 absolute top-4 right-4">{step}</span>
                                <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center mb-4">
                                    <Icon className="w-6 h-6 text-white" />
                                </div>
                                <h3 className="font-bold text-gray-900 mb-2">{title}</h3>
                                <p className="text-gray-500 text-sm leading-relaxed">{desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className="py-20 px-6 bg-orange-50">
                <div className="max-w-5xl mx-auto">
                    <div className="text-center mb-14">
                        <h2 className="text-3xl font-bold text-gray-900 mb-4">Everything You Need</h2>
                        <p className="text-gray-500 max-w-xl mx-auto">Powerful features for restaurants and customers alike.</p>
                    </div>
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[
                            { icon: Clock, title: 'Real-time Wait Time', desc: 'Live estimated wait time updates for every customer.' },
                            { icon: Users, title: 'Smart Queue Management', desc: 'Best-fit table algorithm ensures no table is wasted.' },
                            { icon: Bell, title: 'Instant Notifications', desc: 'Customers are notified the moment their table is ready.' },
                            { icon: BarChart2, title: 'Analytics Dashboard', desc: 'Track queue stats, peak hours, and customer flow.' },
                            { icon: CheckCircle, title: 'Auto No-Show Detection', desc: 'System auto-handles no-shows and moves queue forward.' },
                            { icon: Utensils, title: 'Multi-Table Support', desc: 'Manage multiple tables with different capacities easily.' },
                        ].map(({ icon: Icon, title, desc }) => (
                            <div key={title} className="bg-white p-6 rounded-2xl border border-orange-100">
                                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                                    <Icon className="w-5 h-5 text-orange-500" />
                                </div>
                                <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
                                <p className="text-gray-500 text-sm">{desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA */}
            <section className="py-20 px-6 bg-orange-500">
                <div className="max-w-3xl mx-auto text-center">
                    <h2 className="text-3xl font-bold text-white mb-4">Ready to Eliminate the Wait?</h2>
                    <p className="text-orange-100 mb-8">Join hundreds of restaurants already using QueueEat to manage their queues smarter.</p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <button onClick={() => navigate('/admin/register')}
                            className="bg-white text-orange-500 font-semibold px-8 py-4 rounded-xl hover:bg-orange-50 transition-all">
                            Register Your Restaurant
                        </button>
                        <button onClick={() => navigate('/join')}
                            className="bg-orange-600 text-white font-semibold px-8 py-4 rounded-xl hover:bg-orange-700 transition-all border border-orange-400">
                            Join a Queue
                        </button>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-10 px-6 bg-gray-900 text-center">
                <div className="flex items-center justify-center gap-2 mb-4">
                    <div className="w-7 h-7 bg-orange-500 rounded-lg flex items-center justify-center">
                        <Utensils className="w-3.5 h-3.5 text-white" />
                    </div>
                    <span className="font-bold text-white">QueueEat</span>
                </div>
                <p className="text-gray-400 text-sm">© 2026 QueueEat. Built with ❤️ by Rohit Yadav.</p>
            </footer>
        </div>
    );
}
