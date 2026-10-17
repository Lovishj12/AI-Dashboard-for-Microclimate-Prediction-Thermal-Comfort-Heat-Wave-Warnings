// Global Environment-aware API Base Configuration
// In production, configure VITE_API_BASE on Vercel/Netlify/Render to your backend URL (e.g., https://your-backend.onrender.com).
// If empty, falls back to local FastAPI development server at http://127.0.0.1:8000.

const rawApiBase = import.meta.env.VITE_API_BASE ? import.meta.env.VITE_API_BASE.replace(/\/+$/, '') : 'http://127.0.0.1:8000';

export const API_BASE = rawApiBase.endsWith('/api') ? rawApiBase : (rawApiBase + '/api');
