import { useState } from 'react'
import Button from '../../components/ui/Button'

export default function ChapterList({
  chapters,
  loading,
  selectedId,
  onSelect,
  onDelete,
}) {
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async (id) => {
    setDeleting(true)
    try {
      await onDelete(id)
      if (selectedId === id) {
        onSelect(null)
      }
    } catch (err) {
      console.error('Failed to delete chapter:', err)
    } finally {
      setDeleting(false)
      setConfirmDelete(null)
    }
  }

  // Calculate word count (approximate)
  const getWordCount = (chapter) => {
    if (!chapter.processed_html) return 0
    const text = chapter.processed_html.replace(/<[^>]*>/g, ' ')
    const words = text.trim().split(/\s+/).length
    return (words / 1000).toFixed(1)
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#e3704a] mx-auto"></div>
      </div>
    )
  }

  if (chapters.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400 text-sm">
        No chapters yet
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {chapters.map((chapter, index) => (
        <div
          key={chapter.id}
          className={`group rounded-lg cursor-pointer transition-colors ${
            selectedId === chapter.id
              ? 'bg-gray-100'
              : 'hover:bg-gray-50'
          }`}
          onClick={() => onSelect(chapter.id)}
        >
          <div className="flex items-start gap-2 py-3 px-3">
            <span
              className={`font-semibold text-sm mt-0.5 min-w-[1.5rem] ${
                selectedId === chapter.id ? 'text-[#e3704a]' : 'text-gray-400'
              }`}
            >
              {String(index + 1).padStart(2, '0')}
            </span>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm text-gray-900 truncate mb-1">
                {chapter.title || 'Untitled Chapter'}
              </div>
              <div className="text-xs text-gray-500">
                {getWordCount(chapter)}k words
                {selectedId === chapter.id && ' • Active'}
              </div>
            </div>

            {confirmDelete === chapter.id ? (
              <div className="flex gap-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(chapter.id)
                  }}
                  disabled={deleting}
                  className="text-xs text-red-600 hover:text-red-700 px-2 py-1 rounded bg-red-50"
                >
                  {deleting ? '...' : 'Yes'}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setConfirmDelete(null)
                  }}
                  disabled={deleting}
                  className="text-xs text-gray-600 hover:text-gray-700 px-2 py-1 rounded bg-gray-100"
                >
                  No
                </button>
              </div>
            ) : (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setConfirmDelete(chapter.id)
                }}
                className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 transition-opacity mt-1"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
