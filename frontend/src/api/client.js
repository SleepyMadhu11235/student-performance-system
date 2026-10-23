import axios from 'axios'

// Vite exposes env vars prefixed VITE_ on import.meta.env.
// Normalizes the URL: strips trailing slashes and ensures /api prefix
const resolveApiBaseUrl = () => {
  const envUrl = (import.meta.env.VITE_API_BASE_URL || '').trim()
  if (!envUrl) {
    return 'http://localhost:8000/api'
  }
  const stripped = envUrl.replace(/\/+$/, '')
  return stripped.endsWith('/api') ? stripped : `${stripped}/api`
}

const API_BASE_URL = resolveApiBaseUrl()

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // 60-second timeout accommodates free-tier spinning services (Render cold-start wake-up)
  timeout: 60000,
})

export { API_BASE_URL }

/**
 * Every error response from the backend is shaped
 * { error: { code, message, details } } (see core/exceptions.py). This
 * interceptor unwraps that into a flat, predictable ApiError so components
 * never need to know about the envelope.
 */
export class ApiError extends Error {
  constructor(message, { code = 'UNKNOWN_ERROR', status = null, details = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.details = details
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const envelope = error.response.data?.error
      return Promise.reject(
        new ApiError(envelope?.message || 'The server returned an error.', {
          code: envelope?.code || 'SERVER_ERROR',
          status: error.response.status,
          details: envelope?.details ?? null,
        }),
      )
    }
    if (error.request) {
      return Promise.reject(
        new ApiError('Could not reach the server. If this is Render free tier, it may be waking up (give it 30-60s) or check your backend URL.', {
          code: 'NETWORK_ERROR',
        }),
      )
    }
    return Promise.reject(new ApiError(error.message, { code: 'CLIENT_ERROR' }))
  },
)

export default apiClient
