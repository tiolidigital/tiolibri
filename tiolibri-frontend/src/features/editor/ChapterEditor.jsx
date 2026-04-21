import { useEffect, useState, useRef } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import { Divider } from './extensions/Divider'
import { SearchAndReplace } from './extensions/SearchAndReplace'
import EditorToolbar from './EditorToolbar'
import { getPreset } from '../../lib/presets'
import './editor.css'

export default function ChapterEditor({
  chapter,
  content,
  onSave,
  onContentChange,
  onSaveStateChange,
  projectId,
  showInspector,
  onInspectorToggle,
  showPreview,
  onPreviewToggle,
  typographySettings,
  stylePreset,
  currentUserId,
  editorRef,
}) {
  // Chapter is read-only when locked by a different user
  const lockedByOther = chapter?.locked_by && chapter.locked_by !== currentUserId
  const [saving, setSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState(null)
  const [saveError, setSaveError] = useState(null)

  // Mirror save state to the parent so the header badge shows real status.
  const onSaveStateChangeRef = useRef(onSaveStateChange)
  useEffect(() => {
    onSaveStateChangeRef.current = onSaveStateChange
  }, [onSaveStateChange])
  useEffect(() => {
    onSaveStateChangeRef.current?.({ saving, lastSaved, saveError })
  }, [saving, lastSaved, saveError])

  // Apply typography settings with defaults
  const settings = typographySettings || {
    textAlign: 'left',
    fontSize: 16,
    lineHeight: 1.7,
    marginTop: 2,
    marginBottom: 2,
    marginLeft: 1.5,
    marginRight: 1.5,
  }

  // Get preset with fontFamily
  const preset = getPreset(stylePreset || 'classic')

  const editor = useEditor({
    extensions: [
      StarterKit,
      Image.configure({
        inline: true,
        allowBase64: false,
        HTMLAttributes: {
          class: 'editor-image',
        },
      }),
      Divider,
      SearchAndReplace,
    ],
    content: content || '',
    editable: !lockedByOther,
    editorProps: {
      attributes: {
        class: 'tiptap-editor prose max-w-none focus:outline-none min-h-[500px]',
      },
    },
  })

  // Expose editor instance to parent so EditorPage can drive Find & Replace.
  useEffect(() => {
    if (editorRef) editorRef.current = editor
  }, [editor, editorRef])

  // Load content when chapter changes, and again once async content arrives
  // (parent's loadContent sets `content` after mount). Ref-tracking prevents
  // re-running on every keystroke — `content` updates via onContentChange while
  // typing, and calling setContent again would reset the cursor.
  //
  // Rule: setContent once per chapter with the first non-empty content we see.
  // If the chapter genuinely has no content, we still setContent('') on mount.
  const loadedKeyRef = useRef(null)
  useEffect(() => {
    if (!editor || !chapter?.id) return
    const key = chapter.id
    const hasContent = !!content
    if (loadedKeyRef.current !== key) {
      editor.commands.setContent(content || '', false)
      loadedKeyRef.current = hasContent ? key : `${key}:empty`
      return
    }
    if (loadedKeyRef.current === `${key}:empty` && hasContent) {
      editor.commands.setContent(content, false)
      loadedKeyRef.current = key
    }
  }, [editor, chapter?.id, content])

  // Sync editable flag when lock state changes after mount.
  useEffect(() => {
    if (editor) {
      editor.setEditable(!lockedByOther)
    }
  }, [editor, lockedByOther])

  // Live update for preview. Ref indirection keeps this effect from
  // re-subscribing on every parent render.
  const onContentChangeRef = useRef(onContentChange)
  useEffect(() => {
    onContentChangeRef.current = onContentChange
  }, [onContentChange])

  useEffect(() => {
    if (!editor) return

    const handleUpdate = () => {
      const cb = onContentChangeRef.current
      if (!cb) return
      cb(editor.getHTML())
    }

    editor.on('update', handleUpdate)

    return () => {
      editor.off('update', handleUpdate)
    }
  }, [editor])

  // Auto-save with debounce — a single shared timer, reset on each keystroke.
  // onSave is held in a ref so this effect does NOT re-subscribe when the
  // parent passes a new callback reference on every render. Re-subscribing
  // would fire the cleanup below and clearTimeout the pending save, so a
  // parent that re-renders faster than the debounce (e.g. lifting liveContent
  // for a live preview) would cancel autosave forever.
  const saveTimeoutRef = useRef(null)
  const onSaveRef = useRef(onSave)
  useEffect(() => {
    onSaveRef.current = onSave
  }, [onSave])

  useEffect(() => {
    if (!editor) return

    const runSave = async () => {
      const save = onSaveRef.current
      if (!save) return
      const html = editor.getHTML()
      setSaving(true)
      setSaveError(null)
      try {
        await save(html)
        setLastSaved(new Date())
        setSaveError(null)
      } catch (err) {
        console.error('[autosave] save failed:', err)
        setSaveError(err?.message || 'Save failed')
      } finally {
        setSaving(false)
      }
    }

    const handleUpdate = () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
      saveTimeoutRef.current = setTimeout(() => {
        saveTimeoutRef.current = null
        runSave()
      }, 2000)
    }

    editor.on('update', handleUpdate)

    return () => {
      editor.off('update', handleUpdate)
      // Chapter is changing (or component is unmounting). Flush the pending
      // save instead of cancelling it — otherwise switching chapters within
      // the 2s debounce window silently discards unsaved edits.
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
        saveTimeoutRef.current = null
        runSave()
      }
    }
  }, [editor, chapter?.id])

  if (!editor) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#e3704a]"></div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* Lock banner */}
      {lockedByOther && (
        <div className="flex items-center gap-2 px-6 py-2 bg-amber-50 border-b border-amber-200 text-amber-800 text-sm">
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            className="shrink-0"
          >
            <rect x="2.5" y="6" width="9" height="6.5" rx="1" />
            <path d="M4.5 6V4a2.5 2.5 0 015 0v2" />
          </svg>
          Rozdział jest zablokowany przez innego użytkownika — tryb tylko do odczytu.
        </div>
      )}

      {/* Toolbar - Floating above paper */}
      <div className="sticky top-0 z-10 px-8 pt-6 pb-2 bg-gradient-to-b from-gray-100 to-transparent">
        <div className="max-w-4xl mx-auto bg-white border border-gray-200 rounded-lg shadow-sm">
          <div className="px-4 py-2 flex items-center justify-between gap-4">
            <EditorToolbar
              editor={editor}
              projectId={projectId}
              showInspector={showInspector}
              onInspectorToggle={onInspectorToggle}
              showPreview={showPreview}
              onPreviewToggle={onPreviewToggle}
            />
            <SaveIndicator saving={saving} lastSaved={lastSaved} />
          </div>
        </div>
      </div>

      {/* Editor content - Paper effect */}
      <div className="flex-1 overflow-y-auto px-8 pb-8">
        <div className="max-w-4xl mx-auto bg-white shadow-lg rounded-lg border border-gray-200 min-h-full">
          <div
            className="p-12 transition-all duration-200"
            style={{
              '--editor-font-size': `${settings.fontSize}px`,
              '--editor-line-height': settings.lineHeight,
              '--editor-text-align': settings.textAlign,
              '--editor-font-family': preset.fontFamily,
              marginTop: `${settings.marginTop}em`,
              marginBottom: `${settings.marginBottom}em`,
              marginLeft: `${settings.marginLeft}em`,
              marginRight: `${settings.marginRight}em`,
            }}
          >
            <EditorContent editor={editor} />
          </div>
        </div>
      </div>
    </div>
  )
}

function SaveIndicator({ saving, lastSaved }) {
  if (saving) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-gray-500 whitespace-nowrap">
        <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
        <span>Zapisywanie…</span>
      </div>
    )
  }
  if (lastSaved) {
    return (
      <div
        className="text-xs text-gray-400 whitespace-nowrap"
        title={lastSaved.toLocaleString('pl-PL')}
      >
        Zapisano {formatTime(lastSaved)}
      </div>
    )
  }
  return null
}

function formatTime(date) {
  return date.toLocaleTimeString('pl-PL', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
