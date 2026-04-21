import { useState, useCallback } from 'react'
import { authedFetch } from '../../lib/authedFetch'

export function useVersions(chapterId) {
  const [versions, setVersions] = useState([])
  const [loading, setLoading] = useState(!!chapterId)
  const [error, setError] = useState(null)

  const fetchVersions = useCallback(async () => {
    if (!chapterId) {
      setVersions([])
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data = await authedFetch(`/chapters/${chapterId}/versions?limit=20`)
      setVersions(data.versions || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [chapterId])

  const getVersionContent = useCallback(async (versionId) => {
    return authedFetch(`/chapters/${chapterId}/versions/${versionId}`)
  }, [chapterId])

  const restoreVersion = useCallback(async (versionId) => {
    const result = await authedFetch(`/chapters/${chapterId}/versions/${versionId}/restore`, {
      method: 'POST',
    })
    // Reload version list after restore (a new snapshot was created)
    await fetchVersions()
    return result
  }, [chapterId, fetchVersions])

  return {
    versions,
    loading,
    error,
    fetchVersions,
    getVersionContent,
    restoreVersion,
  }
}

export default useVersions
