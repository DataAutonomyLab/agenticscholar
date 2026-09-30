import React, { useState } from 'react';
// Removed simulateApiCall and generateId from mockApi, as backend will handle IDs
import { Brain, Loader2 } from 'lucide-react';

// Define your Node.js backend URL
const NODE_API_URL = process.env.REACT_APP_NODE_API_URL || 'http://localhost:3001/api';

function AuthForm({ isLogin, setCurrentPage, onLoginSuccess }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState(''); // For signup
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const endpoint = isLogin ? `${NODE_API_URL}/auth/login` : `${NODE_API_URL}/auth/signup`;
        const payload = isLogin ? { email, password } : { email, password, name };

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || `HTTP error! status: ${response.status}`);
            }

            // Assuming backend sends back { user: { id, email, name }, token, message }
            if (data.user && data.token) {
                localStorage.setItem('synapseToken', data.token); // Store the token
                onLoginSuccess(data.user); // Pass user data to App.js
            } else {
                throw new Error(data.message || 'Login/Signup failed: Invalid response from server.');
            }

        } catch (err) {
            setError(err.message || "Authentication failed. Please try again.");
            console.error("Auth error:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex flex-col items-center justify-center p-4" style={{ backgroundColor: 'var(--bg-primary)' }}>
            <div className="w-full max-w-md shadow-2xl rounded-xl p-8" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
                <div className="flex flex-col items-center mb-8">
                    <Brain className="h-16 w-16 mb-3" style={{ color: 'var(--primary-color)' }} />
                    <h1 className="text-4xl font-bold" style={{ color: 'var(--text-primary)' }}>SYNAPSE</h1>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {!isLogin && (
                        <div>
                            <label htmlFor="name" className="block text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Name</label>
                            <input
                                id="name"
                                name="name"
                                type="text"
                                required={!isLogin}
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="mt-1 block w-full px-4 py-3 rounded-lg transition focus:outline-none focus:ring-2"
                                style={{
                                    backgroundColor: 'var(--bg-tertiary)',
                                    border: '1px solid var(--border-color)',
                                    color: 'var(--text-primary)'
                                }}
                                onFocus={(e) => {
                                    e.target.style.borderColor = 'var(--primary-color)';
                                    e.target.style.boxShadow = `0 0 0 2px ${window.getComputedStyle(document.documentElement).getPropertyValue('--primary-color')}33`;
                                }}
                                onBlur={(e) => {
                                    e.target.style.borderColor = 'var(--border-color)';
                                    e.target.style.boxShadow = 'none';
                                }}
                                placeholder="Your Name"
                            />
                        </div>
                    )}
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Email</label>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            autoComplete="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="mt-1 block w-full px-4 py-3 rounded-lg transition focus:outline-none focus:ring-2"
                            style={{
                                backgroundColor: 'var(--bg-tertiary)',
                                border: '1px solid var(--border-color)',
                                color: 'var(--text-primary)'
                            }}
                            onFocus={(e) => {
                                e.target.style.borderColor = 'var(--primary-color)';
                                e.target.style.boxShadow = `0 0 0 2px ${window.getComputedStyle(document.documentElement).getPropertyValue('--primary-color')}33`;
                            }}
                            onBlur={(e) => {
                                e.target.style.borderColor = 'var(--border-color)';
                                e.target.style.boxShadow = 'none';
                            }}
                            placeholder="you@example.com"
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Password</label>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            autoComplete="current-password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="mt-1 block w-full px-4 py-3 rounded-lg transition focus:outline-none focus:ring-2"
                            style={{
                                backgroundColor: 'var(--bg-tertiary)',
                                border: '1px solid var(--border-color)',
                                color: 'var(--text-primary)'
                            }}
                            onFocus={(e) => {
                                e.target.style.borderColor = 'var(--primary-color)';
                                e.target.style.boxShadow = `0 0 0 2px ${window.getComputedStyle(document.documentElement).getPropertyValue('--primary-color')}33`;
                            }}
                            onBlur={(e) => {
                                e.target.style.borderColor = 'var(--border-color)';
                                e.target.style.boxShadow = 'none';
                            }}
                            placeholder="••••••••"
                        />
                    </div>

                    {error && (
                        <p className="text-sm p-3 rounded-md" style={{ 
                            color: 'var(--error-color)', 
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            border: '1px solid rgba(239, 68, 68, 0.2)'
                        }}>{error}</p>
                    )}

                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium transition focus:outline-none focus:ring-2"
                            style={{
                                backgroundColor: loading ? 'var(--bg-muted)' : 'var(--primary-color)',
                                color: 'white',
                                opacity: loading ? 0.6 : 1
                            }}
                            onMouseOver={(e) => {
                                if (!loading) {
                                    e.target.style.backgroundColor = 'var(--primary-dark)';
                                }
                            }}
                            onMouseOut={(e) => {
                                if (!loading) {
                                    e.target.style.backgroundColor = 'var(--primary-color)';
                                }
                            }}
                            onFocus={(e) => {
                                e.target.style.boxShadow = `0 0 0 2px ${window.getComputedStyle(document.documentElement).getPropertyValue('--primary-color')}33`;
                            }}
                            onBlur={(e) => {
                                e.target.style.boxShadow = 'none';
                            }}
                        >
                            {loading ? <Loader2 className="animate-spin h-5 w-5" /> : (isLogin ? 'Log in' : 'Sign up')}
                        </button>
                    </div>
                </form>

                <p className="mt-8 text-center text-sm" style={{ color: 'var(--text-tertiary)' }}>
                    {isLogin ? "Don't have an account?" : "Already have an account?"}
                    <button
                        onClick={() => setCurrentPage(isLogin ? 'signup' : 'login')}
                        className="ml-1 font-medium transition-colors"
                        style={{ color: 'var(--primary-color)' }}
                        onMouseOver={(e) => e.target.style.color = 'var(--primary-dark)'}
                        onMouseOut={(e) => e.target.style.color = 'var(--primary-color)'}
                    >
                        {isLogin ? 'Sign up' : 'Log in'}
                    </button>
                </p>
            </div>
        </div>
    );
}

export default AuthForm;
