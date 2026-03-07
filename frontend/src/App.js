import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

import Login from './components/Login';
import Sidebar from './components/Sidebar';
import VoiceQuery from './components/VoiceQuery';

import Dashboard from './components/Dashboard';
import ShipmentsTable from './components/ShipmentsTable';
import InvoiceViewer from './components/InvoiceViewer';
import ComplianceAlerts from './components/ComplianceAlerts';
import AnalyticsCharts from './components/AnalyticsCharts';
import AnomalyPanel from './components/AnomalyPanel';
import PipelineControl from './components/PipelineControl';

function Layout({ children }) {
  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <VoiceQuery />
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
          <Route path="/shipments" element={<ProtectedRoute><Layout><ShipmentsTable /></Layout></ProtectedRoute>} />
          <Route path="/invoices" element={<ProtectedRoute><Layout><InvoiceViewer /></Layout></ProtectedRoute>} />
          <Route path="/compliance" element={<ProtectedRoute><Layout><ComplianceAlerts /></Layout></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><Layout><AnalyticsCharts /></Layout></ProtectedRoute>} />
          <Route path="/anomalies" element={<ProtectedRoute><Layout><AnomalyPanel /></Layout></ProtectedRoute>} />
          <Route path="/pipeline" element={<ProtectedRoute role="admin"><Layout><PipelineControl /></Layout></ProtectedRoute>} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
