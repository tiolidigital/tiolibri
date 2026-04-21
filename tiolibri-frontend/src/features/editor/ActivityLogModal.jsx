import { useState, useEffect, useCallback } from 'react'
import { authedFetch } from '../../lib/authedFetch'
import { actionLabel, authorInitial } from './activityLabels'

function formatDate(isoString) {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleDateString('pl-PL', { day: 'numeric', month: 'long', year: 'numeric' })
}

function formatTime(isoString) {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })
}

function todayLabel(isoString) {
  if (!isoString) return formatDate(isoString)
  const d = new Date(isoString)
  const now = new Date()
  const diffDays = Math.floor((now - d) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'Dziś'
  if (diffDays === 1) return 'Wczoraj'
  return formatDate(isoString)
}

const PAGE_SIZE = 30

export default function ActivityLogModal({ projectId, onClose }) {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [offset, setOffset] = useState(0)

  const loadMore = useCallback(async (currentOffset = 0, append = false) => {
    setLoading(true)
    try {
      const data = await authedFetch(
        `/projects/${projectId}/activity?limit=${PAGE_SIZE}&offset=${currentOffset}`
      )
      const fetched = data.events || []
      setEvents(prev => append ? [...prev, ...fetched] : fetched)
      setHasMore(fetched.length === PAGE_SIZE)
      setOffset(currentOffset + fetched.length)
    } catch (err) {
      console.error('Failed to load activity:', err)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    loadMore(0, false)
  }, [loadMore])

  // Close on Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  // Group events by day label
  const grouped = events.reduce((acc, event) => {
    const label = todayLabel(event.created_at)
    if (!acc[label]) acc[label] = []
    acc[label].push(event)
    return acc
  }, {})

  const dayKeys = Object.keys(grouped)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-xl mx-4 flex flex-col max-h-[80vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">Historia aktywności</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M4 4l12 12M16 4L4 16" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading && events.length === 0 ? (
            <div className="flex justify-center py-12">
              <div className="w-6 h-6 border-2 border-[#e3704a] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : events.length === 0 ? (
            <p className="text-center text-sm text-gray-400 py-12">Brak aktywności.</p>
          ) : (
            <div className="space-y-6">
              {dayKeys.map(dayLabel => (
                <div key={dayLabel}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="h-px flex-1 bg-gray-100" />
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide shrink-0">
                      {dayLabel}
                    </span>
                    <div className="h-px flex-1 bg-gray-100" />
                  </div>

                  <ul className="space-y-1">
                    {grouped[dayLabel].map(event => (
                      <li key={event.id} className="flex items-start gap-3 py-2 px-2 rounded-lg hover:bg-gray-50">
                        <span className="shrink-0 w-7 h-7 rounded-full bg-[#e3704a]/10 text-[#e3704a] text-xs font-semibold flex items-center justify-center mt-0.5">
                          {authorInitial(event.user_email)}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-800">
                            <span className="font-medium">{event.user_email?.split('@')[0] || '?'}</span>
                            {' '}{actionLabel(event)}
                          </p>
                          <p className="text-xs text-gray-400 mt-0.5">{formatTime(event.created_at)}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}

              {hasMore && (
                <div className="flex justify-center pt-2 pb-4">
                  <button
                    onClick={() => loadMore(offset, true)}
                    disabled={loading}
                    className="text-sm text-[#e3704a] hover:underline disabled:opacity-50"
                  >
                    {loading ? 'Ładowanie…' : 'Załaduj więcej'}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
