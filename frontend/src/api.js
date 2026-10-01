import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY;

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 90000, // 90 s — Ollama can be slow on first call
  headers: API_KEY ? { 'X-API-Key': API_KEY } : {},
});

export const ingestDocuments   = ()           => api.post('/ingest');
export const askQuestion       = (question)   => api.post('/ask', { question });
export const getDocuments      = ()           => api.get('/documents');
export const getAnalytics      = ()           => api.get('/analytics');
export const resetAll          = ()           => api.delete('/reset');
