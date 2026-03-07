import axios from 'axios';
import { API_BASE } from './endpoints';

const instance = axios.create({
    baseURL: API_BASE,
});

instance.interceptors.request.use(config => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

instance.interceptors.response.use(
    response => response,
    error => {
        if (error.response && error.response.status === 401 && !window.location.pathname.includes('/login')) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default instance;
