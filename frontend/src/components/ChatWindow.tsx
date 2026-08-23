import { useEffect, useRef } from 'react'
import type { ChatMessageItem } from '../types'
import { ChatMessage } from './ChatMessage'
import { LoadingBubble } from './LoadingBubble'

type Props = {
  messages: ChatMessageItem[]
  loading: boolean
}

export function ChatWindow({ messages, loading }: Props) {
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  return (
    <div className="flex-1 overflow-y-auto px-3 py-4 sm:px-6">
      <div className="mx-auto flex max-w-3xl flex-col gap-3">
        {messages.length === 0 && !loading && (
          <div className="rounded-2xl border border-dashed border-[var(--color-line)] bg-white/60 px-5 py-8 text-center">
            <h2 className="font-[family-name:var(--font-display)] text-xl text-[var(--color-ink)]">
              Tanya dokumen internal
            </h2>
            <p className="mt-2 text-sm text-[var(--color-ink-soft)]">
              Jawaban disusun hanya dari SOP, kebijakan, dan FAQ yang sudah di-index.
            </p>
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
