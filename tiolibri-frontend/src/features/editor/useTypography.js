import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../../lib/supabase'
import { debounce } from '../../lib/utils'

const DEFAULT_SETTINGS = {
  textAlign: 'left',
  fontSize: 16,
  lineHeight: 1.7,
  marginTop: 2,
  marginBottom: 2,
  marginLeft: 1.5,
  marginRight: 1.5,
  chapterSpacing: 2,
  tocEnabled: false,
  tocDepth: 2,
  // Rozdzial otwarty grafika: tytul zwykle jest juz NA grafice, wiec drukowany
  // naglowek powtarzalby go drugi raz. Domyslnie chowamy — naglowek zostaje
  // w tresci (spis tresci ma dokad skakac), tylko przestaje byc widoczny.
  hideOpenerTitle: true
}

export function useTypography(projectId) {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Load settings from DB
  useEffect(() => {
    if (!projectId) return

    const fetchSettings = async () => {
      try {
        const { data, error } = await supabase
          .from('projects')
          .select('typography_settings')
          .eq('id', projectId)
          .single()

        if (error) throw error

        if (data?.typography_settings) {
          setSettings({ ...DEFAULT_SETTINGS, ...data.typography_settings })
        }
      } catch (err) {
        console.error('Failed to load typography settings:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchSettings()
  }, [projectId])

  // Debounced save to DB (1 second delay)
  const saveToDb = useCallback(
    debounce(async (newSettings) => {
      try {
        const { error } = await supabase
          .from('projects')
          .update({ typography_settings: newSettings })
          .eq('id', projectId)

        if (error) throw error

        console.log('Typography settings saved')
      } catch (err) {
        console.error('Failed to save typography settings:', err)
        setError(err.message)
      }
    }, 1000),
    [projectId]
  )

  // Update settings (local + DB)
  const updateSettings = useCallback(
    (newSettings) => {
      setSettings(newSettings)
      saveToDb(newSettings)
    },
    [saveToDb]
  )

  return {
    settings,
    updateSettings,
    loading,
    error
  }
}
