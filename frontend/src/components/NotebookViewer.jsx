import { useState } from 'react'
import { getNotebook } from '../api'

export default function NotebookViewer({ subjects }) {
  const [subjectId, setSubjectId] = useState('')
  const [notebook, setNotebook] = useState(null)
  const [selectedPage, setSelectedPage] = useState(null)
  const [activeMistake, setActiveMistake] = useState(null)
  const [error, setError] = useState('')

  function handleSelectPage(page) {
    setSelectedPage(page)
    setActiveMistake(null)
  }

  async function handleSelectSubject(id) {
    setSubjectId(id)
    setNotebook(null)
    setSelectedPage(null)
    setError('')
    if (!id) return

    try {
      const data = await getNotebook(id)
      setNotebook(data)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <h2>Notebook Viewer</h2>

      <div className="form-row">
        <select value={subjectId} onChange={(e) => handleSelectSubject(e.target.value)}>
          <option value="">Select a subject</option>
          {subjects.map((subject) => (
            <option key={subject.id} value={subject.id}>
              {subject.name}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="error">{error}</p>}

      {notebook && (
        <div className="notebook-layout">
          <div className="session-list">
            {notebook.sessions.length === 0 && <p>No pages uploaded yet for this subject.</p>}
            {notebook.sessions.map((session) => (
              <div key={session.date} className="card">
                <h3>{session.formatted_date}</h3>
                <div className="page-thumbs">
                  {session.pages.map((page) => (
                    <button
                      key={page.id}
                      className={selectedPage?.id === page.id ? 'active' : ''}
                      onClick={() => handleSelectPage(page)}
                    >
                      Page {page.page_number} ({page.status})
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="page-detail card">
            {!selectedPage && <p>Select a page on the left to view it.</p>}

            {selectedPage && (
              <div>
                <div className="image-wrapper">
                  <img src={selectedPage.image_url} alt={`Page ${selectedPage.page_number}`} />
                  {selectedPage.evaluation?.mistakes.map((pin, index) => (
                    <span
                      key={pin.id}
                      className={`pin pin-${pin.severity}`}
                      style={{ left: `${pin.x_percent}%`, top: `${pin.y_percent}%` }}
                      title={pin.title}
                      onClick={() => setActiveMistake(pin)}
                    >
                      {index + 1}
                    </span>
                  ))}
                </div>

                <p className="pin-hint">Click a numbered marker on the image to see what it means.</p>

                {activeMistake && (
                  <div className={`mistake-popup mistake-${activeMistake.severity}`}>
                    <strong>{activeMistake.title}</strong>
                    <p>{activeMistake.explanation}</p>
                    {activeMistake.corrected_step && <p>Correction: {activeMistake.corrected_step}</p>}
                    {activeMistake.concept_refresher && <p>Tip: {activeMistake.concept_refresher}</p>}
                  </div>
                )}

                {!selectedPage.evaluation && (
                  <p className="pending-note">This page is still pending evaluation.</p>
                )}

                {selectedPage.evaluation && (
                  <div className="evaluation">
                    <h3>
                      Score: {selectedPage.evaluation.score} — {selectedPage.evaluation.grade_label}
                    </h3>
                    <p>{selectedPage.evaluation.summary}</p>

                    <ul className="mistake-list">
                      {selectedPage.evaluation.mistakes.map((mistake, index) => (
                        <li key={mistake.id} className={`mistake mistake-${mistake.severity}`}>
                          <strong>
                            {index + 1}. {mistake.title}
                          </strong>
                          <p>{mistake.explanation}</p>
                          {mistake.corrected_step && <p>Correction: {mistake.corrected_step}</p>}
                          {mistake.concept_refresher && <p>Tip: {mistake.concept_refresher}</p>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
