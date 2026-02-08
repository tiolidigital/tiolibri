import { useState } from 'react'
import Button from '../../components/ui/Button'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function GenerateBooks({ projectId, projectTitle = 'book', stylePreset = 'classic', typographySettings = {}, coverImageUrl = null }) {
  const [urls, setUrls] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Create safe filename from project title
  const getSafeFilename = (extension) => {
    const safeName = projectTitle
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-') // Replace non-alphanumeric with dash
      .replace(/^-+|-+$/g, '') // Remove leading/trailing dashes
    return `${safeName}.${extension}`
  }

  const handleDownload = async (url, filename) => {
    try {
      const response = await fetch(url)
      const blob = await response.blob()
      const blobUrl = window.URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = blobUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      // Clean up
      window.URL.revokeObjectURL(blobUrl)
    } catch (err) {
      console.error('Download failed:', err)
      // Fallback: open in new tab
      window.open(url, '_blank')
    }
  }

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          formats: ['epub', 'pdf'],
          style_preset: stylePreset,
          text_align: typographySettings.textAlign || 'left',
          font_size: typographySettings.fontSize || 16,
          line_height: typographySettings.lineHeight || 1.7,
          margin_top: typographySettings.marginTop || 2,
          margin_bottom: typographySettings.marginBottom || 2,
          margin_left: typographySettings.marginLeft || 1.5,
          margin_right: typographySettings.marginRight || 1.5,
          chapter_spacing: typographySettings.chapterSpacing || 2,
          cover_image_url: coverImageUrl,
        }),
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Generation failed')
      }

      const data = await res.json()
      setUrls(data.files)
    } catch (err) {
      setError(err.message || 'Błąd podczas generowania. Spróbuj ponownie.')
      console.error('Generation failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-3">
      <button
        onClick={handleGenerate}
        disabled={loading}
        className="w-full py-2.5 px-4 bg-[#e3704a] hover:bg-[#FF4520] disabled:bg-gray-300 text-white rounded-lg font-semibold text-sm shadow-sm flex items-center justify-center gap-2 transition-colors"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Generating...
          </>
        ) : (
          <>Generate E-Book</>
        )}
      </button>

      {error && (
        <div className="text-xs text-red-600 text-center">{error}</div>
      )}

      {urls && (
        <div className="flex gap-2">
          {urls.epub && (
            <button
              onClick={() => handleDownload(urls.epub, getSafeFilename('epub'))}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors cursor-pointer"
            >
              EPUB
            </button>
          )}
          {urls.pdf && (
            <button
              onClick={() => handleDownload(urls.pdf, getSafeFilename('pdf'))}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors cursor-pointer"
            >
              PDF
            </button>
          )}
        </div>
      )}
    </div>
  )
}
