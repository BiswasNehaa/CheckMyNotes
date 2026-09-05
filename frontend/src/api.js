// Simple fetch helpers for talking to the FastAPI backend.
// Requests go through the Vite dev proxy (see vite.config.js).

const STUDENT_STORAGE_KEY = 'checkmynotes_student'

export function getStoredStudent() {
  try {
    const raw = localStorage.getItem(STUDENT_STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function storeStudent(student) {
  localStorage.setItem(STUDENT_STORAGE_KEY, JSON.stringify(student))
}

export function clearStoredStudent() {
  localStorage.removeItem(STUDENT_STORAGE_KEY)
}

function authHeaders() {
  const student = getStoredStudent()
  return student ? { 'X-Student-Id': student.id } : {}
}

export async function login(name) {
  const res = await fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error('Failed to log in')
  return res.json()
}

export async function getSubjects() {
  const res = await fetch('/subjects', { headers: authHeaders() })
  if (!res.ok) throw new Error('Failed to load subjects')
  return res.json()
}

export async function createSubject(subject) {
  const res = await fetch('/subjects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(subject),
  })
  if (!res.ok) throw new Error('Failed to create subject')
  return res.json()
}

export async function evaluatePage(pageId) {
  const res = await fetch(`/pages/${pageId}/evaluate`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to evaluate page')
  return res.json()
}

export async function getNotebook(subjectId) {
  const res = await fetch(`/subjects/${subjectId}/notebook`, { headers: authHeaders() })
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
    headers: authHeaders(),
    body: formData,
  })
  if (!res.ok) throw new Error('Failed to upload pages')
  return res.json()
}
