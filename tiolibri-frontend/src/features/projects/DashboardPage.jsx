import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../auth/useAuth'
import { useProjects } from './useProjects'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import ProjectCard from './ProjectCard'
import NewProjectModal from './NewProjectModal'
import UserMenu from '../../components/ui/UserMenu'

export default function DashboardPage() {
  const { user, signOut } = useAuth()
  const { projects, sharedProjects, loading, error, createProject, deleteProject, duplicateProject, importProject } = useProjects()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importError, setImportError] = useState(null)
  const importInputRef = useRef(null)

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

  const handleImportFile = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    // Reset the input so the same file can be picked again if needed
    e.target.value = ''
    setImporting(true)
    setImportError(null)
    try {
      await importProject(file)
    } catch (err) {
      setImportError(err.message)
    } finally {
      setImporting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">TIOLIBRI</h1>
          <UserMenu user={user} onSignOut={handleSignOut} />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
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
        ) : (
          <>
            {/* ── My projects ── */}
            <div className="mb-10">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Moje projekty</h2>
                <div className="flex items-center gap-2">
                  {/* Hidden file input for .tiolibri import */}
                  <input
                    ref={importInputRef}
                    type="file"
                    accept=".tiolibri"
                    className="hidden"
                    onChange={handleImportFile}
                  />
                  <Button
                    variant="ghost"
                    onClick={() => importInputRef.current?.click()}
                    disabled={importing}
                  >
                    {importing ? 'Importuję…' : '↑ Importuj backup'}
                  </Button>
                  <Button variant="primary" onClick={() => setIsModalOpen(true)}>
                    + Nowy projekt
                  </Button>
                </div>
              </div>
              {importError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">
                  {importError}
                </div>
              )}

              {projects.length === 0 ? (
                <Card>
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-5xl mb-4">📚</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Brak projektów</h3>
                    <p className="text-gray-600 mb-6">Utwórz swój pierwszy projekt e-booka.</p>
                    <Button variant="primary" onClick={() => setIsModalOpen(true)}>
                      Utwórz pierwszy projekt
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
                      onDuplicate={duplicateProject}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* ── Shared with me ── */}
            {sharedProjects.length > 0 && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-6">Udostępnione dla mnie</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {sharedProjects.map(project => (
                    <ProjectCard
                      key={project.id}
                      project={project}
                      sharedByEmail={project._shared_by_email}
                      onDelete={null}
                      onDuplicate={duplicateProject}
                    />
                  ))}
                </div>
              </div>
            )}
          </>
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
