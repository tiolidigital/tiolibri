import { useState, useEffect } from 'react'
import { useAuth } from '../auth/useAuth'
import { useProjects } from './useProjects'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import ProjectCard from './ProjectCard'
import NewProjectModal from './NewProjectModal'

export default function DashboardPage() {
  const { user, signOut } = useAuth()
  const { projects, loading, error, createProject, deleteProject } = useProjects()
  const [isModalOpen, setIsModalOpen] = useState(false)

  useEffect(() => {
    document.title = 'Dashboard - TIOLIBRI'
  }, [])

  const handleSignOut = async () => {
    try {
      await signOut()
    } catch (err) {
      console.error('Failed to sign out:', err)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">TIOLIBRI</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <Button variant="ghost" onClick={handleSignOut}>
              Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Your Projects</h2>
          <Button variant="primary" onClick={() => setIsModalOpen(true)}>
            + New Project
          </Button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-6">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading projects...</p>
          </div>
        ) : projects.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <div className="text-gray-400 text-5xl mb-4">📚</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
              <p className="text-gray-600 mb-6">Create your first e-book project to get started.</p>
              <Button variant="primary" onClick={() => setIsModalOpen(true)}>
                Create your first project
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map(project => (
              <ProjectCard
                key={project.id}
                project={project}
                onDelete={deleteProject}
              />
            ))}
          </div>
        )}
      </main>

      <NewProjectModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={createProject}
      />
    </div>
  )
}
