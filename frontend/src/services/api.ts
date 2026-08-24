import type {
  AboutResponse,
  AskResponse,
  DeleteResponse,
  DocumentsResponse,
  HealthResponse,
  SearchResponse,
  StatsResponse,
  UiConfig,
  UploadResponse,
} from '../types'

const API_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '')
  ?? 'http://localhost:8000/api/v1'

function networkErrorMessage(): string {
  return `Cannot reach the API (${API_URL}). Make sure the backend is running — wait ~30s after start/reload, then refresh the page.`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
    })
  } catch {
    throw new Error(networkErrorMessage())
  }

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

export type AskStreamHandlers = {
  onStatus?: (phase: string) => void
  onSources?: (data: {
    sources: AskResponse['sources']
    retrieval_metadata: AskResponse['retrieval_metadata']
  }) => void
  onToken?: (token: string) => void
  onDone?: (data: AskResponse) => void
  onError?: (detail: string) => void
}

export async function askQuestionStream(
  question: string,
  handlers: AskStreamHandlers,
): Promise<void> {
  let response: Response
  try {
    response = await fetch(`${API_URL}/ask/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
  } catch {
    throw new Error(networkErrorMessage())
  }

  if (!response.ok || !response.body) {
    throw new Error(await readErrorDetail(response))
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const dispatchBlock = (block: string) => {
    const lines = block.split('\n')
    let eventName = 'message'
    const dataLines: string[] = []
    for (const line of lines) {
      if (line.startsWith('event:')) eventName = line.slice(6).trim()
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
    }
    if (!dataLines.length) return
    const raw = dataLines.join('\n')
    let data: Record<string, unknown>
    try {
      data = JSON.parse(raw) as Record<string, unknown>
    } catch {
      return
    }
    if (eventName === 'status' && typeof data.phase === 'string') {
      handlers.onStatus?.(data.phase)
    } else if (eventName === 'sources') {
      handlers.onSources?.({
        sources: (data.sources as AskResponse['sources']) ?? [],
        retrieval_metadata: data.retrieval_metadata as AskResponse['retrieval_metadata'],
      })
    } else if (eventName === 'token' && typeof data.token === 'string') {
      handlers.onToken?.(data.token)
    } else if (eventName === 'done') {
      handlers.onDone?.(data as unknown as AskResponse)
    } else if (eventName === 'error') {
      handlers.onError?.(typeof data.detail === 'string' ? data.detail : 'Stream error')
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''
    for (const part of parts) {
      if (part.trim()) dispatchBlock(part)
    }
  }
  if (buffer.trim()) dispatchBlock(buffer)
}

export function searchDocuments(query: string, topK = 5): Promise<SearchResponse> {
  return request<SearchResponse>('/search', {
    method: 'POST',
    body: JSON.stringify({ query, top_k: topK }),
  })
}

export function getUiConfig(): Promise<UiConfig> {
  return request<UiConfig>('/config')
}

export function getAbout(): Promise<AboutResponse> {
  return request<AboutResponse>('/about')
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

export async function deleteDocument(documentId: string): Promise<DeleteResponse> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  const apiKey = import.meta.env.VITE_ADMIN_API_KEY as string | undefined
  if (apiKey) headers['X-API-Key'] = apiKey

  const response = await fetch(
    `${API_URL}/documents/${encodeURIComponent(documentId)}`,
    { method: 'DELETE', headers },
  )

  if (!response.ok) {
    throw new Error(await readErrorDetail(response))
  }

  return response.json() as Promise<DeleteResponse>
}
