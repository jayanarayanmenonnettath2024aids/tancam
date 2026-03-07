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
    };

    const logout = async () => {
        try { await axios.post(ENDPOINTS.LOGOUT); } catch (e) { }
        setUser(null);
        setToken(null);
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
    };

    return (
        <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};
