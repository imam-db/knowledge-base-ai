import { useEffect, useRef } from 'react'
import type { ChatMessageItem } from '../types'
import { ChatMessage } from './ChatMessage'
import { LoadingBubble } from './LoadingBubble'

type Props = {
  messages: ChatMessageItem[]
  loading: boolean
  emptyStateTitle: string
  emptyStateDescription: string
  exampleQuestions: string[]
  indexedDocuments: number | null
  onExampleSelect: (question: string) => void
}

export function ChatWindow({
  messages,
  loading,
  emptyStateTitle,
  emptyStateDescription,
  exampleQuestions,
  indexedDocuments,
  onExampleSelect,
}: Props) {
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  return (
    <div className="flex-1 overflow-y-auto px-3 py-4 sm:px-6">
      <div className="mx-auto flex max-w-3xl flex-col gap-3">
        {messages.length === 0 && !loading && (
          <div className="rounded-2xl border border-dashed border-[var(--color-line)] bg-[var(--color-paper)]/60 px-5 py-8 text-center">
            <h2 className="font-[family-name:var(--font-display)] text-xl text-[var(--color-ink)]">
              {emptyStateTitle}
            </h2>
            <p className="mt-2 text-sm text-[var(--color-ink-soft)]">{emptyStateDescription}</p>
            {indexedDocuments === 0 && (
              <p className="mt-3 text-xs text-[var(--color-danger)]">
                No documents indexed yet. Run ingest before the demo.
              </p>
            )}
            {exampleQuestions.length > 0 && (
              <div className="mt-6 flex flex-col gap-2">
                <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-ink-soft)]">
                  Example questions
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {exampleQuestions.map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => onExampleSelect(question)}
                      className="rounded-full border border-[var(--color-line)] bg-[var(--color-panel)] px-3 py-1.5 text-left text-xs text-[var(--color-ink-soft)] transition hover:border-[var(--color-accent)] hover:text-[var(--color-accent-deep)] active:scale-[0.98]"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {loading && <LoadingBubble />}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
