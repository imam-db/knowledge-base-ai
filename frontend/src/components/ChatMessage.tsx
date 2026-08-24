import type { AnswerStatus, ChatMessageItem } from '../types'
import { SourceBadge } from './SourceBadge'

type Props = {
  message: ChatMessageItem
}

function statusLabel(status?: AnswerStatus): string | null {
  if (status === 'not_found') return 'Not found'
  if (status === 'error') return 'Error'
  if (status === 'answered') return 'Answered'
  return null
}

function statusClass(status?: AnswerStatus): string {
  if (status === 'not_found') {
    return 'bg-[var(--color-paper-2)] text-[var(--color-ink-soft)]'
  }
  if (status === 'error') {
    return 'bg-[var(--color-danger-soft)] text-[var(--color-danger)]'
  }
  return 'bg-[var(--color-accent-soft)] text-[var(--color-accent-deep)]'
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user'
  const label = !isUser ? statusLabel(message.status) : null

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm sm:max-w-[75%] ${
          isUser
            ? 'rounded-br-md bg-[var(--color-ink)] text-[#e8e8e8]'
            : 'rounded-bl-md border border-[var(--color-line)] bg-[var(--color-panel)] text-[var(--color-ink)]'
        }`}
      >
        {label && (
          <span
            className={`mb-2 inline-flex rounded-full px-2 py-0.5 font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-wide ${statusClass(message.status)}`}
          >
            {label}
          </span>
        )}
        <p className="whitespace-pre-wrap text-sm leading-relaxed">
          {message.content}
          {message.streaming && (
            <span className="ml-0.5 inline-block h-3 w-1 animate-pulse bg-[var(--color-accent)] align-middle" />
          )}
        </p>
        {!isUser && message.sources && message.sources.length > 0 && (
          <SourceBadge sources={message.sources} />
        )}
      </div>
    </div>
  )
}
