const API_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export const api = {
  get: (endpoint) => request(endpoint, { method: 'GET' }),
  post: (endpoint, data) =>
    request(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: (endpoint, data) =>
    request(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
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
      const formData = new FormData();
      formData.append('file', file);

      return fetch(`${API_URL}/projects/${projectId}/chapters`, {
        method: 'POST',
        body: formData,
      }).then((res) => res.json());
    },
    reorder: (projectId, order) =>
      api.put(`/projects/${projectId}/chapters/reorder`, { order }),
  },

  // Generate endpoints
  generate: {
    epub: (projectId, options) =>
      api.post(`/projects/${projectId}/generate/epub`, options),
    preview: (projectId) => api.get(`/projects/${projectId}/preview`),
  },
};

export default api;
