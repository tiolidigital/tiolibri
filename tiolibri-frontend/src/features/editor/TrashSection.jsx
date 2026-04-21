import { useState, useEffect, useCallback } from 'react'

function TrashIcon({ className = '' }) {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" className={className}>
      <path d="M2 4h10M5 4V2.5a.5.5 0 01.5-.5h3a.5.5 0 01.5.5V4M5.5 7v4M8.5 7v4" />
      <rect x="2.5" y="4" width="9" height="8" rx="1" />
    </svg>
  )
}

function formatDeletedAt(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'dzisiaj'
  if (diffDays === 1) return 'wczoraj'
  return `${diffDays} dni temu`
}

export default function TrashSection({ fetchTrash, onRestore, onPermanentDelete }) {
  const [isOpen, setIsOpen] = useState(false)
  const [trashedChapters, setTrashedChapters] = useState([])
  const [loading, setLoading] = useState(false)
  const [confirmDeleteId, setConfirmDeleteId] = useState(null)
  const [working, setWorking] = useState(false)

  const load = useCallback(async () => {
    if (!fetchTrash) return
    setLoading(true)
    try {
      const chapters = await fetchTrash()
      setTrashedChapters(chapters)
    } catch (err) {
      console.error('Failed to load trash:', err)
    } finally {
      setLoading(false)
    }
  }, [fetchTrash])

  // Load trash when section opens
  useEffect(() => {
    if (isOpen) {
      load()
    }
  }, [isOpen, load])

  const handleRestore = async (id) => {
    setWorking(true)
    try {
      await onRestore(id)
      setTrashedChapters(prev => prev.filter(ch => ch.id !== id))
    } catch (err) {
      console.error('Failed to restore:', err)
    } finally {
      setWorking(false)
    }
  }

  const handlePermanentDelete = async (id) => {
    setWorking(true)
    try {
      await onPermanentDelete(id)
      setTrashedChapters(prev => prev.filter(ch => ch.id !== id))
    } catch (err) {
      console.error('Failed to permanently delete:', err)
    } finally {
      setWorking(false)
      setConfirmDeleteId(null)
    }
  }

  const count = trashedChapters.length

  return (
    <div className="border-t border-gray-100 mt-2">
      {/* Header / toggle */}
      <button
        onClick={() => setIsOpen(prev => !prev)}
        className="w-full flex items-center justify-between px-3 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider hover:text-gray-600 transition-colors"
      >
        <span className="flex items-center gap-1.5">
          <TrashIcon />
          Kosz
          {count > 0 && (
            <span className="ml-1 bg-gray-200 text-gray-600 text-[10px] font-semibold rounded-full px-1.5 py-0.5">
              {count}
            </span>
          )}
        </span>
        <svg
          width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5"
          className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        >
          <path d="M2 4l4 4 4-4" />
        </svg>
      </button>

      {isOpen && (
        <div className="px-3 pb-3">
          {loading ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-300 mx-auto" />
            </div>
          ) : trashedChapters.length === 0 ? (
            <p className="text-xs text-gray-400 text-center py-3">Kosz jest pusty</p>
          ) : (
            <div className="space-y-1">
              {trashedChapters.map(chapter => (
                <div
                  key={chapter.id}
                  className="rounded-lg bg-gray-50 border border-gray-100 px-3 py-2.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-700 truncate">
                        {chapter.title || 'Untitled Chapter'}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        Usunięto {formatDeletedAt(chapter.deleted_at)}
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-2 mt-2">
                    {/* Restore */}
                    <button
                      onClick={() => handleRestore(chapter.id)}
                      disabled={working}
                      className="flex-1 text-xs text-center py-1.5 rounded border border-gray-200 text-gray-600 hover:border-[#e3704a] hover:text-[#e3704a] transition-colors disabled:opacity-50"
                    >
                      Przywróć
                    </button>

                    {/* Permanent delete — with confirm step */}
                    {confirmDeleteId === chapter.id ? (
                      <div className="flex gap-1">
                        <button
                          onClick={() => handlePermanentDelete(chapter.id)}
                          disabled={working}
                          className="text-xs px-2 py-1.5 rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
                        >
                          {working ? '…' : 'Usuń'}
                        </button>
                        <button
                          onClick={() => setConfirmDeleteId(null)}
                          disabled={working}
                          className="text-xs px-2 py-1.5 rounded border border-gray-200 text-gray-600 hover:bg-gray-100 disabled:opacity-50"
                        >
                          Anuluj
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmDeleteId(chapter.id)}
                        disabled={working}
                        className="text-xs px-2 py-1.5 rounded border border-red-200 text-red-500 hover:bg-red-50 transition-colors disabled:opacity-50"
                      >
                        Usuń na zawsze
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
