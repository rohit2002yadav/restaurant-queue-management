import { createContext, useContext, useState } from 'react';
import axios from 'axios';

const AuthContext = createContext();
const BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

export function AuthProvider({ children }) {
    const [user, setUser] = useState(() => {
        const u = localStorage.getItem('user');
        return u ? JSON.parse(u) : null;
    });

    const login = (userData, tokens) => {
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
        localStorage.setItem('user', JSON.stringify(userData));
        setUser(userData);
    };

    const logout = async () => {
        const refresh = localStorage.getItem('refresh_token');
        if (refresh) {
            try {
                // Blacklist the refresh token on the server so it cannot be reused
                await axios.post(`${BASE_URL}/auth/token/blacklist/`, { refresh });
            } catch {
                // Server unavailable or token already blacklisted — proceed with local logout anyway
            }
        }
        localStorage.clear();
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
