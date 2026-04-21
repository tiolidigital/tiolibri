import { useEffect, useMemo } from 'react'
import { diff_match_patch } from 'diff-match-patch'

const dmp = new diff_match_patch()

function stripHtml(html) {
  if (!html) return ''
  return html.replace(/<[^>]*>/g, '')
}

function buildDiffHtml(oldText, newText) {
  const diffs = dmp.diff_main(oldText, newText)
  dmp.diff_cleanupSemantic(diffs)
  return diffs.map(([op, text]) => {
    const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br/>')
    if (op === 1) return `<ins class="bg-green-100 text-green-800">${escaped}</ins>`
    if (op === -1) return `<del class="bg-red-100 text-red-800 line-through">${escaped}</del>`
    return `<span>${escaped}</span>`
  }).join('')
}

export default function DiffViewer({ version, currentContent, onRestore, onClose, restoring }) {
  useEffect(() => {
    const handleKey = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onClose])

  const currentText = useMemo(() => stripHtml(currentContent), [currentContent])
  const versionText = useMemo(() => stripHtml(version?.content), [version])

  const diffHtml = useMemo(() => {
    if (!version?.content) return ''
    return buildDiffHtml(currentText, versionText)
  }, [currentText, versionText])

  const formattedDate = version?.created_at
    ? new Date(version.created_at).toLocaleString('pl-PL', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    : ''

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 className="text-base font-semibold text-gray-900">
              Wersja z {formattedDate}
            </h2>
            {version?.author_email && (
              <p className="text-xs text-gray-500 mt-0.5">
                Zapisana przez {version.author_email}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1 rounded"
            aria-label="Zamknij"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M15 5L5 15M5 5l10 10" />
            </svg>
          </button>
        </div>

        {/* Split pane */}
        <div className="flex flex-1 overflow-hidden divide-x divide-gray-200 min-h-0">
          {/* Current version */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider bg-gray-50 border-b border-gray-100 shrink-0">
              Aktualna wersja
            </div>
            <div className="flex-1 overflow-y-auto p-4 prose prose-sm max-w-none text-gray-700 text-sm leading-relaxed">
              <div dangerouslySetInnerHTML={{ __html: currentContent || '<em class="text-gray-400">Brak treści</em>' }} />
            </div>
          </div>

          {/* Historical version + diff */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider bg-gray-50 border-b border-gray-100 shrink-0">
              Ta wersja
            </div>
            <div className="flex-1 overflow-y-auto p-4 text-sm leading-relaxed text-gray-700">
              <div dangerouslySetInnerHTML={{ __html: diffHtml || '<em class="text-gray-400">Brak treści</em>' }} />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Anuluj
          </button>
          <button
            onClick={onRestore}
            disabled={restoring}
            className="px-4 py-2 text-sm font-medium text-white bg-[#e3704a] hover:bg-[#c95e3a] disabled:opacity-50 rounded-lg transition-colors"
          >
            {restoring ? 'Przywracanie…' : 'Przywróć tę wersję'}
          </button>
        </div>
      </div>
    </div>
  )
}
