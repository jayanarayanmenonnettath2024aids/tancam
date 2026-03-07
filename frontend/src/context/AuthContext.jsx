import React, { createContext, useState } from 'react';
import axios from '../api/axiosConfig';
import { ENDPOINTS } from '../api/endpoints';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')));
    const [token, setToken] = useState(localStorage.getItem('access_token'));

    const login = async (email, password) => {
        const res = await axios.post(ENDPOINTS.LOGIN, { email, password });
        setUser(res.data.user);
        setToken(res.data.access_token);
        localStorage.setItem('user', JSON.stringify(res.data.user));
        localStorage.setItem('access_token', res.data.access_token);
        if (res.data.refresh_token) {
            localStorage.setItem('refresh_token', res.data.refresh_token);
        }
    };

    const logout = async () => {
        try { await axios.post(ENDPOINTS.LOGOUT); } catch (e) { }
        setUser(null);
        setToken(null);
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    };

    const refreshToken = async () => {
        const refreshTk = localStorage.getItem('refresh_token');
        if (!refreshTk) throw new Error('No refresh token available');
        const res = await axios.post(ENDPOINTS.REFRESH, {}, {
            headers: { Authorization: `Bearer ${refreshTk}` }
        });
        const newToken = res.data.access_token;
        setToken(newToken);
        localStorage.setItem('access_token', newToken);
        return newToken;
    };

    return (
        <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, login, logout, refreshToken }}>
            {children}
        </AuthContext.Provider>
    );
};
