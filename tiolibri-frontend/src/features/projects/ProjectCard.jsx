import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import { timeAgo } from '../../lib/utils'
import { authedFetch } from '../../lib/authedFetch'

// 3-dot kebab menu
function KebabMenu({ onDuplicate, onDelete, onExport, duplicating, exporting }) {
  // onDelete === null means this is a shared (non-owned) project — hide the delete option.
  const [open, setOpen] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleteInput, setDeleteInput] = useState('')
  const menuRef = useRef(null)
  const inputRef = useRef(null)

  // Close menu on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false)
        setShowDeleteConfirm(false)
        setDeleteInput('')
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // Focus input when delete confirm shows
  useEffect(() => {
    if (showDeleteConfirm && inputRef.current) {
      inputRef.current.focus()
    }
  }, [showDeleteConfirm])

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true)
  }

  const handleDeleteConfirm = () => {
    if (deleteInput.toLowerCase() === 'usuń') {
      setOpen(false)
      setShowDeleteConfirm(false)
      setDeleteInput('')
      onDelete()
    }
  }

  const handleDuplicateClick = () => {
    setOpen(false)
    onDuplicate()
  }

  const handleExportClick = () => {
    setOpen(false)
    onExport()
  }

  return (
    <div ref={menuRef} className="relative">
      <button
        onClick={(e) => {
          e.stopPropagation()
          setOpen((prev) => !prev)
          setShowDeleteConfirm(false)
          setDeleteInput('')
        }}
        className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
        title="Więcej opcji"
      >
        {/* Vertical 3-dot icon */}
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <circle cx="8" cy="3" r="1.5" />
          <circle cx="8" cy="8" r="1.5" />
          <circle cx="8" cy="13" r="1.5" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 bottom-full mb-1 z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[180px]">
          {!showDeleteConfirm ? (
            <>
              <button
                onClick={handleDuplicateClick}
                disabled={duplicating}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2 disabled:opacity-50"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <rect x="4" y="4" width="8" height="8" rx="1" />
                  <path d="M2 10V2h8" />
                </svg>
                {duplicating ? 'Duplikuję...' : 'Duplikuj projekt'}
              </button>
              <button
                onClick={handleExportClick}
                disabled={exporting}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2 disabled:opacity-50"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M7 2v7M4 6l3 3 3-3" />
                  <path d="M2 10v1a1 1 0 001 1h8a1 1 0 001-1v-1" />
                </svg>
                {exporting ? 'Eksportuję...' : 'Eksportuj backup (.tiolibri)'}
              </button>
              {onDelete && (
                <>
                  <div className="border-t border-gray-100 my-1" />
                  <button
                    onClick={handleDeleteClick}
                    className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                  >
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M2 4h10M5 4V2.5a.5.5 0 01.5-.5h3a.5.5 0 01.5.5V4M5.5 7v4M8.5 7v4" />
                      <rect x="2.5" y="4" width="9" height="8" rx="1" />
                    </svg>
                    Usuń projekt
                  </button>
                </>
              )}
            </>
          ) : (
            <div className="px-3 py-2">
              <p className="text-xs text-gray-500 mb-2">
                Wpisz <span className="font-mono font-semibold text-red-600">usuń</span> żeby potwierdzić:
              </p>
              <input
                ref={inputRef}
                value={deleteInput}
                onChange={(e) => setDeleteInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleDeleteConfirm()
                  if (e.key === 'Escape') {
                    setShowDeleteConfirm(false)
                    setDeleteInput('')
                  }
                }}
                className="w-full text-sm border border-gray-300 rounded px-2 py-1 mb-2 outline-none focus:border-red-400"
                placeholder="usuń"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleDeleteConfirm}
                  disabled={deleteInput.toLowerCase() !== 'usuń'}
                  className="flex-1 text-xs bg-red-600 text-white rounded py-1.5 font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-red-700 transition-colors"
                >
                  Usuń
                </button>
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false)
                    setDeleteInput('')
                  }}
                  className="flex-1 text-xs bg-gray-100 text-gray-700 rounded py-1.5 font-medium hover:bg-gray-200 transition-colors"
                >
                  Anuluj
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ProjectCard({ project, onDelete, onDuplicate, sharedByEmail }) {
  const [deleting, setDeleting] = useState(false)
  const [duplicating, setDuplicating] = useState(false)
  const [exporting, setExporting] = useState(false)

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await onDelete(project.id)
    } catch (err) {
      console.error('Failed to delete project:', err)
      setDeleting(false)
    }
  }

  const handleDuplicate = async () => {
    setDuplicating(true)
    try {
      await onDuplicate(project.id)
    } catch (err) {
      console.error('Failed to duplicate project:', err)
    } finally {
      setDuplicating(false)
    }
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      const blob = await authedFetch(`/projects/${project.id}/export`, {
        method: 'POST',
        responseType: 'blob',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      const safeName = (project.title || 'project').replace(/[^a-zA-Z0-9 \-_]/g, '_')
      a.href = url
      a.download = `${safeName}.tiolibri`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to export project:', err)
    } finally {
      setExporting(false)
    }
  }

  return (
    <Card className="flex flex-col">
      <div className="flex-1">
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-semibold text-gray-900 truncate pr-2">
            {project.title}
          </h3>
          <Badge variant={project.status}>{project.status}</Badge>
        </div>

        {project.author && (
          <p className="text-sm text-gray-600 mb-2">by {project.author}</p>
        )}

        {sharedByEmail !== undefined ? (
          <p className="text-xs text-[#e3704a] font-medium mt-1">
            {sharedByEmail ? `Udostępnione przez ${sharedByEmail}` : 'Udostępnione dla ciebie'}
          </p>
        ) : (
          <p className="text-xs text-gray-400">
            Updated {timeAgo(project.updated_at)}
          </p>
        )}
      </div>

      <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
        <Link to={`/editor/${project.id}`} className="flex-1">
          <Button variant="primary" className="w-full" disabled={deleting}>
            {deleting ? 'Usuwanie...' : 'Otwórz'}
          </Button>
        </Link>

        <KebabMenu
          onDuplicate={handleDuplicate}
          onDelete={onDelete ? handleDelete : null}
          onExport={handleExport}
          duplicating={duplicating}
          exporting={exporting}
        />
      </div>
    </Card>
  )
}
