import type {
  AskResponse,
  DocumentsResponse,
  HealthResponse,
  SearchResponse,
  StatsResponse,
  UploadResponse,
} from '../types'

const API_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '')
  ?? 'http://localhost:8000/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })

  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = (await response.json()) as { detail?: string }
      if (body.detail) detail = typeof body.detail === 'string' ? body.detail : detail
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  return response.json() as Promise<T>
}

async function readErrorDetail(response: Response): Promise<string> {
  let detail = `Request failed (${response.status})`
  try {
    const body = (await response.json()) as { detail?: string }
    if (typeof body.detail === 'string' && body.detail) detail = body.detail
  } catch {
    // ignore
  }
  return detail
}

export function askQuestion(question: string): Promise<AskResponse> {
  return request<AskResponse>('/ask', {
    method: 'POST',
    body: JSON.stringify({ question }),
  })
}

export function searchDocuments(query: string, topK = 5): Promise<SearchResponse> {
  return request<SearchResponse>('/search', {
    method: 'POST',
    body: JSON.stringify({ query, top_k: topK }),
  })
}

export function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

export function getStats(): Promise<StatsResponse> {
  return request<StatsResponse>('/stats')
}

export function getDocuments(): Promise<DocumentsResponse> {
  return request<DocumentsResponse>('/documents')
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)

  const headers: HeadersInit = {}
  const apiKey = import.meta.env.VITE_ADMIN_API_KEY as string | undefined
  if (apiKey) headers['X-API-Key'] = apiKey

  const response = await fetch(`${API_URL}/documents/upload`, {
    method: 'POST',
    headers,
    body: form,
  })

  if (!response.ok) {
    throw new Error(await readErrorDetail(response))
  }

  return response.json() as Promise<UploadResponse>
}
