import type { FormEvent, KeyboardEvent } from 'react'

type Props = {
  value: string
  loading: boolean
  onChange: (value: string) => void
  onSubmit: () => void
}

export function ChatInput({ value, loading, onChange, onSubmit }: Props) {
  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!loading && value.trim()) onSubmit()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (!loading && value.trim()) onSubmit()
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-[var(--color-line)] bg-[var(--color-panel)]/90 p-3 sm:p-4"
    >
      <div className="mx-auto flex max-w-3xl flex-col gap-3 sm:flex-row sm:items-end">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          placeholder="Ask about rules, policies, or handbook topics…"
          className="min-h-[72px] w-full flex-1 resize-y rounded-2xl border border-[var(--color-line)] bg-[var(--color-paper)] px-4 py-3 text-sm outline-none transition focus:border-[var(--color-accent)] focus:ring-2 focus:ring-[var(--color-accent-bright)]/40 focus:bg-[var(--color-panel)]"
        />
        <button
          type="submit"
          disabled={loading || !value.trim()}
          className="rounded-2xl bg-[var(--color-ink)] px-5 py-3 font-[family-name:var(--font-mono)] text-sm font-medium text-[var(--color-accent-bright)] transition hover:bg-[var(--color-accent-deep)] enabled:active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </form>
  )
}
