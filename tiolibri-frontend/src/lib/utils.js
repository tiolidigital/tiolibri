/**
 * Combines class names, filtering out falsy values
 */
export function cn(...classes) {
  return classes.filter(Boolean).join(' ')
}

/**
 * Formats a date to a readable string
 */
export function formatDate(date, options = {}) {
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options,
  }
  return new Date(date).toLocaleDateString('pl-PL', defaultOptions)
}

/**
 * Formats file size to human readable format
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * Generates a unique ID
 */
export function generateId() {
  return Math.random().toString(36).substring(2, 9)
}

/**
 * Debounce function
 */
export function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Truncates text to specified length
 */
export function truncate(text, length = 100) {
  if (!text || text.length <= length) return text
  return text.substring(0, length) + '...'
}

/**
 * Formats a date to relative time (e.g., "2d ago", "5h ago")
 */
export function timeAgo(date) {
  const now = new Date()
  const past = new Date(date)
  const diffMs = now - past
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffDay > 30) return formatDate(date)
  if (diffDay > 0) return `${diffDay}d ago`
  if (diffHour > 0) return `${diffHour}h ago`
  if (diffMin > 0) return `${diffMin}m ago`
  return 'just now'
}
