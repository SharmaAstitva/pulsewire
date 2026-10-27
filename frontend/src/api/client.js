import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: `${BASE}/api/v1`,
  timeout: 15000,
})

api.interceptors.response.use(
  (r) => r.data,
  (err) => Promise.reject(new Error(
    err.response?.data?.detail || err.message || 'Request failed'
  ))
)

export const getArticles    = (p) => api.get('/articles', { params: p })
export const getArticle     = (id) => api.get(`/articles/${id}`)
export const getTrending    = (p) => api.get('/trending',  { params: p })
export const getCategories  = ()  => api.get('/categories')
export const searchArticles = (p) => api.get('/search',   { params: p })
