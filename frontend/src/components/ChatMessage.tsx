import type { ChatMessageItem } from '../types'
import { SourceBadge } from './SourceBadge'

type Props = {
  message: ChatMessageItem
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm sm:max-w-[75%] ${
          isUser
            ? 'rounded-br-md bg-[var(--color-accent)] text-white'
            : 'rounded-bl-md border border-[var(--color-line)] bg-white text-[var(--color-ink)]'
        }`}
      >
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className={!isUser ? 'text-[var(--color-ink)]' : ''}>
            <SourceBadge sources={message.sources} bestDistance={message.retrieval_metadata?.best_distance ?? null} />
          </div>
        )}
      </div>
    </div>
  )
}
