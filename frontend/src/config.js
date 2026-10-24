// Global Environment-aware API Base Configuration
// Supports both VITE_API_BASE and VITE_API_URL for zero-confusion deployment.
// If empty, falls back to local FastAPI development server at http://127.0.0.1:8000.

const envUrl = import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_URL || '';
const rawApiBase = envUrl ? envUrl.replace(/\/+$/, '') : 'http://127.0.0.1:8000';

export const API_BASE = rawApiBase.endsWith('/api') ? rawApiBase : (rawApiBase + '/api');
