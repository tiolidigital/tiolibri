import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../../lib/supabase'
import { authedFetch } from '../../lib/authedFetch'
import { convertGoogleDocsHtml, isGoogleDocsHtml } from '../../lib/htmlConverter'

// Fields that go through the backend (to trigger version snapshots).
const BACKEND_FIELDS = ['processed_html']

export function useChapters(projectId, projectLanguage = 'pl') {
  const [chapters, setChapters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchChapters = useCallback(async () => {
    if (!projectId) return

    setLoading(true)
    setError(null)

    try {
      const { data, error: fetchError } = await supabase
        .from('chapters')
        .select('*')
        .eq('project_id', projectId)
        .is('deleted_at', null)
        .order('sort_order', { ascending: true })

      if (fetchError) throw fetchError
      setChapters(data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  const uploadChapter = async (file) => {
    if (!projectId) throw new Error('No project ID')

    // Generate unique filename
    const timestamp = Date.now()
    const safeName = file.name.replace(/[^a-zA-Z0-9.-]/g, '_')
    const filePath = `${projectId}/${timestamp}_${safeName}`

    // Upload to Supabase Storage
    const { error: uploadError } = await supabase.storage
      .from('uploads')
      .upload(filePath, file)

    if (uploadError) throw uploadError

    // Get next sort order
    const maxOrder = chapters.reduce((max, ch) => Math.max(max, ch.sort_order || 0), 0)

    // Extract title from filename (remove extension)
    const title = file.name.replace(/\.html?$/i, '').replace(/_/g, ' ')

    // Insert chapter record
    const { data, error: insertError } = await supabase
      .from('chapters')
      .insert({
        project_id: projectId,
        title,
        sort_order: maxOrder + 1,
        source_file_path: filePath,
      })
      .select()
      .single()

    if (insertError) throw insertError

    // Add to local state
    setChapters(prev => [...prev, data])
    return data
  }

  const updateChapter = useCallback(async (id, updates) => {
    const hasBackendField = Object.keys(updates).some(k => BACKEND_FIELDS.includes(k))

    if (hasBackendField) {
      // Route through the backend so version snapshots are written.
      const data = await authedFetch(`/chapters/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      })
      setChapters(prev => prev.map(ch => ch.id === id ? data : ch))
      return data
    }

    // Metadata-only updates (title, sort_order, status…) go direct to Supabase.
    const { data, error } = await supabase
      .from('chapters')
      .update({ ...updates, updated_at: new Date().toISOString() })
      .eq('id', id)
      .select()
      .single()

    if (error) throw error

    setChapters(prev => prev.map(ch => ch.id === id ? data : ch))
    return data
  }, [])

  // Soft-delete: sends chapter to Trash, does not remove from DB.
  const softDeleteChapter = async (id) => {
    await authedFetch(`/chapters/${id}`, { method: 'DELETE' })
    setChapters(prev => prev.filter(ch => ch.id !== id))
  }

  // Legacy hard-delete kept for backwards compat (not exposed in UI).
  const deleteChapter = softDeleteChapter

  // Restore a soft-deleted chapter from Trash back into the chapter list.
  const restoreChapter = async (id) => {
    const result = await authedFetch(`/chapters/${id}/restore`, { method: 'POST' })
    // Re-fetch so sort_order is correct and the chapter appears in the right place.
    await fetchChapters()
    return result.chapter
  }

  // Hard-delete a chapter that is already in Trash.
  const permanentDeleteChapter = async (id) => {
    await authedFetch(`/chapters/${id}/permanent`, { method: 'DELETE' })
  }

  // Fetch soft-deleted chapters for the Trash UI.
  const fetchTrash = useCallback(async () => {
    if (!projectId) return []
    const result = await authedFetch(`/chapters/trash?project_id=${projectId}`)
    return result.chapters || []
  }, [projectId])

  // Update chapter status (draft | review | done) via backend.
  const updateChapterStatus = async (id, status) => {
    const data = await authedFetch(`/chapters/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
    setChapters(prev => prev.map(ch => ch.id === id ? data : ch))
    return data
  }

  // Toggle chapter lock via backend.
  const toggleChapterLock = async (id) => {
    const data = await authedFetch(`/chapters/${id}/lock`, { method: 'POST' })
    setChapters(prev => prev.map(ch => ch.id === id ? data : ch))
    return data
  }

  const reorderChapters = async (reorderedChapters) => {
    // Update local state immediately for optimistic UI
    setChapters(reorderedChapters)

    try {
      // Prepare order array for backend API
      const order = reorderedChapters.map((ch, index) => ({
        chapter_id: ch.id,
        sort_order: index + 1, // Start from 1
      }))

      const result = await authedFetch(`/projects/${projectId}/chapters/reorder`, {
        method: 'POST',
        body: JSON.stringify({ order }),
      })

      if (result.chapters) {
        setChapters(result.chapters)
      }
    } catch (err) {
      console.error('Failed to reorder chapters:', err)
      // Revert to original order on error
      await fetchChapters()
      throw err
    }
  }

  const getChapterContent = useCallback(async (chapterId, { signal } = {}) => {
    const chapter = chapters.find((ch) => ch.id === chapterId)
    if (!chapter) return null

    // Always fetch fresh from DB to get the latest saved processed_html.
    const { data: fresh, error: fetchError } = await supabase
      .from('chapters')
      .select('processed_html, source_file_path')
      .eq('id', chapterId)
      .single()

    if (fetchError) throw fetchError
    if (signal?.aborted) throw new DOMException('Aborted', 'AbortError')

    // If the chapter has been edited and saved, use the processed HTML from DB.
    if (fresh?.processed_html) return fresh.processed_html

    // Fall back to the original uploaded file (first-time load, never edited).
    const filePath = fresh?.source_file_path || chapter.source_file_path
    if (!filePath) return null

    const { data, error } = await supabase.storage
      .from('uploads')
      .download(filePath)

    if (error) throw error
    if (signal?.aborted) throw new DOMException('Aborted', 'AbortError')

    let html = await data.text()
    if (signal?.aborted) throw new DOMException('Aborted', 'AbortError')

    if (isGoogleDocsHtml(html)) {
      html = convertGoogleDocsHtml(html, projectLanguage)
    }

    return html
  }, [chapters, projectLanguage])

  useEffect(() => {
    fetchChapters()
  }, [fetchChapters])

  return {
    chapters,
    loading,
    error,
    fetchChapters,
    uploadChapter,
    updateChapter,
    deleteChapter,
    softDeleteChapter,
    restoreChapter,
    permanentDeleteChapter,
    fetchTrash,
    updateChapterStatus,
    toggleChapterLock,
    reorderChapters,
    getChapterContent,
  }
}

export default useChapters
