import { useEffect, useState, useCallback } from 'react'
import { useSnapshots } from './useSnapshots'

const TRIGGERED_BY_LABEL = {
  auto: 'Auto',
  manual: 'Ręczny',
  'pre-restore': 'Przed przywróceniem',
}

function formatDate(isoString) {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleString('pl-PL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function ConfirmDialog({ snapshotDate, onConfirm, onCancel, restoring, error }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm mx-4 p-6">
        <h3 className="text-base font-semibold text-gray-900 mb-2">Przywrócić ten snapshot?</h3>
        <p className="text-sm text-gray-600 mb-1">
          Snapshot z <span className="font-medium">{snapshotDate}</span> zostanie zastosowany.
        </p>
        <p className="text-sm text-gray-500 mb-5">
          Bieżący stan projektu zostanie zapisany jako snapshot <em>przed przywróceniem</em> — możesz go cofnąć.
        </p>
        {error && (
          <p className="text-xs text-red-500 mb-3">{error}</p>
        )}
        <div className="flex gap-3">
          <button
            onClick={onConfirm}
            disabled={restoring}
            className="flex-1 py-2 text-sm font-medium bg-[#e3704a] text-white rounded-lg hover:bg-[#c95e3a] disabled:opacity-50 transition-colors"
          >
            {restoring ? 'Przywracam…' : 'Przywróć'}
          </button>
          <button
            onClick={onCancel}
            disabled={restoring}
            className="flex-1 py-2 text-sm font-medium bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
          >
            Anuluj
          </button>
        </div>
      </div>
    </div>
  )
}

export default function ProjectSnapshots({ projectId, onRestored }) {
  const { snapshots, loading, error, fetchSnapshots, createSnapshot, restoreSnapshot } = useSnapshots(projectId)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState(null)
  const [confirmSnapshot, setConfirmSnapshot] = useState(null)
  const [restoring, setRestoring] = useState(false)
  const [restoreError, setRestoreError] = useState(null)

  useEffect(() => {
    fetchSnapshots()
  }, [fetchSnapshots])

  const handleCreate = useCallback(async () => {
    setCreating(true)
    setCreateError(null)
    try {
      await createSnapshot()
    } catch (err) {
      setCreateError(err.message)
    } finally {
      setCreating(false)
    }
  }, [createSnapshot])

  const handleRestore = useCallback(async () => {
    if (!confirmSnapshot) return
    setRestoring(true)
    setRestoreError(null)
    try {
      await restoreSnapshot(confirmSnapshot.id)
      setConfirmSnapshot(null)
      onRestored?.()
    } catch (err) {
      setRestoreError(err.message)
    } finally {
      setRestoring(false)
    }
  }, [confirmSnapshot, restoreSnapshot, onRestored])

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <button
          onClick={handleCreate}
          disabled={creating}
          className="text-xs px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors font-medium"
        >
          {creating ? 'Zapisuję…' : '+ Zapisz snapshot teraz'}
        </button>
      </div>

      {createError && (
        <p className="text-xs text-red-500">{createError}</p>
      )}

      {loading ? (
        <div className="flex justify-center py-4">
          <div className="w-5 h-5 border-2 border-[#e3704a] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : error ? (
        <p className="text-xs text-red-500">{error}</p>
      ) : snapshots.length === 0 ? (
        <p className="text-xs text-gray-400 py-1">
          Brak snapshotów. Snapshoty tworzone są automatycznie co 6h lub ręcznie powyżej.
        </p>
      ) : (
        <ul className="space-y-1">
          {snapshots.map(snap => (
            <li key={snap.id}>
              <div className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-gray-50 group">
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-gray-700">
                    {formatDate(snap.created_at)}
                  </div>
                  <div className="text-[10px] text-gray-400 mt-0.5">
                    {TRIGGERED_BY_LABEL[snap.triggered_by] || snap.triggered_by}
                  </div>
                </div>
                <button
                  onClick={() => setConfirmSnapshot(snap)}
                  className="opacity-0 group-hover:opacity-100 focus:opacity-100 shrink-0 text-xs text-[#e3704a] hover:underline transition-opacity"
                >
                  Przywróć
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {confirmSnapshot && (
        <ConfirmDialog
          snapshotDate={formatDate(confirmSnapshot.created_at)}
          onConfirm={handleRestore}
          onCancel={() => { setConfirmSnapshot(null); setRestoreError(null) }}
          restoring={restoring}
          error={restoreError}
        />
      )}
    </div>
  )
}
