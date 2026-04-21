import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../../lib/supabase'
import { authedFetch } from '../../lib/authedFetch'

export function useProjects() {
  const [projects, setProjects] = useState([])
  const [sharedProjects, setSharedProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchProjects = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const { data: { user } } = await supabase.auth.getUser()

      // Own projects (filter by user_id to exclude shared projects that RLS now exposes)
      const { data: ownData, error: ownError } = await supabase
        .from('projects')
        .select('*')
        .eq('user_id', user?.id)
        .order('updated_at', { ascending: false })

      if (ownError) throw ownError
      setProjects(ownData || [])

      // Shared projects (enriched with owner email via backend)
      const sharedData = await authedFetch('/projects/shared')
      setSharedProjects(sharedData.projects || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const createProject = async ({ title, author = '', language = 'pl' }) => {
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) throw new Error('Not authenticated')

    const { data, error } = await supabase
      .from('projects')
      .insert({
        user_id: user.id,
        title,
        author,
        language,
        status: 'draft',
      })
      .select()
      .single()

    if (error) throw error

    // Add to local state
    setProjects(prev => [data, ...prev])
    return data
  }

  const updateProject = async (id, updates) => {
    const { data, error } = await supabase
      .from('projects')
      .update({ ...updates, updated_at: new Date().toISOString() })
      .eq('id', id)
      .select()
      .single()

    if (error) throw error

    // Update local state
    setProjects(prev => prev.map(p => p.id === id ? data : p))
    return data
  }

  const deleteProject = async (id) => {
    const { error } = await supabase
      .from('projects')
      .delete()
      .eq('id', id)

    if (error) throw error

    // Remove from local state
    setProjects(prev => prev.filter(p => p.id !== id))
  }

  const duplicateProject = async (id) => {
    const newProject = await authedFetch(`/projects/${id}/duplicate`, { method: 'POST' })
    setProjects(prev => [newProject, ...prev])
    return newProject
  }

  const importProject = async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const newProject = await authedFetch('/projects/import', {
      method: 'POST',
      body: formData,
      skipContentType: true,
    })
    setProjects(prev => [newProject, ...prev])
    return newProject
  }

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  return {
    projects,
    sharedProjects,
    loading,
    error,
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    duplicateProject,
    importProject,
  }
}

export default useProjects
