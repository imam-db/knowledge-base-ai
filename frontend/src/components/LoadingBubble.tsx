export function LoadingBubble() {
  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] rounded-2xl rounded-bl-md border border-[var(--color-line)] bg-white px-4 py-3 shadow-sm">
        <div className="flex items-center gap-2 text-sm text-[var(--color-ink-soft)]">
          <span className="font-medium">Thinking</span>
          <span className="inline-flex gap-1">
            <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-[var(--color-accent)]" />
            <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-[var(--color-accent)]" />
            <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-[var(--color-accent)]" />
          </span>
        </div>
      </div>
    </div>
  )
}
