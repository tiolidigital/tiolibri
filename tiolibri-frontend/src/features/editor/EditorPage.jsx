import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { supabase } from '../../lib/supabase'
import { useChapters } from './useChapters'
import { useTypography } from './useTypography'
import { useCover } from './useCover'
import { useAuth } from '../auth/useAuth'
import { STYLE_PRESETS } from '../../lib/presets'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import CollapsibleSection from '../../components/ui/CollapsibleSection'
import ChapterList from './ChapterList'
import ChapterUpload from './ChapterUpload'
import ChapterEditor from './ChapterEditor'
import GenerateBooks from './GenerateBooks'
import TypographyControls from './TypographyControls'
import CoverUpload from './CoverUpload'
import BookPreview from './BookPreview'

export default function EditorPage() {
  const { projectId } = useParams()
  const { user } = useAuth()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedChapterId, setSelectedChapterId] = useState(null)
  const [chapterContent, setChapterContent] = useState('')
  const [liveContent, setLiveContent] = useState('') // Live content from editor for preview
  const [showUpload, setShowUpload] = useState(false)
  const [stylePreset, setStylePreset] = useState('classic')

  // Collapsible sections state
  const [openSections, setOpenSections] = useState({
    projectDetails: false,
    style: false,
    cover: false,
    typography: true,  // Default open
    production: false,  // Closed by default
  })

  const [focusMode, setFocusMode] = useState(false)

  // Preview mode state with localStorage persistence
  const [showPreview, setShowPreview] = useState(() => {
    const saved = localStorage.getItem('tiolibri_show_preview')
    if (saved !== null) {
      return JSON.parse(saved)
    }
    // Default: show on desktop (>1440px), hide on smaller screens
    return window.innerWidth >= 1440
  })

  // Check if screen is ultrawide (>= 2560px) for side-by-side layout
  const [isUltrawide, setIsUltrawide] = useState(window.innerWidth >= 2560)

  const {
    chapters,
    loading: chaptersLoading,
    uploadChapter,
    updateChapter,
    deleteChapter,
    getChapterContent,
  } = useChapters(projectId)

  const {
    settings: typographySettings,
    updateSettings: setTypographySettings,
    loading: typographyLoading
  } = useTypography(projectId)

  const {
    coverUrl,
    setCoverUrl,
    loading: coverLoading
  } = useCover(projectId)

  const selectedChapter = chapters.find(ch => ch.id === selectedChapterId)

  // Persist showPreview state to localStorage
  useEffect(() => {
    localStorage.setItem('tiolibri_show_preview', JSON.stringify(showPreview))
  }, [showPreview])

  // Keyboard shortcut for preview toggle (Cmd+Shift+P / Ctrl+Shift+P)
  // Disabled when Focus Mode is active
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Cmd+Shift+P or Ctrl+Shift+P
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'p') {
        e.preventDefault()

        // Only toggle preview if Focus Mode is OFF
        if (!focusMode) {
          setShowPreview(prev => !prev)
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [focusMode])

  // Update isUltrawide on window resize
  useEffect(() => {
    const handleResize = () => {
      setIsUltrawide(window.innerWidth >= 2560)
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Fetch project data
  useEffect(() => {
    async function fetchProject() {
      try {
        const { data, error: fetchError } = await supabase
          .from('projects')
          .select('*')
          .eq('id', projectId)
          .single()

        if (fetchError) throw fetchError
        setProject(data)
        setStylePreset(data.style_preset || 'classic')
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchProject()
  }, [projectId])

  // Load chapter content when selected
  useEffect(() => {
    async function loadContent() {
      if (!selectedChapterId) {
        setChapterContent('')
        setLiveContent('')
        return
      }

      // First check if there's processed_html
      const chapter = chapters.find(ch => ch.id === selectedChapterId)
      if (chapter?.processed_html) {
        setChapterContent(chapter.processed_html)
        setLiveContent(chapter.processed_html)
        return
      }

      // Otherwise load from storage
      try {
        const content = await getChapterContent(selectedChapterId)
        setChapterContent(content || '')
        setLiveContent(content || '')
      } catch (err) {
        console.error('Failed to load chapter:', err)
        setChapterContent('')
        setLiveContent('')
      }
    }

    loadContent()
  }, [selectedChapterId, chapters, getChapterContent])

  const handleUpdateProject = async (field, value) => {
    try {
      const { error } = await supabase
        .from('projects')
        .update({ [field]: value, updated_at: new Date().toISOString() })
        .eq('id', projectId)

      if (error) throw error
      setProject(prev => ({ ...prev, [field]: value }))
    } catch (err) {
      console.error('Failed to update project:', err)
    }
  }

  const handleSaveChapter = useCallback(async (html) => {
    if (!selectedChapterId) return

    await updateChapter(selectedChapterId, { processed_html: html })
  }, [selectedChapterId, updateChapter])

  const toggleSection = (section) => {
    setOpenSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  // Handle Focus Mode toggle with auto-hide preview
  const handleFocusModeToggle = useCallback(() => {
    const newFocusMode = !focusMode
    setFocusMode(newFocusMode)

    // If enabling Focus Mode, hide preview
    if (newFocusMode && showPreview) {
      setShowPreview(false)
    }
  }, [focusMode, showPreview])

  // Get user initials
  const getUserInitials = () => {
    if (!user?.email) return 'U'
    return user.email.charAt(0).toUpperCase()
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#e3704a]"></div>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Project not found'}</p>
          <Link to="/dashboard">
            <Button variant="primary">Back to Dashboard</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#e3704a] rounded flex items-center justify-center text-white font-bold text-lg">
              📚
            </div>
            <span className="text-xl font-bold text-gray-900">TIOLIBRI</span>
          </div>
          <div className="text-sm text-gray-600">
            <span className="font-medium">PROJECT:</span> <span className="uppercase tracking-wide">{project.title}</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-green-600 bg-green-50 px-3 py-1 rounded-full">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Saved
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gray-200 rounded-full flex items-center justify-center text-sm font-semibold">
            {getUserInitials()}
          </div>
        </div>
      </header>

      {/* Main content - 3 columns */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Chapters Only */}
        {!focusMode && (
          <div className="w-64 bg-white border-r border-gray-200 flex flex-col overflow-hidden">
            {/* Chapters */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="p-4 pb-3 flex items-center justify-between border-b border-gray-100">
                <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Chapters</h2>
              </div>

              <div className="flex-1 overflow-y-auto px-3 py-3">
                <ChapterList
                  chapters={chapters}
                  loading={chaptersLoading}
                  selectedId={selectedChapterId}
                  onSelect={setSelectedChapterId}
                  onDelete={deleteChapter}
                />
              </div>

              <div className="p-3 border-t border-gray-100">
                <button
                  onClick={() => setShowUpload(true)}
                  className="w-full py-2 px-3 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors flex items-center justify-center gap-2 border border-gray-200 border-dashed"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  <span>Add New Chapter</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main content area - Split view when preview enabled */}
        <div className="flex-1 flex overflow-hidden">
          {/* Center - Editor with Paper Effect */}
          <div className={`flex flex-col overflow-hidden bg-gray-100 transition-all duration-300 ${showPreview && isUltrawide ? 'w-[60%]' : 'w-full'}`}>
            {selectedChapterId ? (
              <ChapterEditor
                key={selectedChapterId}
                chapter={selectedChapter}
                content={chapterContent}
                onSave={handleSaveChapter}
                onContentChange={setLiveContent}
                projectId={projectId}
                focusMode={focusMode}
                onFocusModeToggle={handleFocusModeToggle}
                showPreview={showPreview}
                onPreviewToggle={() => setShowPreview(!showPreview)}
                typographySettings={typographySettings}
                stylePreset={stylePreset}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400 bg-gray-100">
                <div className="text-center">
                  <p className="text-lg">Select a chapter to edit</p>
                  {chapters.length === 0 && (
                    <Button
                      variant="primary"
                      className="mt-4"
                      onClick={() => setShowUpload(true)}
                    >
                      Upload your first chapter
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right - Book Preview (side-by-side on ultrawide) */}
          {showPreview && !focusMode && isUltrawide && (
            <aside className="w-[40%] bg-gray-100 border-l border-gray-200 overflow-hidden">
              <BookPreview
                content={liveContent}
                typography={typographySettings}
                preset={stylePreset}
                isFullScreen={false}
                onClose={() => setShowPreview(false)}
              />
            </aside>
          )}

          {/* Full-screen preview on smaller screens */}
          {showPreview && !focusMode && !isUltrawide && (
            <div className="absolute inset-0 z-50 bg-gray-100">
              <BookPreview
                content={liveContent}
                typography={typographySettings}
                preset={stylePreset}
                isFullScreen={true}
                onClose={() => setShowPreview(false)}
              />
            </div>
          )}
        </div>

        {/* Right Panel - Inspector with Collapsible Sections */}
        {!focusMode && (
          <aside className="w-80 bg-white border-l border-gray-200 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto">
              <div className="p-5">
                <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
                  Inspector
                </h2>

                <div className="space-y-3">
                {/* Project Details Section */}
                <CollapsibleSection
                  title="Project Details"
                  isOpen={openSections.projectDetails}
                  onToggle={() => toggleSection('projectDetails')}
                >
                  <div className="space-y-3 mt-4">
                    <div>
                      <label className="block text-xs text-gray-500 mb-1.5">Title</label>
                      <Input
                        value={project.title}
                        onChange={(e) => handleUpdateProject('title', e.target.value)}
                        placeholder="Book title"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1.5">Author</label>
                      <Input
                        value={project.author || ''}
                        onChange={(e) => handleUpdateProject('author', e.target.value)}
                        placeholder="Author name"
                      />
                    </div>
                  </div>
                </CollapsibleSection>

                {/* Style Preset Section */}
                <CollapsibleSection
                  title="Style Preset"
                  isOpen={openSections.style}
                  onToggle={() => toggleSection('style')}
                >
                  <div className="space-y-2 mt-4">
                    {Object.entries(STYLE_PRESETS).map(([key, preset]) => (
                      <label
                        key={key}
                        className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                          stylePreset === key
                            ? 'border-[#e3704a] bg-[#FFF7F5]'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="stylePreset"
                          value={key}
                          checked={stylePreset === key}
                          onChange={(e) => {
                            setStylePreset(e.target.value)
                            handleUpdateProject('style_preset', e.target.value)
                          }}
                          className="accent-[#e3704a]"
                        />
                        <div>
                          <div className="font-medium text-gray-900">{preset.name}</div>
                          <div className="text-xs text-gray-500">{preset.description}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </CollapsibleSection>

                {/* Cover Image Section */}
                <CollapsibleSection
                  title="Cover Image"
                  isOpen={openSections.cover}
                  onToggle={() => toggleSection('cover')}
                >
                  <div className="mt-4">
                    {coverLoading ? (
                      <div className="text-center py-4 text-sm text-gray-500">
                        Loading cover...
                      </div>
                    ) : (
                      <CoverUpload
                        projectId={projectId}
                        coverImageUrl={coverUrl}
                        onCoverChange={setCoverUrl}
                      />
                    )}
                  </div>
                </CollapsibleSection>

                {/* Typography Section */}
                <CollapsibleSection
                  title="Typography"
                  isOpen={openSections.typography}
                  onToggle={() => toggleSection('typography')}
                >
                  <div className="mt-4">
                    {typographyLoading ? (
                      <div className="text-center py-4 text-sm text-gray-500">
                        Loading settings...
                      </div>
                    ) : (
                      <TypographyControls
                        value={typographySettings}
                        onChange={setTypographySettings}
                      />
                    )}
                  </div>
                </CollapsibleSection>
                </div>
              </div>
            </div>

            {/* Bottom Section - Generate & Export */}
            <div className="border-t border-gray-200 p-5 bg-gray-50">
              <div className="space-y-3">
                <h4 className="text-xs font-medium text-gray-500 mb-3">Production</h4>

                <div className="space-y-2 mb-4">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked className="accent-gray-400" />
                    <span className="text-sm text-gray-700">EPUB 3.0</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked className="accent-gray-400" />
                    <span className="text-sm text-gray-700">PDF (Print Ready)</span>
                  </label>
                </div>

                <GenerateBooks
                  projectId={projectId}
                  stylePreset={stylePreset}
                  typographySettings={typographySettings}
                  coverImageUrl={coverUrl}
                />
              </div>
            </div>
          </aside>
        )}
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <ChapterUpload
          onClose={() => setShowUpload(false)}
          onUpload={async (file) => {
            await uploadChapter(file)
          }}
        />
      )}
    </div>
  )
}
