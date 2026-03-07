export const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:5000";

export const ENDPOINTS = {
    LOGIN: "/api/auth/login",
    REFRESH: "/api/auth/refresh",
    LOGOUT: "/api/auth/logout",
    ME: "/api/auth/me",
    SHIPMENTS: "/api/shipments",
    INVOICES: "/api/invoices",
    INVOICES_UPLOAD: "/api/invoices/upload",
    COMPLIANCE: "/api/compliance",
    COMPLIANCE_ALERTS: "/api/compliance/alerts",
    COMPLIANCE_RUN: "/api/compliance/run",
    ANALYTICS_SUMMARY: "/api/analytics/summary",
    ANALYTICS_TRENDS: "/api/analytics/trends",
    ANALYTICS_SOURCES: "/api/analytics/source-split",
    ANALYTICS_COMPLIANCE: "/api/analytics/compliance-trend",
    ANOMALIES: "/api/anomalies",
    ANOMALIES_DETECT: "/api/anomalies/detect",
    QUERY: "/api/query",
    PIPELINE_STATUS: "/api/pipeline/status",
    PIPELINE_SCHEDULE: "/api/pipeline/schedule",
    PIPELINE_TRIGGER: "/api/pipeline/trigger"
};
