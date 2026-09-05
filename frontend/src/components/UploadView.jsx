import { useState } from 'react'
import { uploadPages, evaluatePage } from '../api'

function today() {
  return new Date().toISOString().slice(0, 10)
}

export default function UploadView({ subjects }) {
  const [subjectId, setSubjectId] = useState('')
  const [uploadDate, setUploadDate] = useState(today())
  const [files, setFiles] = useState([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [status, setStatus] = useState('idle') // idle | uploading | checking

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setMessage('')

    if (!subjectId) {
      setError('Please select a subject.')
      return
    }
    if (files.length === 0) {
      setError('Please select at least one image.')
      return
    }

    try {
      setStatus('uploading')
      const result = await uploadPages({ subjectId, uploadDate, files })

      // Evaluate each page right away so it doesn't sit as "pending" forever.
      setStatus('checking')
      for (const page of result.uploaded) {
        await evaluatePage(page.id)
      }

      setMessage(`Uploaded and checked ${result.uploaded.length} page(s) successfully.`)
      setFiles([])
      e.target.reset()
    } catch (err) {
      setError(err.message)
    } finally {
      setStatus('idle')
    }
  }

  const isBusy = status !== 'idle'
  const buttonLabel =
    status === 'uploading' ? 'Uploading...' : status === 'checking' ? 'Checking with AI...' : 'Upload'

  return (
    <div>
      <h2>Upload Notebook Pages</h2>

      <form className="card" onSubmit={handleSubmit}>
        <div className="form-row">
          <select value={subjectId} onChange={(e) => setSubjectId(e.target.value)}>
            <option value="">Select a subject</option>
            {subjects.map((subject) => (
              <option key={subject.id} value={subject.id}>
                {subject.name}
              </option>
            ))}
          </select>

          <input
            type="date"
            value={uploadDate}
            onChange={(e) => setUploadDate(e.target.value)}
          />
        </div>

        <div className="form-row">
          <input
            type="file"
            accept="image/*"
            multiple
            disabled={isBusy}
            onChange={(e) => setFiles(Array.from(e.target.files))}
          />
        </div>

        <button type="submit" disabled={isBusy}>
          {buttonLabel}
        </button>

        {message && <p className="success">{message}</p>}
        {error && <p className="error">{error}</p>}
      </form>
    </div>
  )
}
