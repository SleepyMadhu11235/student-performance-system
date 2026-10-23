import axios from 'axios'

// Vite exposes env vars prefixed VITE_ on import.meta.env. Falls back to the
// Django dev server default so `npm run dev` works out of the box alongside
// `python manage.py runserver` with zero extra config.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
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
        new ApiError('Could not reach the server. Is the Django backend running?', {
          code: 'NETWORK_ERROR',
        }),
      )
    }
    return Promise.reject(new ApiError(error.message, { code: 'CLIENT_ERROR' }))
  },
)

export default apiClient
