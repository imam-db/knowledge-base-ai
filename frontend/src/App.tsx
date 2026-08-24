import { useEffect, useReducer, useState } from 'react'
import { AboutPanel } from './components/AboutPanel'
import { ChatPage } from './pages/ChatPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { getUiConfig } from './services/api'
import type { ChatAction, ChatState, UiConfig } from './types'

type Tab = 'chat' | 'documents'

const initialChatState: ChatState = {
  messages: [],
  loading: false,
  systemError: null,
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SEND_USER':
      return {
        ...state,
        systemError: null,
        messages: [
          ...state.messages,
          { id: action.payload.id, role: 'user', content: action.payload.content },
        ],
      }
    case 'START_ASSISTANT':
      return {
        ...state,
        messages: [
          ...state.messages,
          {
            id: action.payload.id,
            role: 'assistant',
            content: '',
            streaming: true,
          },
        ],
      }
    case 'APPEND_TOKEN':
      return {
        ...state,
        messages: state.messages.map((m) =>
          m.id === action.payload.id
            ? { ...m, content: m.content + action.payload.token, streaming: true }
            : m,
        ),
      }
    case 'PATCH_ASSISTANT':
      return {
        ...state,
        messages: state.messages.map((m) =>
          m.id === action.payload.id
            ? {
                ...m,
                ...action.payload,
                streaming: action.payload.streaming ?? m.streaming,
              }
            : m,
        ),
      }
    case 'RECEIVE_ASSISTANT':
      return {
        ...state,
        messages: [...state.messages, action.payload],
      }
    case 'SET_LOADING':
      return { ...state, loading: action.payload }
    case 'SET_SYSTEM_ERROR':
      return { ...state, systemError: action.payload, loading: false }
    case 'CLEAR_SYSTEM_ERROR':
      return { ...state, systemError: null }
    default:
      return state
  }
}

export default function App() {
  const [tab, setTab] = useState<Tab>('chat')
  const [aboutOpen, setAboutOpen] = useState(false)
  const [uiConfig, setUiConfig] = useState<UiConfig | null>(null)
  const [configError, setConfigError] = useState<string | null>(null)
  const [chatState, chatDispatch] = useReducer(chatReducer, initialChatState)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const config = await getUiConfig()
        if (!cancelled) setUiConfig(config)
      } catch (error) {
        if (!cancelled) {
          setConfigError(
            error instanceof Error ? error.message : 'Failed to load UI configuration',
          )
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  if (!uiConfig && !configError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--color-paper)] text-sm text-[var(--color-ink-soft)]">
        Loading…
      </div>
    )
  }

  if (configError || !uiConfig) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--color-paper)] px-4">
        <p className="rounded-xl border border-[var(--color-danger)]/20 bg-[var(--color-danger-soft)] px-4 py-3 text-sm text-[var(--color-danger)]">
          {configError ?? 'UI configuration unavailable'}
        </p>
      </div>
    )
  }

  const showDocuments = uiConfig.show_documents
  const showAbout = uiConfig.show_about

  return (
    <div className="flex h-full min-h-[100dvh] flex-col">
      <nav className="sticky top-0 z-40 border-b border-[var(--color-line)] bg-[var(--color-paper)]/85 backdrop-blur-sm">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex min-w-0 items-center gap-4 sm:gap-6">
            <a
              href={uiConfig.back_link}
              className="shrink-0 font-[family-name:var(--font-mono)] text-xs text-[var(--color-accent)] transition hover:text-[var(--color-accent-deep)]"
            >
              ← {uiConfig.back_label}
            </a>
            {showDocuments && (
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setTab('chat')}
                  className={`rounded-lg px-3 py-1.5 font-[family-name:var(--font-mono)] text-sm transition ${
                    tab === 'chat'
                      ? 'bg-[var(--color-ink)] text-[var(--color-accent-bright)]'
                      : 'text-[var(--color-ink-soft)] hover:bg-[var(--color-paper-2)] hover:text-[var(--color-ink)]'
                  }`}
                >
                  Chat
                </button>
                <button
                  type="button"
                  onClick={() => setTab('documents')}
                  className={`rounded-lg px-3 py-1.5 font-[family-name:var(--font-mono)] text-sm transition ${
                    tab === 'documents'
                      ? 'bg-[var(--color-ink)] text-[var(--color-accent-bright)]'
                      : 'text-[var(--color-ink-soft)] hover:bg-[var(--color-paper-2)] hover:text-[var(--color-ink)]'
                  }`}
                >
                  Documents
                </button>
              </div>
            )}
          </div>
          {showAbout && (
            <button
              type="button"
              onClick={() => setAboutOpen(true)}
              className="shrink-0 rounded-lg border border-[var(--color-line)] bg-[var(--color-panel)] px-3 py-1.5 font-[family-name:var(--font-mono)] text-xs text-[var(--color-ink-soft)] transition hover:border-[var(--color-accent)] hover:text-[var(--color-accent-deep)]"
            >
              About
            </button>
          )}
        </div>
      </nav>
      <AboutPanel open={aboutOpen} onClose={() => setAboutOpen(false)} />
      <main className="min-h-0 flex-1">
        {tab === 'chat' || !showDocuments ? (
          <ChatPage state={chatState} dispatch={chatDispatch} uiConfig={uiConfig} />
        ) : (
          <DocumentsPage />
        )}
      </main>
    </div>
  )
}
