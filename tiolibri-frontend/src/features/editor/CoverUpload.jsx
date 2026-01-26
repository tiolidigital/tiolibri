import { useState, useRef } from 'react'
import { supabase } from '../../lib/supabase'
import Button from '../../components/ui/Button'

const MAX_FILE_SIZE = 5 * 1024 * 1024 // 5MB
const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png']

export default function CoverUpload({ projectId, coverImageUrl, onCoverChange }) {
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef(null)

  const validateFile = (file) => {
    if (!file) {
      return 'No file selected'
    }

    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Only JPG and PNG files are allowed'
    }

    if (file.size > MAX_FILE_SIZE) {
      return 'File size must be less than 5MB'
    }

    return null
  }

  const uploadFile = async (file) => {
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      // Get file extension
      const ext = file.name.split('.').pop()
      const fileName = `cover.${ext}`
      const filePath = `${projectId}/${fileName}`

      // Upload to Supabase Storage (assets bucket)
      const { error: uploadError } = await supabase.storage
        .from('assets')
        .upload(filePath, file, {
          contentType: file.type,
          upsert: true, // Replace if exists
        })

      if (uploadError) throw uploadError

      // Get public URL
      const { data: { publicUrl } } = supabase.storage
        .from('assets')
        .getPublicUrl(filePath)

      // Call parent's onChange handler
      onCoverChange(publicUrl)
    } catch (err) {
      console.error('Upload failed:', err)
      setError(err.message || 'Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadFile(file)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files?.[0]
    if (file) {
      uploadFile(file)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDelete = async () => {
    if (!coverImageUrl) return

    setIsUploading(true)
    setError(null)

    try {
      // Extract file path from URL
      // URL format: https://[project].supabase.co/storage/v1/object/public/assets/[projectId]/cover.jpg
      const urlParts = coverImageUrl.split('/assets/')
      if (urlParts.length === 2) {
        const filePath = urlParts[1]

        // Delete from storage
        const { error: deleteError } = await supabase.storage
          .from('assets')
          .remove([filePath])

        if (deleteError) throw deleteError
      }

      // Clear from parent state
      onCoverChange(null)
    } catch (err) {
      console.error('Delete failed:', err)
      setError(err.message || 'Failed to delete cover')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      {coverImageUrl ? (
        // Preview mode
        <div className="relative">
          <div className="aspect-[2/3] w-full max-w-[200px] mx-auto rounded-lg overflow-hidden border-2 border-gray-200 shadow-sm">
            <img
              src={coverImageUrl}
              alt="Book cover"
              className="w-full h-full object-cover"
            />
          </div>

          <div className="mt-3 flex gap-2 justify-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              Change
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDelete}
              disabled={isUploading}
              className="text-red-600 hover:text-red-700"
            >
              {isUploading ? 'Deleting...' : 'Remove'}
            </Button>
          </div>
        </div>
      ) : (
        // Upload mode
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${
            isDragging
              ? 'border-[#e3704a] bg-[#FFF7F5]'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="space-y-2">
            <div className="text-4xl">📷</div>
            <div className="text-sm text-gray-600">
              {isUploading ? (
                <span className="text-[#e3704a]">Uploading...</span>
              ) : (
                <>
                  <span className="font-medium text-[#e3704a]">Click to upload</span>
                  {' or drag and drop'}
                </>
              )}
            </div>
            <div className="text-xs text-gray-400">
              JPG or PNG (max 5MB)
            </div>
          </div>
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".jpg,.jpeg,.png"
        onChange={handleFileSelect}
        className="hidden"
        disabled={isUploading}
      />

      {/* Error message */}
      {error && (
        <div className="text-sm text-red-600 text-center">
          {error}
        </div>
      )}

      {/* Success indicator */}
      {coverImageUrl && !error && !isUploading && (
        <div className="text-sm text-green-600 text-center flex items-center justify-center gap-1">
          <span>✓</span>
          <span>Cover uploaded</span>
        </div>
      )}
    </div>
  )
}
