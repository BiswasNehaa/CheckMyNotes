// Simple fetch helpers for talking to the FastAPI backend.
// Requests go through the Vite dev proxy (see vite.config.js).

export async function getSubjects() {
  const res = await fetch('/subjects')
  if (!res.ok) throw new Error('Failed to load subjects')
  return res.json()
}

export async function createSubject(subject) {
  const res = await fetch('/subjects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(subject),
  })
  if (!res.ok) throw new Error('Failed to create subject')
  return res.json()
}

export async function getNotebook(subjectId) {
  const res = await fetch(`/subjects/${subjectId}/notebook`)
  if (!res.ok) throw new Error('Failed to load notebook')
  return res.json()
}

export async function uploadPages({ subjectId, uploadDate, files }) {
  const formData = new FormData()
  formData.append('subject_id', subjectId)
  formData.append('upload_date', uploadDate)
  for (const file of files) {
    formData.append('files', file)
  }

  const res = await fetch('/pages/upload', {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error('Failed to upload pages')
  return res.json()
}
