import { useReducer, useState } from 'react'
import { ChatPage } from './pages/ChatPage'
import { DocumentsPage } from './pages/DocumentsPage'
import type { ChatAction, ChatState } from './types'

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
  const [chatState, chatDispatch] = useReducer(chatReducer, initialChatState)

  return (
    <div className="flex h-full min-h-screen flex-col">
      <nav className="border-b border-[var(--color-line)] bg-[var(--color-ink)] text-white">
        <div className="mx-auto flex max-w-5xl items-center gap-1 px-4 py-2 sm:px-6">
          <button
            type="button"
            onClick={() => setTab('chat')}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
              tab === 'chat' ? 'bg-white/15' : 'hover:bg-white/10'
            }`}
          >
            Chat
          </button>
          <button
            type="button"
            onClick={() => setTab('documents')}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
              tab === 'documents' ? 'bg-white/15' : 'hover:bg-white/10'
            }`}
          >
            Documents
          </button>
        </div>
      </nav>
      <main className="min-h-0 flex-1">
        {tab === 'chat' ? (
          <ChatPage state={chatState} dispatch={chatDispatch} />
        ) : (
          <DocumentsPage />
        )}
      </main>
    </div>
  )
}
