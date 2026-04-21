import { authedFetch } from './authedFetch'

async function request(endpoint, options = {}) {
  return authedFetch(endpoint, options)
}

export const api = {
  get: (endpoint) => request(endpoint, { method: 'GET' }),
  post: (endpoint, data) => request(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: (endpoint, data) => request(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (endpoint) => request(endpoint, { method: 'DELETE' }),

  // Project endpoints
  projects: {
    list: () => api.get('/projects'),
    get: (id) => api.get(`/projects/${id}`),
    create: (data) => api.post('/projects', data),
    update: (id, data) => api.put(`/projects/${id}`, data),
    delete: (id) => api.delete(`/projects/${id}`),
  },

  // Chapter endpoints
  chapters: {
    list: (projectId) => api.get(`/projects/${projectId}/chapters`),
    upload: (projectId, file) => {
      const formData = new FormData()
      formData.append('file', file)
      return authedFetch(`/projects/${projectId}/chapters`, {
        method: 'POST',
        skipContentType: true,
        body: formData,
      })
    },
    reorder: (projectId, order) => api.post(`/projects/${projectId}/chapters/reorder`, { order }),
  },

  // Generate endpoints
  generate: {
    epub: (projectId, options) => api.post(`/projects/${projectId}/generate/epub`, options),
    preview: (projectId) => api.get(`/projects/${projectId}/preview`),
  },
}

export default api
