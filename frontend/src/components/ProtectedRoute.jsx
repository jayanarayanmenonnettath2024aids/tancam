import { Navigate } from 'react-router-dom';
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export default function ProtectedRoute({ children, role }) {
    const { isAuthenticated, user } = useContext(AuthContext);
    if (!isAuthenticated) return <Navigate to="/login" />;
    if (role && user?.role !== role) {
        return <Navigate to="/dashboard" />;
    }
    return children;
}
