export interface Source {
  document: string
  page: number
  chunk_id?: number
  distance?: number
}

export interface RetrievalMetadata {
  top_k: number
  returned_chunks: number
  best_distance: number | null
}

export interface AskResponse {
  answer: string
  sources: Source[]
  retrieval_metadata: RetrievalMetadata
  confidence: number | null
}

export interface SearchResultItem {
  document: string
  page: number
  chunk_id: number
  distance: number
  text: string
}

export interface SearchResponse {
  results: SearchResultItem[]
  debug?: {
    embedding_time_ms: number
    retrieval_time_ms: number
    threshold: number
    collection_name: string
  }
}

export interface HealthResponse {
  status: string
  embedding: string
  vector_db: string
  groq: string
}

export interface StatsResponse {
  documents: number
  chunks: number
}

export interface DocumentInfo {
  name: string
  pages: number
  uploaded_at: string
}

export interface DocumentsResponse {
  documents: DocumentInfo[]
}

export interface UploadResponse {
  document_id: string
  document_name: string
  chunks_created: number
  status: string
}

export type ChatRole = 'user' | 'assistant'

export interface ChatMessageItem {
  id: string
  role: ChatRole
  content: string
  sources?: Source[]
  retrieval_metadata?: RetrievalMetadata
  isError?: boolean
}

export type ChatState = {
  messages: ChatMessageItem[]
  loading: boolean
  systemError: string | null
}

export type ChatAction =
  | { type: 'SEND_USER'; payload: { id: string; content: string } }
  | { type: 'RECEIVE_ASSISTANT'; payload: ChatMessageItem }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_SYSTEM_ERROR'; payload: string | null }
  | { type: 'CLEAR_SYSTEM_ERROR' }
