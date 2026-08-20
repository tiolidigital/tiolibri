import { useState } from 'react'
import { useEditorState } from '@tiptap/react'
import { supabase } from '../../lib/supabase'

function DividerButton({ editor }) {
  const [showMenu, setShowMenu] = useState(false);

  const insertDivider = (style) => {
    editor.chain().focus().setDivider(style).run();
    setShowMenu(false);
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="px-3 py-1.5 text-sm font-medium rounded transition-colors text-gray-600 hover:bg-gray-100 hover:text-gray-900"
        title="Insert Divider"
        type="button"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="6" cy="10" r="1.5" fill="currentColor"/>
          <circle cx="10" cy="10" r="1.5" fill="currentColor"/>
          <circle cx="14" cy="10" r="1.5" fill="currentColor"/>
        </svg>
      </button>

      {showMenu && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          marginTop: '4px',
          backgroundColor: 'white',
          border: '1px solid #d1d5db',
          borderRadius: '6px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          padding: '8px',
          zIndex: 1000,
          minWidth: '200px',
        }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px', fontWeight: '500' }}>
            Choose divider style:
          </div>

          <button
            onClick={() => insertDivider('stars')}
            style={{
              display: 'block',
              width: '100%',
              padding: '8px',
              border: '1px solid #e5e7eb',
              borderRadius: '4px',
              backgroundColor: 'white',
              marginBottom: '4px',
              cursor: 'pointer',
              textAlign: 'center',
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#f9fafb'}
            onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
          >
            <svg width="60" height="16" viewBox="0 0 60 16" fill="none" style={{ margin: '0 auto', display: 'block' }}>
              <circle cx="20" cy="8" r="2" fill="currentColor"/>
              <circle cx="30" cy="8" r="2" fill="currentColor"/>
              <circle cx="40" cy="8" r="2" fill="currentColor"/>
            </svg>
          </button>

          <button
            onClick={() => insertDivider('line')}
            style={{
              display: 'block',
              width: '100%',
              padding: '8px',
              border: '1px solid #e5e7eb',
              borderRadius: '4px',
              backgroundColor: 'white',
              marginBottom: '4px',
              cursor: 'pointer',
              textAlign: 'center',
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#f9fafb'}
            onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
          >
            <svg width="100" height="16" viewBox="0 0 100 16" fill="none" style={{ margin: '0 auto', display: 'block' }}>
              <line x1="10" y1="8" x2="42" y2="8" stroke="currentColor" strokeWidth="1"/>
              <circle cx="50" cy="8" r="2.5" fill="currentColor"/>
              <line x1="58" y1="8" x2="90" y2="8" stroke="currentColor" strokeWidth="1"/>
            </svg>
          </button>

          <button
            onClick={() => insertDivider('dots')}
            style={{
              display: 'block',
              width: '100%',
              padding: '8px',
              border: '1px solid #e5e7eb',
              borderRadius: '4px',
              backgroundColor: 'white',
              cursor: 'pointer',
              textAlign: 'center',
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#f9fafb'}
            onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
          >
            <svg width="50" height="16" viewBox="0 0 50 16" fill="none" style={{ margin: '0 auto', display: 'block' }}>
              <circle cx="17" cy="8" r="1.5" fill="currentColor"/>
              <circle cx="25" cy="8" r="1.5" fill="currentColor"/>
              <circle cx="33" cy="8" r="1.5" fill="currentColor"/>
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}

export default function EditorToolbar({ editor, projectId, showInspector, onInspectorToggle, showPreview, onPreviewToggle }) {
  const [isUploading, setIsUploading] = useState(false)

  // Guzik „Plansza" musi widzieć bieżące zaznaczenie. TipTap 3 nie odświeża
  // paska przy samej zmianie kursora — stąd useEditorState.
  const figureState = useEditorState({
    editor,
    selector: ({ editor: e }) => ({
      active: !!e?.isActive('figure'),
      fullPage: !!e?.getAttributes('figure').fullPage,
    }),
  })

  if (!editor) return null

  const handleImageUpload = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/jpeg,image/jpg,image/png,image/gif'

    input.onchange = async (e) => {
      const file = e.target.files?.[0]
      if (!file) return

      // Validation
      const maxSize = 5 * 1024 * 1024 // 5MB
      if (file.size > maxSize) {
        alert('Image too large. Maximum size is 5MB.')
        return
      }

      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
      if (!allowedTypes.includes(file.type)) {
        alert('Invalid file type. Please upload JPG, PNG, or GIF.')
        return
      }

      try {
        setIsUploading(true)

        // Upload to Supabase Storage
        const fileName = `${Date.now()}-${file.name}`
        const filePath = `${projectId}/images/${fileName}`

        const { error: uploadError } = await supabase.storage
          .from('assets')
          .upload(filePath, file, {
            contentType: file.type,
            upsert: true,
          })

        if (uploadError) throw uploadError

        // Get public URL
        const { data: { publicUrl } } = supabase.storage
          .from('assets')
          .getPublicUrl(filePath)

        // Wstaw obraz razem z miejscem na podpis; kursor ląduje w podpisie,
        // więc autor pisze nazwę od razu po wgraniu.
        editor.chain().focus().setFigure({ src: publicUrl }).run()

        setIsUploading(false)
      } catch (error) {
        console.error('Image upload failed:', error)
        alert('Failed to upload image. Please try again.')
        setIsUploading(false)
      }
    }

    input.click()
  }

  const ToolbarButton = ({ onClick, isActive, children, title, disabled }) => (
    <button
      type="button"
      onClick={onClick}
      title={title}
      disabled={disabled}
      className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
        isActive
          ? 'bg-gray-200 text-gray-900'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      {children}
    </button>
  )

  const Divider = () => <div className="w-px h-6 bg-gray-200 mx-1" />

  return (
    <div className="flex items-center gap-1 w-full">
      {/* Headings */}
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
        isActive={editor.isActive('heading', { level: 1 })}
        title="Heading 1"
      >
        H1
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        isActive={editor.isActive('heading', { level: 2 })}
        title="Heading 2"
      >
        H2
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        isActive={editor.isActive('heading', { level: 3 })}
        title="Heading 3"
      >
        H3
      </ToolbarButton>

      <Divider />

      {/* Text formatting */}
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleBold().run()}
        isActive={editor.isActive('bold')}
        title="Bold (Ctrl+B)"
      >
        <strong>B</strong>
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleItalic().run()}
        isActive={editor.isActive('italic')}
        title="Italic (Ctrl+I)"
      >
        <em>I</em>
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleStrike().run()}
        isActive={editor.isActive('strike')}
        title="Strikethrough"
      >
        <s>S</s>
      </ToolbarButton>

      <Divider />

      {/* Lists */}
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        isActive={editor.isActive('bulletList')}
        title="Bullet list"
      >
        • List
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        isActive={editor.isActive('orderedList')}
        title="Numbered list"
      >
        1. List
      </ToolbarButton>

      <Divider />

      {/* Block elements */}
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
        isActive={editor.isActive('blockquote')}
        title="Quote"
      >
        " Quote
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().setHorizontalRule().run()}
        title="Horizontal rule"
      >
        ―
      </ToolbarButton>

      <Divider />

      {/* Image upload - Orange button */}
      <button
        onClick={handleImageUpload}
        disabled={isUploading || !projectId}
        className="px-3 py-1.5 bg-[#e3704a] hover:bg-[#FF4520] disabled:bg-gray-300 text-white rounded-lg text-sm font-medium transition-colors"
        title={isUploading ? "Uploading..." : "Insert image"}
      >
        {isUploading ? 'Uploading...' : 'Media'}
      </button>

      {/* Plansza: zaznaczona grafika dostaje całą stronę, bez numeru strony */}
      {figureState?.active && (
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleFigureFullPage().run()}
          isActive={figureState.fullPage}
          title="Plansza — cała strona dla tej grafiki (bez numeru strony)"
        >
          Plansza
        </ToolbarButton>
      )}

      {/* Divider */}
      <DividerButton editor={editor} />

      <Divider />

      {/* Undo/Redo */}
      <ToolbarButton
        onClick={() => editor.chain().focus().undo().run()}
        title="Undo (Ctrl+Z)"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
        </svg>
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().redo().run()}
        title="Redo (Ctrl+Y)"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 10h-10a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6" />
        </svg>
      </ToolbarButton>

      <Divider />

      {/* Preview Toggle */}
      {onPreviewToggle && (
        <button
          onClick={onPreviewToggle}
          className="ml-auto p-2 text-gray-600 hover:text-gray-900 transition-colors"
          title={showPreview ? "Hide Preview (⌘⇧P)" : "Show Preview (⌘⇧P)"}
        >
          {showPreview ? (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          )}
        </button>
      )}

      {/* Inspector Toggle */}
      {onInspectorToggle && (
        <button
          onClick={onInspectorToggle}
          className={`p-2 rounded transition-colors ${showInspector ? 'text-[#e3704a] bg-orange-50' : 'text-gray-400 hover:text-gray-700'}`}
          title={showInspector ? "Ukryj inspektor" : "Pokaż inspektor"}
        >
          {/* PanelRight icon */}
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <rect x="3" y="3" width="18" height="18" rx="2" strokeWidth={1.5} />
            <line x1="15" y1="3" x2="15" y2="21" strokeWidth={1.5} />
          </svg>
        </button>
      )}
    </div>
  )
}
