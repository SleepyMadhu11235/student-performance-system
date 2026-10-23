import { apiClient, API_BASE_URL } from './client'

/** GET /api/dashboard */
export async function getDashboard() {
  const { data } = await apiClient.get('/dashboard')
  return data
}

/** GET /api/history?student_id=&predicted_label=&page=&page_size= */
export async function getHistory({ studentId = '', predictedLabel = '', page = 1, pageSize = 10 } = {}) {
  const { data } = await apiClient.get('/history', {
    params: {
      student_id: studentId || undefined,
      predicted_label: predictedLabel && predictedLabel !== 'All' ? predictedLabel : undefined,
      page,
      page_size: pageSize,
    },
  })
  return data // { count, next, previous, results }
}

/** DELETE /api/history/<id> */
export async function deleteHistoryRecord(id) {
  await apiClient.delete(`/history/${id}`)
}

/**
 * GET /api/export/csv?... — this is a plain browser download, not an XHR
 * call, so it never touches CORS and streams straight from Django.
 */
export function buildExportCsvUrl({ studentId = '', predictedLabel = '' } = {}) {
  const params = new URLSearchParams()
  if (studentId) params.set('student_id', studentId)
  if (predictedLabel && predictedLabel !== 'All') params.set('predicted_label', predictedLabel)
  const query = params.toString()
  return `${API_BASE_URL}/export/csv${query ? `?${query}` : ''}`
}

/** GET /api/models */
export async function getModels() {
  const { data } = await apiClient.get('/models')
  return data
}

/** POST /api/retrain */
export async function triggerRetrain(options = {}) {
  const { data } = await apiClient.post('/retrain', options)
  return data
}

/** POST /api/predict */
export async function predictSingle(features) {
  const { data } = await apiClient.post('/predict', features)
  return data
}

/** POST /api/upload-csv (multipart) */
export async function uploadCsv(file, onUploadProgress) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post('/upload-csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  })
  return data
}
