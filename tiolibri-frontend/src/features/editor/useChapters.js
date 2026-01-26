import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../../lib/supabase'

export function useChapters(projectId) {
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

  const updateChapter = async (id, updates) => {
    const { data, error } = await supabase
      .from('chapters')
      .update({ ...updates, updated_at: new Date().toISOString() })
      .eq('id', id)
      .select()
      .single()

    if (error) throw error

    setChapters(prev => prev.map(ch => ch.id === id ? data : ch))
    return data
  }

  const deleteChapter = async (id) => {
    // Find chapter to get file path
    const chapter = chapters.find(ch => ch.id === id)

    // Delete from database first
    const { error: deleteError } = await supabase
      .from('chapters')
      .delete()
      .eq('id', id)

    if (deleteError) throw deleteError

    // Delete from storage if file exists
    if (chapter?.source_file_path) {
      await supabase.storage
        .from('uploads')
        .remove([chapter.source_file_path])
    }

    // Remove from local state
    setChapters(prev => prev.filter(ch => ch.id !== id))
  }

  const reorderChapters = async (reorderedChapters) => {
    // Update local state immediately
    setChapters(reorderedChapters)

    // Update sort_order in database
    const updates = reorderedChapters.map((ch, index) => ({
      id: ch.id,
      sort_order: index,
    }))

    for (const update of updates) {
      await supabase
        .from('chapters')
        .update({ sort_order: update.sort_order })
        .eq('id', update.id)
    }
  }

  const getChapterContent = async (chapterId) => {
    const chapter = chapters.find(ch => ch.id === chapterId)
    if (!chapter?.source_file_path) return null

    const { data, error } = await supabase.storage
      .from('uploads')
      .download(chapter.source_file_path)

    if (error) throw error

    return await data.text()
  }

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
    reorderChapters,
    getChapterContent,
  }
}

export default useChapters
