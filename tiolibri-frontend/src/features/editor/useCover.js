import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../../lib/supabase'
import { debounce } from '../../lib/utils'

export function useCover(projectId) {
  const [coverUrl, setCoverUrl] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Load cover URL from DB on mount
  useEffect(() => {
    if (!projectId) return

    const fetchCover = async () => {
      try {
        const { data, error: fetchError } = await supabase
          .from('projects')
          .select('cover_image_url')
          .eq('id', projectId)
          .single()

        if (fetchError) throw fetchError

        if (data?.cover_image_url) {
          setCoverUrl(data.cover_image_url)
        }
      } catch (err) {
        console.error('Failed to load cover:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchCover()
  }, [projectId])

  // Debounced save to DB (1 second delay)
  const saveToDb = useCallback(
    debounce(async (newCoverUrl) => {
      try {
        const { error: updateError } = await supabase
          .from('projects')
          .update({ cover_image_url: newCoverUrl })
          .eq('id', projectId)

        if (updateError) throw updateError

        console.log('Cover URL saved to database')
      } catch (err) {
        console.error('Failed to save cover URL:', err)
        setError(err.message)
      }
    }, 1000),
    [projectId]
  )

  // Update cover URL (local + DB)
  const updateCoverUrl = useCallback(
    (newCoverUrl) => {
      setCoverUrl(newCoverUrl)
      saveToDb(newCoverUrl)
    },
    [saveToDb]
  )

  return {
    coverUrl,
    setCoverUrl: updateCoverUrl,
    loading,
    error,
  }
}
