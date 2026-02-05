import { useState } from 'react'
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
import Button from '../../components/ui/Button'

// Sortable Chapter Item Component
function SortableChapterItem({
  chapter,
  index,
  selectedId,
  onSelect,
  confirmDelete,
  setConfirmDelete,
  onDelete,
  deleting,
  getWordCount,
}) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id: chapter.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const handleDelete = async () => {
    try {
      await onDelete(chapter.id)
      if (selectedId === chapter.id) {
        onSelect(null)
      }
    } catch (err) {
      console.error('Failed to delete chapter:', err)
    } finally {
      setConfirmDelete(null)
    }
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`group rounded-lg cursor-pointer transition-colors ${
        selectedId === chapter.id ? 'bg-gray-100' : 'hover:bg-gray-50'
      }`}
      onClick={() => onSelect(chapter.id)}
    >
      <div className="flex items-start gap-2 py-3 px-3">
        {/* Drag Handle */}
        <button
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 mt-0.5"
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
                handleDelete()
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
  )
}

export default function ChapterList({
  chapters,
  loading,
  selectedId,
  onSelect,
  onDelete,
  onReorder,
}) {
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [deleting, setDeleting] = useState(false)

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

      // Call parent callback to save new order
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
              onSelect={onSelect}
              confirmDelete={confirmDelete}
              setConfirmDelete={setConfirmDelete}
              onDelete={onDelete}
              deleting={deleting}
              getWordCount={getWordCount}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  )
}
