// Simple fetch helpers for talking to the FastAPI backend.
// In local dev, requests go through the Vite dev proxy (see vite.config.js).
// In production, set VITE_API_URL to the deployed backend's URL.

export const API_BASE = import.meta.env.VITE_API_URL || ''

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
  const res = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error('Failed to log in')
  return res.json()
}

export async function getSubjects() {
  const res = await fetch(`${API_BASE}/subjects`, { headers: authHeaders() })
  if (!res.ok) throw new Error('Failed to load subjects')
  return res.json()
}

export async function createSubject(subject) {
  const res = await fetch(`${API_BASE}/subjects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(subject),
  })
  if (!res.ok) throw new Error('Failed to create subject')
  return res.json()
}

export async function evaluatePage(pageId) {
  const res = await fetch(`${API_BASE}/pages/${pageId}/evaluate`, { method: 'POST' })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail || 'Failed to evaluate page')
  }
  return res.json()
}

export async function getNotebook(subjectId) {
  const res = await fetch(`${API_BASE}/subjects/${subjectId}/notebook`, { headers: authHeaders() })
  if (!res.ok) throw new Error('Failed to load notebook')
  return res.json()
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export async function downloadNotebookPdf(subjectId, subjectName) {
  const res = await fetch(`${API_BASE}/subjects/${subjectId}/notebook/pdf`, { headers: authHeaders() })
  if (!res.ok) throw new Error('Failed to generate notebook PDF')
  const blob = await res.blob()
  triggerDownload(blob, `${subjectName}_notebook.pdf`)
}

export async function downloadSessionPdf(subjectId, uploadDate, subjectName) {
  const res = await fetch(`${API_BASE}/subjects/${subjectId}/sessions/${uploadDate}/pdf`, { headers: authHeaders() })
  if (!res.ok) throw new Error('Failed to generate session PDF')
  const blob = await res.blob()
  triggerDownload(blob, `${subjectName}_${uploadDate}.pdf`)
}

export async function downloadPagePdf(pageId, subjectName, pageNumber) {
  const res = await fetch(`${API_BASE}/pages/${pageId}/pdf`, { headers: authHeaders() })
  if (!res.ok) throw new Error('Failed to generate page PDF')
  const blob = await res.blob()
  triggerDownload(blob, `${subjectName}_page${pageNumber}.pdf`)
}

export async function uploadPages({ subjectId, uploadDate, files }) {
  const formData = new FormData()
  formData.append('subject_id', subjectId)
  formData.append('upload_date', uploadDate)
  for (const file of files) {
    formData.append('files', file)
  }

  const res = await fetch(`${API_BASE}/pages/upload`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  })
  if (!res.ok) throw new Error('Failed to upload pages')
  return res.json()
}
