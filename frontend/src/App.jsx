import { useEffect, useState } from 'react'
import { clearStoredStudent, getStoredStudent, getSubjects, storeStudent } from './api'
import Login from './components/Login'
import SubjectDashboard from './components/SubjectDashboard'
import UploadView from './components/UploadView'
import NotebookViewer from './components/NotebookViewer'
import './App.css'

export default function App() {
  const [student, setStudent] = useState(() => getStoredStudent())
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
    if (student) loadSubjects()
  }, [student])

  function handleLogin(loggedInStudent) {
    storeStudent(loggedInStudent)
    setStudent(loggedInStudent)
  }

  function handleLogout() {
    clearStoredStudent()
    setStudent(null)
    setSubjects([])
  }

  if (!student) {
    return <Login onLogin={handleLogin} />
  }

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
        <div className="app-header-user">
          <span>{student.name}</span>
          <button onClick={handleLogout}>Log out</button>
        </div>
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
