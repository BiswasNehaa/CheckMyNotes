import { useState } from 'react'
import { createSubject } from '../api'

export default function SubjectDashboard({ subjects, onSubjectCreated }) {
  const [name, setName] = useState('')
  const [color, setColor] = useState('#4F46E5')
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim()) return

    setError('')
    try {
      await createSubject({ name, color })
      setName('')
      onSubjectCreated()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <h2>Subjects</h2>

      <form className="card" onSubmit={handleSubmit}>
        <div className="form-row">
          <input
            type="text"
            placeholder="Subject name (e.g. Mathematics)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            title="Subject color"
          />
          <button type="submit">Add Subject</button>
        </div>
        {error && <p className="error">{error}</p>}
      </form>

      <div className="subject-grid">
        {subjects.length === 0 && <p>No subjects yet. Add one above.</p>}
        {subjects.map((subject) => (
          <div key={subject.id} className="card subject-card" style={{ borderLeftColor: subject.color }}>
            <h3>{subject.name}</h3>
            <p>{subject.page_count} pages uploaded</p>
            <p>Average score: {subject.average_score ?? 'N/A'}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
