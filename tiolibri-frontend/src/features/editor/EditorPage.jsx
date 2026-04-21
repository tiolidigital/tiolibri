import { useState, useEffect, useCallback, useRef } from 'react'
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
import VersionHistory from './VersionHistory'
import TrashSection from './TrashSection'
import CollaborationSection from './CollaborationSection'
import ProjectSnapshots from './ProjectSnapshots'
import FindReplacePanel from './FindReplacePanel'

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
    typography: true,
    production: false,
    history: false,
    snapshots: false,
    collaboration: false,
  })

  const [showInspector, setShowInspector] = useState(false)

  // Find & Replace panel state
  const [findReplaceOpen, setFindReplaceOpen] = useState(false)
  const [findReplaceShowReplace, setFindReplaceShowReplace] = useState(false)
  const [findReplaceScope, setFindReplaceScope] = useState('chapter')
  const editorRef = useRef(null)

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
    fetchChapters,
    uploadChapter,
    updateChapter,
    softDeleteChapter,
    restoreChapter,
    permanentDeleteChapter,
    fetchTrash,
    updateChapterStatus,
    toggleChapterLock,
    reorderChapters,
    getChapterContent,
  } = useChapters(projectId, project?.language)

  // The current user is the project owner if the project's user_id matches their id.
  const isOwner = project?.user_id === user?.id

  const {
    settings: typographySettings,
    updateSettings: setTypographySettings,
    loading: typographyLoading,
  } = useTypography(projectId)

  const { coverUrl, setCoverUrl, loading: coverLoading } = useCover(projectId)

  const selectedChapter = chapters.find((ch) => ch.id === selectedChapterId)

  // Persist showPreview state to localStorage
  useEffect(() => {
    localStorage.setItem('tiolibri_show_preview', JSON.stringify(showPreview))
  }, [showPreview])

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      const mod = e.metaKey || e.ctrlKey

      // Cmd+Shift+P — toggle preview
      if (mod && e.shiftKey && e.key === 'p') {
        e.preventDefault()
        setShowPreview((prev) => !prev)
        return
      }

      // Cmd+F — open Find panel (search only)
      if (mod && !e.shiftKey && e.key === 'f') {
        if (!selectedChapterId) return
        e.preventDefault()
        setFindReplaceShowReplace(false)
        setFindReplaceOpen(true)
        return
      }

      // Cmd+H — open Find & Replace panel
      if (mod && !e.shiftKey && e.key === 'h') {
        if (!selectedChapterId) return
        e.preventDefault()
        setFindReplaceShowReplace(true)
        setFindReplaceOpen(true)
        return
      }

      // Esc — close Find & Replace panel (only when panel is open)
      if (e.key === 'Escape' && findReplaceOpen) {
        setFindReplaceOpen(false)
        editorRef.current?.commands?.clearSearch?.()
        return
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedChapterId, findReplaceOpen])

  // Update isUltrawide on window resize
  useEffect(() => {
    const handleResize = () => {
      setIsUltrawide(window.innerWidth >= 2560)
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const fetchProject = useCallback(async () => {
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
  }, [projectId])

  useEffect(() => {
    fetchProject()
  }, [fetchProject])

  // Update document title with project name
  useEffect(() => {
    if (project?.title) {
      document.title = `${project.title} - TIOLIBRI`
    } else {
      document.title = 'Editor - TIOLIBRI'
    }
  }, [project])

  // Load chapter content when selected. Abort in-flight fetches on re-selection
  // so a slow response for an old chapter can never overwrite a newer one's content.
  useEffect(() => {
    if (!selectedChapterId) return

    const controller = new AbortController()
    const loadForId = selectedChapterId

    async function loadContent() {
      const chapter = chapters.find((ch) => ch.id === loadForId)
      if (chapter?.processed_html) {
        if (controller.signal.aborted) return
        setChapterContent(chapter.processed_html)
        setLiveContent(chapter.processed_html)
        return
      }

      try {
        const content = await getChapterContent(loadForId, { signal: controller.signal })
        if (controller.signal.aborted) return
        setChapterContent(content || '')
        setLiveContent(content || '')
      } catch (err) {
        if (err.name === 'AbortError' || controller.signal.aborted) return
        console.error('Failed to load chapter:', err)
        setChapterContent('')
        setLiveContent('')
      }
    }

    loadContent()
    return () => {
      controller.abort()
    }
  }, [selectedChapterId, chapters, getChapterContent])

  const handleUpdateProject = async (field, value) => {
    try {
      const { error } = await supabase
        .from('projects')
        .update({ [field]: value, updated_at: new Date().toISOString() })
        .eq('id', projectId)

      if (error) throw error
      setProject((prev) => ({ ...prev, [field]: value }))
    } catch (err) {
      console.error('Failed to update project:', err)
    }
  }

  const handleSaveChapter = useCallback(
    async (html) => {
      if (!selectedChapterId) return

      await updateChapter(selectedChapterId, { processed_html: html })
    },
    [selectedChapterId, updateChapter]
  )

  // Used by FindReplacePanel for book-scope replace (saves any chapter by id).
  const handleSaveChapterById = useCallback(
    async (chapterId, html) => {
      await updateChapter(chapterId, { processed_html: html })
    },
    [updateChapter]
  )

  const handleCloseFindReplace = useCallback(() => {
    setFindReplaceOpen(false)
    editorRef.current?.commands?.clearSearch?.()
  }, [])

  const handleSoftDelete = useCallback(
    async (id) => {
      await softDeleteChapter(id)
      if (selectedChapterId === id) {
        setSelectedChapterId(null)
        setChapterContent('')
        setLiveContent('')
      }
    },
    [softDeleteChapter, selectedChapterId]
  )

  // Called after a version restore: refresh chapter list + reload editor content.
  const handleVersionRestored = useCallback(
    async (updatedChapter) => {
      if (!updatedChapter) return
      // Re-fetch chapters so word count etc. reflect the restored content.
      await fetchChapters()
      setChapterContent(updatedChapter.processed_html || '')
      setLiveContent(updatedChapter.processed_html || '')
    },
    [fetchChapters]
  )

  // Called after a snapshot restore: reload project metadata + chapters, clear editor.
  const handleSnapshotRestored = useCallback(async () => {
    await Promise.all([fetchProject(), fetchChapters()])
    setSelectedChapterId(null)
    setChapterContent('')
    setLiveContent('')
  }, [fetchProject, fetchChapters])

  const toggleSection = (section) => {
    setOpenSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  const handleInspectorToggle = useCallback(() => {
    setShowInspector((prev) => !prev)
  }, [])

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
          <Link
            to="/dashboard"
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <div className="w-8 h-8 bg-[#e3704a] rounded flex items-center justify-center text-white font-bold text-lg">
              📚
            </div>
            <span className="text-xl font-bold text-gray-900">TIOLIBRI</span>
          </Link>
          <div className="text-sm text-gray-600">
            <span className="font-medium">PROJECT:</span>{' '}
            <span className="uppercase tracking-wide">{project.title}</span>
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
        {/* Left Panel - Chapters (always visible) */}
        <div className="w-64 bg-white border-r border-gray-200 flex flex-col overflow-hidden">
            {/* Chapters */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="p-4 pb-3 flex items-center justify-between border-b border-gray-100">
                <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Chapters
                </h2>
              </div>

              <div className="flex-1 overflow-y-auto px-3 py-3">
                <ChapterList
                  chapters={chapters}
                  loading={chaptersLoading}
                  selectedId={selectedChapterId}
                  isOwner={isOwner}
                  currentUserId={user?.id}
                  onSelect={(id) => {
                    // Clear the previous chapter's content in the same event
                    // handler so the remounting ChapterEditor's first render
                    // sees empty content, not the previous chapter's HTML.
                    setChapterContent('')
                    setLiveContent('')
                    setSelectedChapterId(id)
                  }}
                  onDelete={handleSoftDelete}
                  onReorder={reorderChapters}
                  onRename={(id, title) => updateChapter(id, { title })}
                  onSetStatus={updateChapterStatus}
                  onToggleLock={toggleChapterLock}
                />

                {/* Trash — inside the scroll area so it doesn't overflow the panel */}
                <TrashSection
                  fetchTrash={fetchTrash}
                  onRestore={restoreChapter}
                  onPermanentDelete={permanentDeleteChapter}
                />
              </div>

              <div className="p-3 border-t border-gray-100">
                <button
                  onClick={() => setShowUpload(true)}
                  className="w-full py-2 px-3 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors flex items-center justify-center gap-2 border border-gray-200 border-dashed"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4v16m8-8H4"
                    />
                  </svg>
                  <span>Add New Chapter</span>
                </button>
              </div>
            </div>
        </div>

        {/* Main content area - Split view when preview enabled */}
        <div className="flex-1 flex overflow-hidden">
          {/* Center - Editor with Paper Effect */}
          <div
            className={`flex flex-col overflow-hidden bg-gray-100 transition-all duration-300 ${showPreview && isUltrawide ? 'w-[60%]' : 'w-full'}`}
          >
            {selectedChapterId ? (
              <div className="flex flex-col h-full relative">
                {/* Find & Replace panel — floats below toolbar, above content */}
                {findReplaceOpen && (
                  <div className="sticky top-0 z-20 px-8 pt-2">
                    <div className="max-w-4xl mx-auto relative">
                      <FindReplacePanel
                        editor={editorRef.current}
                        showReplace={findReplaceShowReplace}
                        scope={findReplaceScope}
                        onScopeChange={setFindReplaceScope}
                        chapters={chapters}
                        onSaveChapter={handleSaveChapterById}
                        onClose={handleCloseFindReplace}
                      />
                    </div>
                  </div>
                )}
                <ChapterEditor
                  key={selectedChapterId}
                  chapter={selectedChapter}
                  content={chapterContent}
                  onSave={handleSaveChapter}
                  onContentChange={setLiveContent}
                  projectId={projectId}
                  showInspector={showInspector}
                  onInspectorToggle={handleInspectorToggle}
                  showPreview={showPreview}
                  onPreviewToggle={() => setShowPreview(!showPreview)}
                  typographySettings={typographySettings}
                  stylePreset={stylePreset}
                  currentUserId={user?.id}
                  editorRef={editorRef}
                />
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400 bg-gray-100">
                <div className="text-center">
                  <p className="text-lg">Select a chapter to edit</p>
                  {chapters.length === 0 && (
                    <Button variant="primary" className="mt-4" onClick={() => setShowUpload(true)}>
                      Upload your first chapter
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right - Book Preview (side-by-side on ultrawide) */}
          {showPreview && isUltrawide && (
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
          {showPreview && !isUltrawide && (
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

        {/* Right Panel - Inspector (hidden by default, toggled via toolbar) */}
        {showInspector && (
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

                  {/* History Section */}
                  <CollapsibleSection
                    title="Historia wersji"
                    isOpen={openSections.history}
                    onToggle={() => toggleSection('history')}
                  >
                    <div className="mt-2">
                      <VersionHistory
                        chapterId={selectedChapterId}
                        currentContent={chapterContent}
                        onContentRestored={handleVersionRestored}
                      />
                    </div>
                  </CollapsibleSection>

                  {/* Snapshots Section */}
                  <CollapsibleSection
                    title="Snapshoty projektu"
                    isOpen={openSections.snapshots}
                    onToggle={() => toggleSection('snapshots')}
                  >
                    <div className="mt-2">
                      <ProjectSnapshots projectId={projectId} onRestored={handleSnapshotRestored} />
                    </div>
                  </CollapsibleSection>

                  {/* Collaboration Section */}
                  <CollapsibleSection
                    title="Współpraca"
                    isOpen={openSections.collaboration}
                    onToggle={() => toggleSection('collaboration')}
                  >
                    <div className="mt-2">
                      <CollaborationSection projectId={projectId} isOwner={isOwner} />
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
                  projectTitle={project?.title}
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
