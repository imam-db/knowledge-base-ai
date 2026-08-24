import { useEffect, useRef, useState, type Dispatch } from 'react'
import { ChatInput } from '../components/ChatInput'
import { ChatWindow } from '../components/ChatWindow'
import { ErrorBanner } from '../components/ErrorBanner'
import { HealthIndicator } from '../components/HealthIndicator'
import { StatsPanel } from '../components/StatsPanel'
import { askQuestionStream, checkHealth, getStats } from '../services/api'
import type {
  AnswerStatus,
  ChatAction,
  ChatState,
  HealthResponse,
  StatsResponse,
  UiConfig,
} from '../types'

function createId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function shareUrlForQuestion(question: string): string {
  const url = new URL(window.location.href)
  url.searchParams.set('q', question)
  return url.toString()
}

type Props = {
  state: ChatState
  dispatch: Dispatch<ChatAction>
  uiConfig: UiConfig
}

export function ChatPage({ state, dispatch, uiConfig }: Props) {
  const [draft, setDraft] = useState('')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthLoading, setHealthLoading] = useState(true)
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [copyHint, setCopyHint] = useState<string | null>(null)
  const autoAsked = useRef(false)

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

  const handleSend = async (questionOverride?: string) => {
    const question = (questionOverride ?? draft).trim()
    if (!question || state.loading) return

    const userId = createId()
    const assistantId = createId()
    dispatch({ type: 'SEND_USER', payload: { id: userId, content: question } })
    setDraft('')
    dispatch({ type: 'SET_LOADING', payload: true })
    dispatch({ type: 'START_ASSISTANT', payload: { id: assistantId } })

    const url = new URL(window.location.href)
    url.searchParams.set('q', question)
    window.history.replaceState({}, '', url)

    try {
      await askQuestionStream(question, {
        onSources: ({ sources, retrieval_metadata }) => {
          dispatch({
            type: 'PATCH_ASSISTANT',
            payload: { id: assistantId, sources, retrieval_metadata },
          })
        },
        onToken: (token) => {
          dispatch({ type: 'APPEND_TOKEN', payload: { id: assistantId, token } })
        },
        onDone: (data) => {
          const status: AnswerStatus = data.status ?? 'answered'
          dispatch({
            type: 'PATCH_ASSISTANT',
            payload: {
              id: assistantId,
              content: data.answer,
              sources: data.sources,
              retrieval_metadata: data.retrieval_metadata,
              status,
              streaming: false,
            },
          })
          dispatch({ type: 'SET_LOADING', payload: false })
        },
        onError: (detail) => {
          dispatch({
            type: 'PATCH_ASSISTANT',
            payload: {
              id: assistantId,
              content: detail,
              status: 'error',
              streaming: false,
            },
          })
          dispatch({ type: 'SET_LOADING', payload: false })
        },
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'A system error occurred.'
      dispatch({
        type: 'PATCH_ASSISTANT',
        payload: {
          id: assistantId,
          content: message,
          status: 'error',
          streaming: false,
        },
      })
      dispatch({ type: 'SET_SYSTEM_ERROR', payload: message })
    }
  }

  useEffect(() => {
    if (autoAsked.current || state.loading) return
    const q = new URLSearchParams(window.location.search).get('q')?.trim()
    if (!q) return
    autoAsked.current = true
    void handleSend(q)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once on mount for ?q=
  }, [])

  const lastUserQuestion = [...state.messages].reverse().find((m) => m.role === 'user')?.content

  const handleCopyLink = async () => {
    const question = lastUserQuestion || draft.trim()
    if (!question) return
    const link = shareUrlForQuestion(question)
    try {
      await navigator.clipboard.writeText(link)
      setCopyHint('Link copied')
    } catch {
      setCopyHint(link)
    }
    window.setTimeout(() => setCopyHint(null), 2000)
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="border-b border-[var(--color-line)] bg-[var(--color-panel)]/80 px-4 py-3 backdrop-blur sm:px-6">
        <div className="mx-auto flex max-w-5xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-[var(--color-ink)]">
              {uiConfig.app_name}
            </h1>
            <p className="mt-0.5 text-sm text-[var(--color-ink-soft)]">{uiConfig.subtitle}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <HealthIndicator health={health} loading={healthLoading} />
            <StatsPanel stats={stats} />
            <button
              type="button"
              onClick={() => void handleCopyLink()}
              disabled={!lastUserQuestion && !draft.trim()}
              className="rounded-full border border-[var(--color-line)] bg-[var(--color-panel)] px-3 py-1 font-[family-name:var(--font-mono)] text-xs text-[var(--color-ink-soft)] transition hover:border-[var(--color-accent)] hover:text-[var(--color-accent-deep)] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {copyHint ?? 'Copy link'}
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-5xl flex-1 min-h-0 flex-col px-0 sm:px-4">
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-none border-x-0 border-[var(--color-line)] bg-[var(--color-panel)]/80 sm:my-4 sm:rounded-2xl sm:border sm:shadow-sm">
          <div className="px-4 pt-4 sm:px-6">
            {state.systemError && (
              <ErrorBanner
                message={state.systemError}
                onDismiss={() => dispatch({ type: 'CLEAR_SYSTEM_ERROR' })}
              />
            )}
          </div>
          <ChatWindow
            messages={state.messages}
            loading={state.loading && !state.messages.some((m) => m.streaming)}
            emptyStateTitle={uiConfig.empty_state_title}
            emptyStateDescription={uiConfig.empty_state_description}
            exampleQuestions={uiConfig.example_questions}
            indexedDocuments={stats?.documents ?? null}
            onExampleSelect={(question) => {
              void handleSend(question)
            }}
          />
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
