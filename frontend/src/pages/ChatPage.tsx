import { useEffect, useState, type Dispatch } from 'react'
import { ChatInput } from '../components/ChatInput'
import { ChatWindow } from '../components/ChatWindow'
import { ErrorBanner } from '../components/ErrorBanner'
import { HealthIndicator } from '../components/HealthIndicator'
import { StatsPanel } from '../components/StatsPanel'
import { askQuestion, checkHealth, getStats, searchDocuments } from '../services/api'
import type {
  ChatAction,
  ChatMessageItem,
  ChatState,
  HealthResponse,
  Source,
  StatsResponse,
} from '../types'

function createId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

async function enrichSources(question: string, sources: Source[]): Promise<Source[]> {
  if (!sources.length) return sources
  try {
    const search = await searchDocuments(question, 5)
    return sources.map((source) => {
      const match = search.results.find(
        (item) => item.document === source.document && item.page === source.page,
      )
      return match
        ? { ...source, chunk_id: match.chunk_id, distance: match.distance }
        : source
    })
  } catch {
    return sources
  }
}

type Props = {
  state: ChatState
  dispatch: Dispatch<ChatAction>
}

export function ChatPage({ state, dispatch }: Props) {
  const [draft, setDraft] = useState('')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthLoading, setHealthLoading] = useState(true)
  const [stats, setStats] = useState<StatsResponse | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const [healthRes, statsRes] = await Promise.all([checkHealth(), getStats()])
        if (!cancelled) {
          setHealth(healthRes)
          setStats(statsRes)
        }
      } catch {
        if (!cancelled) setHealth(null)
      } finally {
        if (!cancelled) setHealthLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const handleSend = async () => {
    const question = draft.trim()
    if (!question || state.loading) return

    const userId = createId()
    dispatch({ type: 'SEND_USER', payload: { id: userId, content: question } })
    setDraft('')
    dispatch({ type: 'SET_LOADING', payload: true })

    try {
      const result = await askQuestion(question)
      const enriched = await enrichSources(question, result.sources)
      const assistant: ChatMessageItem = {
        id: createId(),
        role: 'assistant',
        content: result.answer,
        sources: enriched,
        retrieval_metadata: result.retrieval_metadata,
        isError: false,
      }
      dispatch({ type: 'RECEIVE_ASSISTANT', payload: assistant })
      dispatch({ type: 'SET_LOADING', payload: false })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Terjadi kesalahan sistem.'
      dispatch({ type: 'SET_SYSTEM_ERROR', payload: message })
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="border-b border-[var(--color-line)] bg-white/80 px-4 py-3 backdrop-blur sm:px-6">
        <div className="mx-auto flex max-w-5xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-[var(--color-ink)]">
              Knowledge Base AI
            </h1>
            <p className="text-xs text-[var(--color-ink-soft)]">Jawaban berbasis dokumen internal</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <HealthIndicator health={health} loading={healthLoading} />
            <StatsPanel stats={stats} />
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-5xl flex-1 min-h-0 flex-col px-0 sm:px-4">
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-none border-x-0 border-[var(--color-line)] bg-white/70 sm:my-4 sm:rounded-3xl sm:border sm:shadow-sm">
          <div className="px-4 pt-4 sm:px-6">
            {state.systemError && (
              <ErrorBanner
                message={state.systemError}
                onDismiss={() => dispatch({ type: 'CLEAR_SYSTEM_ERROR' })}
              />
            )}
          </div>
          <ChatWindow messages={state.messages} loading={state.loading} />
          <ChatInput
            value={draft}
            loading={state.loading}
            onChange={setDraft}
            onSubmit={() => void handleSend()}
          />
        </div>
      </div>
    </div>
  )
}
