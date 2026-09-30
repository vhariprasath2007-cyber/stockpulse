// API Configuration
// Uses Vite environment variable VITE_API_BASE, falls back to localhost for development
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';