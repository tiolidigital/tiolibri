import { useState, useRef } from 'react'
import Modal from '../../components/ui/Modal'
import Button from '../../components/ui/Button'

export default function ChapterUpload({ onClose, onUpload }) {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState({})
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFiles = (fileList) => {
    const htmlFiles = Array.from(fileList).filter(
      (f) => f.name.endsWith('.html') || f.name.endsWith('.htm')
    )

    if (htmlFiles.length !== fileList.length) {
      setError('Only HTML files are accepted')
    } else {
      setError('')
    }

    setFiles((prev) => [...prev, ...htmlFiles])
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setUploading(true)
    setError('')

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        setUploadProgress((prev) => ({ ...prev, [file.name]: 'uploading' }))

        try {
          await onUpload(file)
          setUploadProgress((prev) => ({ ...prev, [file.name]: 'done' }))
        } catch (err) {
          setUploadProgress((prev) => ({ ...prev, [file.name]: 'error' }))
          throw err
        }
      }

      // Close modal after successful upload
      setTimeout(() => {
        onClose()
      }, 500)
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <Modal isOpen={true} onClose={onClose} className="max-w-2xl">
      <div className="space-y-5">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Source Content Section */}
        <div>
          <label className="block text-sm font-medium text-gray-900 mb-3">
            Source Content
          </label>

          {/* Drop zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragging
                ? 'border-[#e3704a] bg-[#FFF7F5]'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".html,.htm"
              multiple
              onChange={(e) => handleFiles(e.target.files)}
              className="hidden"
            />

            {/* Cloud icon */}
            <div className="mb-3">
              <svg className="w-16 h-16 mx-auto text-gray-300" fill="currentColor" viewBox="0 0 24 24">
                <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/>
              </svg>
            </div>

            <div className="text-sm text-gray-600">
              <span className="font-medium text-[#e3704a] cursor-pointer hover:text-[#FF4520]">
                Upload a file
              </span>
              <span> or drag and drop</span>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              HTML, DOCX, or RTF up to 10MB
            </p>
          </div>
        </div>

        {/* OR IMPORT FROM divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200"></div>
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="px-2 bg-white text-gray-400 uppercase tracking-wide">OR IMPORT FROM</span>
          </div>
        </div>

        {/* Connect to Google Docs button */}
        <button
          disabled
          className="w-full py-3 px-4 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-400 cursor-not-allowed flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
          </svg>
          Connect to Google Docs
        </button>

        {/* File list */}
        {files.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-700">
              Files to upload ({files.length})
            </h3>
            <div className="max-h-48 overflow-y-auto space-y-2">
              {files.map((file, index) => (
                <div
                  key={`${file.name}-${index}`}
                  className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-gray-400">📄</span>
                    <span className="text-sm text-gray-700 truncate">
                      {file.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {uploadProgress[file.name] === 'uploading' && (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-[#e3704a]"></div>
                    )}
                    {uploadProgress[file.name] === 'done' && (
                      <span className="text-green-600">✓</span>
                    )}
                    {uploadProgress[file.name] === 'error' && (
                      <span className="text-red-600">✗</span>
                    )}
                    {!uploadProgress[file.name] && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          removeFile(index)
                        }}
                        className="text-gray-400 hover:text-red-600"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Upload button for files */}
            <Button
              variant="primary"
              onClick={handleUpload}
              disabled={files.length === 0 || uploading}
              className="w-full"
            >
              {uploading ? 'Uploading...' : `Upload ${files.length} file${files.length !== 1 ? 's' : ''}`}
            </Button>
          </div>
        )}
      </div>

      {/* Gray bottom bar with Cancel */}
      <div className="mt-6 -mx-6 -mb-6 px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-start">
        <Button variant="ghost" onClick={onClose} disabled={uploading}>
          Cancel
        </Button>
      </div>
    </Modal>
  )
}
