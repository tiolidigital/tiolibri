import { useEffect, useState, useRef } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import { Divider } from './extensions/Divider'
import EditorToolbar from './EditorToolbar'
import { getPreset } from '../../lib/presets'
import './editor.css'

export default function ChapterEditor({ chapter, content, onSave, onContentChange, projectId, focusMode, onFocusModeToggle, showPreview, onPreviewToggle, typographySettings, stylePreset }) {
  const [saving, setSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState(null)

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
    ],
    content: content || '',
    editorProps: {
      attributes: {
        class: 'tiptap-editor prose max-w-none focus:outline-none min-h-[500px]',
      },
    },
  })

  // Load content only when chapter changes — never on every `content` update,
  // otherwise setContent() resets the cursor mid-typing.
  useEffect(() => {
    if (editor && chapter?.id) {
      editor.commands.setContent(content || '', false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editor, chapter?.id])

  // Live update for preview
  useEffect(() => {
    if (!editor || !onContentChange) return

    const handleUpdate = () => {
      const html = editor.getHTML()
      onContentChange(html)
    }

    editor.on('update', handleUpdate)

    return () => {
      editor.off('update', handleUpdate)
    }
  }, [editor, onContentChange])

  // Auto-save with debounce — a single shared timer, reset on each keystroke.
  const saveTimeoutRef = useRef(null)
  useEffect(() => {
    if (!editor || !onSave) return

    const handleUpdate = () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
      saveTimeoutRef.current = setTimeout(async () => {
        const html = editor.getHTML()
        setSaving(true)
        try {
          await onSave(html)
          setLastSaved(new Date())
        } catch (err) {
          console.error('Failed to save:', err)
        } finally {
          setSaving(false)
        }
      }, 2000)
    }

    editor.on('update', handleUpdate)

    return () => {
      editor.off('update', handleUpdate)
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
    }
  }, [editor, onSave])

  if (!editor) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#e3704a]"></div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* Toolbar - Floating above paper */}
      <div className="sticky top-0 z-10 px-8 pt-6 pb-2 bg-gradient-to-b from-gray-100 to-transparent">
        <div className="max-w-4xl mx-auto bg-white border border-gray-200 rounded-lg shadow-sm">
          <div className="px-4 py-2">
            <EditorToolbar
              editor={editor}
              projectId={projectId}
              focusMode={focusMode}
              onFocusModeToggle={onFocusModeToggle}
              showPreview={showPreview}
              onPreviewToggle={onPreviewToggle}
            />
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

function formatTime(date) {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
