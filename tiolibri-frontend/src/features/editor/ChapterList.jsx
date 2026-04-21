import { useState, useRef, useEffect } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

// Status dot: gray=draft, yellow=review, green=done
const STATUS_DOT = {
  draft: 'bg-gray-300',
  review: 'bg-yellow-400',
  done: 'bg-green-500',
}

const STATUS_LABELS = {
  draft: 'Szkic',
  review: 'Do recenzji',
  done: 'Gotowy',
}

// Context menu component
function ContextMenu({ x, y, chapter, isOwner, onRename, onMoveToTrash, onSetStatus, onToggleLock, onClose }) {
  const menuRef = useRef(null)

  useEffect(() => {
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [onClose])

  const isLocked = !!chapter.locked_by
  const currentStatus = chapter.status || 'draft'

  return (
    <div
      ref={menuRef}
      style={{ top: y, left: x }}
      className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[180px]"
    >
      {/* Rename */}
      <button
        onClick={() => { onRename(); onClose() }}
        className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M9.5 2.5l2 2-7 7H2.5v-2l7-7z" />
        </svg>
        Zmień nazwę
      </button>

      {/* Status sub-section */}
      <div className="border-t border-gray-100 my-1" />
      <div className="px-3 py-1 text-xs font-medium text-gray-400 uppercase tracking-wide">Status</div>
      {(['draft', 'review', 'done']).map((s) => (
        <button
          key={s}
          onClick={() => { onSetStatus(s); onClose() }}
          className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 ${
            currentStatus === s ? 'text-[#e3704a] bg-[#FFF7F5]' : 'text-gray-700 hover:bg-gray-50'
          }`}
        >
          <span className={`w-2 h-2 rounded-full inline-block ${STATUS_DOT[s]}`} />
          {STATUS_LABELS[s]}
          {currentStatus === s && (
            <svg className="ml-auto w-3 h-3" fill="currentColor" viewBox="0 0 12 12">
              <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
            </svg>
          )}
        </button>
      ))}

      {/* Lock — only shown for owner */}
      {isOwner && (
        <>
          <div className="border-t border-gray-100 my-1" />
          <button
            onClick={() => { onToggleLock(); onClose() }}
            className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
          >
            {isLocked ? (
              <>
                <LockOpenIcon />
                Odblokuj rozdział
              </>
            ) : (
              <>
                <LockIcon />
                Zablokuj rozdział
              </>
            )}
          </button>
        </>
      )}

      {/* Move to Trash */}
      <div className="border-t border-gray-100 my-1" />
      <button
        onClick={() => { onMoveToTrash(); onClose() }}
        className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
      >
        <TrashIcon />
        Przenieś do kosza
      </button>
    </div>
  )
}

// Small icon components to keep JSX clean
function LockIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="2.5" y="6" width="9" height="6.5" rx="1" />
      <path d="M4.5 6V4a2.5 2.5 0 015 0v2" />
    </svg>
  )
}

function LockOpenIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="2.5" y="6" width="9" height="6.5" rx="1" />
      <path d="M4.5 6V4a2.5 2.5 0 015 0" />
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M2 4h10M5 4V2.5a.5.5 0 01.5-.5h3a.5.5 0 01.5.5V4M5.5 7v4M8.5 7v4" />
      <rect x="2.5" y="4" width="9" height="8" rx="1" />
    </svg>
  )
}

// Sortable Chapter Item Component
function SortableChapterItem({
  chapter,
  index,
  selectedId,
  isOwner,
  currentUserId,
  onSelect,
  onDelete,
  onSetStatus,
  onToggleLock,
  getWordCount,
  editingId,
  editingTitle,
  setEditingTitle,
  onRenameSubmit,
  onContextMenu,
}) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id: chapter.id })

  const inputRef = useRef(null)
  const isEditing = editingId === chapter.id
  const isLocked = !!chapter.locked_by
  const lockedByOther = isLocked && chapter.locked_by !== currentUserId
  const status = chapter.status || 'draft'

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  // Focus input when editing starts
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  const handleRenameKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      onRenameSubmit(chapter.id, editingTitle)
    } else if (e.key === 'Escape') {
      onRenameSubmit(null, null) // cancel
    }
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`group rounded-lg cursor-pointer transition-colors ${
        selectedId === chapter.id ? 'bg-gray-100' : 'hover:bg-gray-50'
      }`}
      onClick={() => !isEditing && onSelect(chapter.id)}
      onContextMenu={(e) => {
        e.preventDefault()
        onContextMenu(e, chapter.id)
      }}
    >
      <div className="flex items-start gap-2 py-3 px-3">
        {/* Drag Handle */}
        <button
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 mt-0.5 shrink-0"
          onClick={(e) => e.stopPropagation()}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <circle cx="5" cy="4" r="1.5" />
            <circle cx="11" cy="4" r="1.5" />
            <circle cx="5" cy="8" r="1.5" />
            <circle cx="11" cy="8" r="1.5" />
            <circle cx="5" cy="12" r="1.5" />
            <circle cx="11" cy="12" r="1.5" />
          </svg>
        </button>

        {/* Chapter number */}
        <span
          className={`font-semibold text-sm mt-0.5 min-w-[1.5rem] shrink-0 ${
            selectedId === chapter.id ? 'text-[#e3704a]' : 'text-gray-400'
          }`}
        >
          {String(index + 1).padStart(2, '0')}
        </span>

        <div className="flex-1 min-w-0">
          {isEditing ? (
            <input
              ref={inputRef}
              value={editingTitle}
              onChange={(e) => setEditingTitle(e.target.value)}
              onKeyDown={handleRenameKeyDown}
              onBlur={() => onRenameSubmit(chapter.id, editingTitle)}
              onClick={(e) => e.stopPropagation()}
              className="w-full text-sm font-medium text-gray-900 bg-white border border-[#e3704a] rounded px-1.5 py-0.5 outline-none ring-1 ring-[#e3704a]/30"
            />
          ) : (
            <>
              <div className="font-medium text-sm text-gray-900 truncate mb-1 flex items-center gap-1.5">
                {/* Status dot */}
                <span
                  className={`w-2 h-2 rounded-full shrink-0 ${STATUS_DOT[status]}`}
                  title={STATUS_LABELS[status]}
                />
                {chapter.title || 'Untitled Chapter'}
                {/* Lock icon */}
                {isLocked && (
                  <span
                    title={lockedByOther ? 'Zablokowany przez innego użytkownika' : 'Zablokowany przez ciebie'}
                    className={`ml-0.5 shrink-0 ${lockedByOther ? 'text-amber-500' : 'text-gray-400'}`}
                  >
                    <svg width="11" height="11" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <rect x="2.5" y="6" width="9" height="6.5" rx="1" />
                      <path d="M4.5 6V4a2.5 2.5 0 015 0v2" />
                    </svg>
                  </span>
                )}
              </div>
              <div className="text-xs text-gray-500">
                {getWordCount(chapter)}k słów
                {selectedId === chapter.id && ' • Active'}
              </div>
            </>
          )}
        </div>

        {/* Delete button (hover, non-edit mode) */}
        {!isEditing && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete(chapter.id)
            }}
            title="Przenieś do kosza"
            className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 transition-opacity mt-1 shrink-0"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  )
}

export default function ChapterList({
  chapters,
  loading,
  selectedId,
  isOwner,
  currentUserId,
  onSelect,
  onDelete,
  onReorder,
  onRename,
  onSetStatus,
  onToggleLock,
}) {
  // Rename state
  const [editingId, setEditingId] = useState(null)
  const [editingTitle, setEditingTitle] = useState('')

  // Context menu state
  const [contextMenu, setContextMenu] = useState(null) // { x, y, chapterId }

  // DnD sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  // Handle drag end
  const handleDragEnd = (event) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      const oldIndex = chapters.findIndex((c) => c.id === active.id)
      const newIndex = chapters.findIndex((c) => c.id === over.id)

      const newOrder = arrayMove(chapters, oldIndex, newIndex)

      if (onReorder) {
        onReorder(newOrder)
      }
    }
  }

  // Calculate word count (approximate)
  const getWordCount = (chapter) => {
    if (!chapter.processed_html) return 0
    const text = chapter.processed_html.replace(/<[^>]*>/g, ' ')
    const words = text.trim().split(/\s+/).length
    return (words / 1000).toFixed(1)
  }

  const handleContextMenu = (e, chapterId) => {
    setContextMenu({ x: e.clientX, y: e.clientY, chapterId })
  }

  const startRename = (chapterId) => {
    const chapter = chapters.find((c) => c.id === chapterId)
    if (chapter) {
      setEditingId(chapterId)
      setEditingTitle(chapter.title || '')
    }
  }

  const handleRenameSubmit = async (chapterId, newTitle) => {
    if (!chapterId || newTitle === null) {
      setEditingId(null)
      setEditingTitle('')
      return
    }

    const chapter = chapters.find((c) => c.id === chapterId)
    const trimmed = newTitle.trim()

    // Don't save if empty or unchanged
    if (!trimmed || trimmed === chapter?.title) {
      setEditingId(null)
      setEditingTitle('')
      return
    }

    try {
      if (onRename) {
        await onRename(chapterId, trimmed)
      }
    } catch (err) {
      console.error('Failed to rename chapter:', err)
    } finally {
      setEditingId(null)
      setEditingTitle('')
    }
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

  const contextChapter = chapters.find((c) => c.id === contextMenu?.chapterId)

  return (
    <>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={chapters.map((c) => c.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="space-y-1">
            {chapters.map((chapter, index) => (
              <SortableChapterItem
                key={chapter.id}
                chapter={chapter}
                index={index}
                selectedId={selectedId}
                isOwner={isOwner}
                currentUserId={currentUserId}
                onSelect={onSelect}
                onDelete={onDelete}
                onSetStatus={(status) => onSetStatus?.(chapter.id, status)}
                onToggleLock={() => onToggleLock?.(chapter.id)}
                getWordCount={getWordCount}
                editingId={editingId}
                editingTitle={editingTitle}
                setEditingTitle={setEditingTitle}
                onRenameSubmit={handleRenameSubmit}
                onContextMenu={handleContextMenu}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      {contextMenu && contextChapter && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          chapter={contextChapter}
          isOwner={isOwner}
          onRename={() => startRename(contextMenu.chapterId)}
          onMoveToTrash={() => onDelete?.(contextMenu.chapterId)}
          onSetStatus={(status) => onSetStatus?.(contextMenu.chapterId, status)}
          onToggleLock={() => onToggleLock?.(contextMenu.chapterId)}
          onClose={() => setContextMenu(null)}
        />
      )}
    </>
  )
}
