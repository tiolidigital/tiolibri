import { supabase } from './supabase'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Authenticated fetch wrapper. Automatically attaches the Supabase JWT.
 *
 * Pass `options.skipContentType = true` for multipart requests so the browser
 * can set the correct Content-Type boundary itself.
 */
export async function authedFetch(path, options = {}) {
  const { skipContentType, headers: extraHeaders, ...fetchOptions } = options

  const {
    data: { session },
  } = await supabase.auth.getSession()

  const headers = {
    ...(skipContentType ? {} : { 'Content-Type': 'application/json' }),
    ...extraHeaders,
  }
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`
  }

  const res = await fetch(`${API_URL}${path}`, { ...fetchOptions, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || err.message || `HTTP ${res.status}`)
  }

  // 204 No Content (and any other empty response) → return null
  // instead of letting res.json() throw on empty body.
  if (res.status === 204) return null
  const contentType = res.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) return null

  return res.json()
}
