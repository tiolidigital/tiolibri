import { useState, useCallback } from 'react'
import { authedFetch } from '../../lib/authedFetch'

export function useShares(projectId) {
  const [shares, setShares] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchShares = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const data = await authedFetch(`/projects/${projectId}/shares`)
      setShares(data.shares || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  const addShare = async (email) => {
    const share = await authedFetch(`/projects/${projectId}/share`, {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
    setShares(prev => [...prev, share])
    return share
  }

  const removeShare = async (shareId) => {
    await authedFetch(`/projects/${projectId}/share/${shareId}`, { method: 'DELETE' })
    setShares(prev => prev.filter(s => s.id !== shareId))
  }

  return { shares, loading, error, fetchShares, addShare, removeShare }
}
