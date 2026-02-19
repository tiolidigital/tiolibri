import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../../lib/supabase'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useProjects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchProjects = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const { data, error: fetchError } = await supabase
        .from('projects')
        .select('*')
        .order('updated_at', { ascending: false })

      if (fetchError) throw fetchError
      setProjects(data || [])
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
    const res = await fetch(`${API_URL}/projects/${id}/duplicate`, { method: 'POST' })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Duplication failed')
    }
    const newProject = await res.json()
    setProjects(prev => [newProject, ...prev])
    return newProject
  }

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  return {
    projects,
    loading,
    error,
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    duplicateProject,
  }
}

export default useProjects
