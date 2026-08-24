export interface Source {
  document: string
  page: number
  snippet?: string
  chunk_id?: number
  distance?: number
}

export interface RetrievalMetadata {
  top_k: number
  returned_chunks: number
  best_distance: number | null
}

export type AnswerStatus = 'answered' | 'not_found' | 'error'

export interface AskResponse {
  answer: string
  sources: Source[]
  retrieval_metadata: RetrievalMetadata
  confidence: number | null
  status?: AnswerStatus
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

export interface UiConfig {
  app_name: string
  mode: 'portfolio' | 'playground'
  show_documents: boolean
  show_about: boolean
  back_link: string
  back_label: string
  subtitle: string
  empty_state_title: string
  empty_state_description: string
  example_questions: string[]
}

export interface PipelineStep {
  label: string
  detail: string
}

export interface EvalSnapshot {
  dataset: string
  questions: number
  hit_at_5: number
  mrr?: number | null
  unanswerable_empty_rate?: number | null
  note?: string | null
}

export interface AboutLiveStats {
  documents: number
  chunks: number
  chunk_size: number
  chunk_overlap: number
  embedding_model: string
  llm_model: string
  hybrid_enabled: boolean
  top_k: number
}

export interface AboutResponse {
  show: boolean
  title?: string | null
  tagline?: string | null
  problem?: string | null
  approach?: string | null
  pipeline?: PipelineStep[]
  guardrails?: string[]
  tradeoffs?: string[]
  eval?: EvalSnapshot | null
  stats?: AboutLiveStats | null
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
  document_id: string
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

export interface DeleteResponse {
  document_id: string
  document_name: string
  chunks_deleted: number
  status: string
}

export type ChatRole = 'user' | 'assistant'

export interface ChatMessageItem {
  id: string
  role: ChatRole
  content: string
  sources?: Source[]
  retrieval_metadata?: RetrievalMetadata
  status?: AnswerStatus
  isError?: boolean
  streaming?: boolean
}

export type ChatState = {
  messages: ChatMessageItem[]
  loading: boolean
  systemError: string | null
}

export type ChatAction =
  | { type: 'SEND_USER'; payload: { id: string; content: string } }
  | { type: 'START_ASSISTANT'; payload: { id: string } }
  | { type: 'APPEND_TOKEN'; payload: { id: string; token: string } }
  | {
      type: 'PATCH_ASSISTANT'
      payload: {
        id: string
        sources?: Source[]
        retrieval_metadata?: RetrievalMetadata
        status?: AnswerStatus
        content?: string
        streaming?: boolean
      }
    }
  | { type: 'RECEIVE_ASSISTANT'; payload: ChatMessageItem }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_SYSTEM_ERROR'; payload: string | null }
  | { type: 'CLEAR_SYSTEM_ERROR' }
