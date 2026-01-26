import { useState } from 'react'
import { Link } from 'react-router-dom'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import { timeAgo } from '../../lib/utils'

export default function ProjectCard({ project, onDelete }) {
  const [showConfirm, setShowConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await onDelete(project.id)
    } catch (err) {
      console.error('Failed to delete project:', err)
      setDeleting(false)
      setShowConfirm(false)
    }
  }

  return (
    <Card className="flex flex-col">
      <div className="flex-1">
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-semibold text-gray-900 truncate pr-2">
            {project.title}
          </h3>
          <Badge variant={project.status}>{project.status}</Badge>
        </div>

        {project.author && (
          <p className="text-sm text-gray-600 mb-2">by {project.author}</p>
        )}

        <p className="text-xs text-gray-400">
          Updated {timeAgo(project.updated_at)}
        </p>
      </div>

      <div className="flex gap-2 mt-4 pt-4 border-t border-gray-100">
        {showConfirm ? (
          <>
            <Button
              variant="danger"
              className="flex-1"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Confirm'}
            </Button>
            <Button
              variant="ghost"
              className="flex-1"
              onClick={() => setShowConfirm(false)}
              disabled={deleting}
            >
              Cancel
            </Button>
          </>
        ) : (
          <>
            <Link to={`/editor/${project.id}`} className="flex-1">
              <Button variant="primary" className="w-full">
                Open
              </Button>
            </Link>
            <Button
              variant="ghost"
              onClick={() => setShowConfirm(true)}
            >
              Delete
            </Button>
          </>
        )}
      </div>
    </Card>
  )
}
