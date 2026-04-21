import { useState, useCallback } from 'react'
import { authedFetch } from '../../lib/authedFetch'

export function useSnapshots(projectId) {
  const [snapshots, setSnapshots] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchSnapshots = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const data = await authedFetch(`/projects/${projectId}/snapshots`)
      setSnapshots(data.snapshots || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  const createSnapshot = useCallback(async () => {
    const data = await authedFetch(`/projects/${projectId}/snapshots`, { method: 'POST' })
    setSnapshots(prev => [data, ...prev])
    return data
  }, [projectId])

  const restoreSnapshot = useCallback(async (snapshotId) => {
    const data = await authedFetch(
      `/projects/${projectId}/snapshots/${snapshotId}/restore`,
      { method: 'POST' },
    )
    // After restore a pre-restore snapshot is created — re-fetch to show it
    await fetchSnapshots()
    return data
  }, [projectId, fetchSnapshots])

  return { snapshots, loading, error, fetchSnapshots, createSnapshot, restoreSnapshot }
}
