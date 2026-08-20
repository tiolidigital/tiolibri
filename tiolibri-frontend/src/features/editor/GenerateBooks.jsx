import { useState } from 'react'
import Button from '../../components/ui/Button'
import { authedFetch } from '../../lib/authedFetch'
import { bookFilename } from '../../lib/filename'

export default function GenerateBooks({ projectId, projectTitle = 'book', stylePreset = 'classic', typographySettings = {}, coverImageUrl = null }) {
  const [urls, setUrls] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Create safe filename from project title
  const getSafeFilename = (extension) => bookFilename(projectTitle, extension)

  // Pobieranie idzie zwyklym linkiem, nie przez fetch+blob.
  //
  // Powod: blob wymagal `await fetch(...)` miedzy klikiem a wywolaniem `.click()`.
  // Chromium (Arc) liczy gest uzytkownika na sekundy — gdy odpowiedz z CDN-a przyszla
  // pozniej, pobranie bylo po cichu blokowane i nic sie nie dzialo. Do tego
  // `revokeObjectURL()` lecial synchronicznie zaraz po `.click()`, co potrafi uciac
  // pobieranie zanim wystartuje. EPUB (wiekszy, czesciej cache MISS) obrywal, PDF nie.
  //
  // Supabase Storage przyjmuje `?download=nazwa` i odsyla
  // `Content-Disposition: attachment; filename=...`, wiec nazwa pliku zostaje nasza.
  const downloadUrl = (url, filename) =>
    `${url}${url.includes('?') ? '&' : '?'}download=${encodeURIComponent(filename)}`

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await authedFetch('/generate', {
        method: 'POST',
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
          toc_enabled: typographySettings.tocEnabled || false,
          toc_depth: typographySettings.tocDepth || 2,
          // `!== false`, bo domyslnie chowamy — brak ustawienia w starym projekcie
          // ma znaczyc „chowaj", a nie „pokazuj".
          hide_opener_title: typographySettings.hideOpenerTitle !== false,
        }),
      })
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
            <a
              href={downloadUrl(urls.epub, getSafeFilename('epub'))}
              download={getSafeFilename('epub')}
              rel="noopener"
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors cursor-pointer"
            >
              EPUB
            </a>
          )}
          {urls.pdf && (
            <a
              href={downloadUrl(urls.pdf, getSafeFilename('pdf'))}
              download={getSafeFilename('pdf')}
              rel="noopener"
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors cursor-pointer"
            >
              PDF
            </a>
          )}
        </div>
      )}
    </div>
  )
}
