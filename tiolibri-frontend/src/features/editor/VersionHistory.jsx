import { useEffect, useState, useCallback } from 'react'
import { useVersions } from './useVersions'
import DiffViewer from './DiffViewer'

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

function authorInitial(email) {
  if (!email) return '?'
  return email.charAt(0).toUpperCase()
}

export default function VersionHistory({ chapterId, currentContent, onContentRestored }) {
  const { versions, loading, error, fetchVersions, getVersionContent, restoreVersion } = useVersions(chapterId)
  const [diffVersion, setDiffVersion] = useState(null) // full version object with content
  const [restoring, setRestoring] = useState(false)

  useEffect(() => {
    fetchVersions()
  }, [fetchVersions])

  const handleOpenDiff = useCallback(async (version) => {
    try {
      const full = await getVersionContent(version.id)
      setDiffVersion(full)
    } catch (err) {
      console.error('Failed to load version content:', err)
    }
  }, [getVersionContent])

  const handleRestore = useCallback(async () => {
    if (!diffVersion) return
    setRestoring(true)
    try {
      const result = await restoreVersion(diffVersion.id)
      setDiffVersion(null)
      onContentRestored?.(result.chapter)
    } catch (err) {
      console.error('Failed to restore version:', err)
    } finally {
      setRestoring(false)
    }
  }, [diffVersion, restoreVersion, onContentRestored])

  if (!chapterId) {
    return (
      <p className="text-xs text-gray-400 py-2">Wybierz rozdział, żeby zobaczyć historię wersji.</p>
    )
  }

  if (loading) {
    return (
      <div className="flex justify-center py-4">
        <div className="w-5 h-5 border-2 border-[#e3704a] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error) {
    return <p className="text-xs text-red-500 py-2">{error}</p>
  }

  if (versions.length === 0) {
    return (
      <p className="text-xs text-gray-400 py-2">
        Brak zapisanych wersji. Wersje tworzone są automatycznie podczas zapisywania rozdziału.
      </p>
    )
  }

  return (
    <>
      <ul className="space-y-1 mt-1">
        {versions.map((version) => (
          <li key={version.id}>
            <button
              onClick={() => handleOpenDiff(version)}
              className="w-full text-left flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-gray-100 transition-colors group"
            >
              {/* Author avatar */}
              <span className="shrink-0 w-6 h-6 rounded-full bg-[#e3704a]/15 text-[#e3704a] text-[10px] font-semibold flex items-center justify-center">
                {authorInitial(version.author_email)}
              </span>

              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-gray-700 truncate">
                  {version.title_snapshot || 'Rozdział'}
                </div>
                <div className="text-[10px] text-gray-400 truncate">
                  {relativeTime(version.created_at)}
                  {version.author_email && ` · ${version.author_email}`}
                </div>
              </div>

              <svg
                className="shrink-0 w-3.5 h-3.5 text-gray-300 group-hover:text-gray-500 transition-colors"
                fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 14 14"
              >
                <path d="M5 2l4 5-4 5" />
              </svg>
            </button>
          </li>
        ))}
      </ul>

      {diffVersion && (
        <DiffViewer
          version={diffVersion}
          currentContent={currentContent}
          onRestore={handleRestore}
          onClose={() => setDiffVersion(null)}
          restoring={restoring}
        />
      )}
    </>
  )
}
