import { useState, useEffect, useCallback } from 'react'
import { authedFetch } from '../../lib/authedFetch'
import { useShares } from './useShares'
import ActivityLogModal from './ActivityLogModal'
import { actionLabel, authorInitial } from './activityLabels'

function relativeTime(isoString) {
  if (!isoString) return ''
  const diff = Date.now() - new Date(isoString).getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return 'przed chwilą'
  if (minutes < 60) return `${minutes} min temu`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} godz. temu`
  const days = Math.floor(hours / 24)
  return `${days} dni temu`
}

// ─── Share row ────────────────────────────────────────────────────────────────
function ShareRow({ share, onRemove, removing }) {
  return (
    <div className="flex items-center gap-2 py-2 px-2 rounded-lg hover:bg-gray-50 group">
      <span className="shrink-0 w-7 h-7 rounded-full bg-[#e3704a]/15 text-[#e3704a] text-xs font-semibold flex items-center justify-center">
        {authorInitial(share.shared_with_email)}
      </span>
      <span className="flex-1 min-w-0 text-sm text-gray-700 truncate">
        {share.shared_with_email}
      </span>
      <button
        onClick={() => onRemove(share.id)}
        disabled={removing}
        title="Cofnij dostęp"
        aria-label={`Cofnij dostęp dla ${share.shared_with_email}`}
        className="opacity-50 group-hover:opacity-100 focus:opacity-100 text-gray-400 hover:text-red-500 transition-all disabled:opacity-30"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M2 2l10 10M12 2L2 12" />
        </svg>
      </button>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function CollaborationSection({ projectId, isOwner }) {
  const { shares, loading: sharesLoading, error: sharesError, fetchShares, addShare, removeShare } = useShares(projectId)
  const [emailInput, setEmailInput] = useState('')
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState(null)
  const [removingId, setRemovingId] = useState(null)

  const [events, setEvents] = useState([])
  const [eventsLoading, setEventsLoading] = useState(false)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    if (isOwner) fetchShares()
  }, [isOwner, fetchShares])

  const fetchRecentActivity = useCallback(async () => {
    if (!projectId) return
    setEventsLoading(true)
    try {
      const data = await authedFetch(`/projects/${projectId}/activity?limit=20`)
      setEvents(data.events || [])
    } catch {
      // non-critical, swallow
    } finally {
      setEventsLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    fetchRecentActivity()
  }, [fetchRecentActivity])

  const handleAdd = async (e) => {
    e.preventDefault()
    const email = emailInput.trim()
    if (!email) return
    setAdding(true)
    setAddError(null)
    try {
      await addShare(email)
      setEmailInput('')
    } catch (err) {
      setAddError(err.message)
    } finally {
      setAdding(false)
    }
  }

  const handleRemove = async (shareId) => {
    setRemovingId(shareId)
    try {
      await removeShare(shareId)
    } catch (err) {
      console.error('Failed to remove share:', err)
    } finally {
      setRemovingId(null)
    }
  }

  return (
    <div className="space-y-4">

      {/* ── Share management (owner only) ── */}
      {isOwner && (
        <div>
          <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Osoby z dostępem</p>

          {sharesLoading ? (
            <div className="flex justify-center py-3">
              <div className="w-4 h-4 border-2 border-[#e3704a] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : sharesError ? (
            <p className="text-xs text-red-500">{sharesError}</p>
          ) : shares.length === 0 ? (
            <p className="text-xs text-gray-400 py-1">Tylko ty masz dostęp do tego projektu.</p>
          ) : (
            <div className="-mx-2">
              {shares.map(share => (
                <ShareRow
                  key={share.id}
                  share={share}
                  onRemove={handleRemove}
                  removing={removingId === share.id}
                />
              ))}
            </div>
          )}

          {/* Add collaborator form */}
          <form onSubmit={handleAdd} className="mt-3 flex gap-2">
            <input
              type="email"
              value={emailInput}
              onChange={(e) => { setEmailInput(e.target.value); setAddError(null) }}
              placeholder="adres@email.com"
              disabled={adding}
              className="flex-1 text-sm border border-gray-200 rounded-lg px-3 py-2 outline-none focus:border-[#e3704a] focus:ring-1 focus:ring-[#e3704a]/30 disabled:opacity-50 transition-colors"
            />
            <button
              type="submit"
              disabled={adding || !emailInput.trim()}
              className="shrink-0 px-3 py-2 text-sm bg-[#e3704a] text-white rounded-lg hover:bg-[#c95e3a] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {adding ? '…' : 'Dodaj'}
            </button>
          </form>
          {addError && (
            <p className="text-xs text-red-500 mt-1.5">{addError}</p>
          )}
        </div>
      )}

      {/* ── Activity log ── */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Aktywność</p>
          {events.length > 0 && (
            <button
              onClick={() => setShowModal(true)}
              className="text-xs text-[#e3704a] hover:underline"
            >
              Zobacz wszystko
            </button>
          )}
        </div>

        {eventsLoading ? (
          <div className="flex justify-center py-3">
            <div className="w-4 h-4 border-2 border-gray-300 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : events.length === 0 ? (
          <p className="text-xs text-gray-400 py-1">Brak aktywności.</p>
        ) : (
          <ul className="space-y-0.5">
            {events.slice(0, 8).map(event => (
              <li key={event.id} className="flex items-start gap-2 py-1.5 px-2 rounded-lg hover:bg-gray-50">
                <span className="shrink-0 w-6 h-6 rounded-full bg-gray-100 text-gray-500 text-[10px] font-semibold flex items-center justify-center mt-0.5">
                  {authorInitial(event.user_email)}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-700 leading-snug">
                    <span className="font-medium">{event.user_email?.split('@')[0] || '?'}</span>
                    {' '}{actionLabel(event)}
                  </p>
                  <p className="text-[10px] text-gray-400 mt-0.5">{relativeTime(event.created_at)}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {showModal && (
        <ActivityLogModal
          projectId={projectId}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  )
}
