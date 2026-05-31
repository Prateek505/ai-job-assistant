/**
 * Axios HTTP client with JWT interceptor.
 * All API calls go through this client so auth tokens are injected automatically.
 */

import axios from 'axios'

const api = axios.create({
    // In production: served from same domain, so '/api' works perfectly.
    // VITE_API_URL can override for separate backend deployments.
    baseURL: import.meta.env.VITE_API_URL ?? '/api',
    headers: { 'Content-Type': 'application/json' },
})

// Inject JWT token on every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Handle 401 responses globally
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

export default api
