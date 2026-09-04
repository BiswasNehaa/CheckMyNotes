import { useEffect, useState } from 'react'
import { getSubjects } from './api'
import SubjectDashboard from './components/SubjectDashboard'
import UploadView from './components/UploadView'
import NotebookViewer from './components/NotebookViewer'
import './App.css'

export default function App() {
  const [view, setView] = useState('dashboard')
  const [subjects, setSubjects] = useState([])

  async function loadSubjects() {
    try {
      const data = await getSubjects()
      setSubjects(data)
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    loadSubjects()
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>CheckMyNotes</h1>
        <nav>
          <button
            className={view === 'dashboard' ? 'active' : ''}
            onClick={() => setView('dashboard')}
          >
            Subjects
          </button>
          <button
            className={view === 'upload' ? 'active' : ''}
            onClick={() => setView('upload')}
          >
            Upload
          </button>
          <button
            className={view === 'notebook' ? 'active' : ''}
            onClick={() => setView('notebook')}
          >
            Notebook
          </button>
        </nav>
      </header>

      <main>
        {view === 'dashboard' && (
          <SubjectDashboard subjects={subjects} onSubjectCreated={loadSubjects} />
        )}
        {view === 'upload' && <UploadView subjects={subjects} />}
        {view === 'notebook' && <NotebookViewer subjects={subjects} />}
      </main>
    </div>
  )
}
