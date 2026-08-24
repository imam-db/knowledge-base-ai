import type { StatsResponse } from '../types'

type Props = {
  stats: StatsResponse | null
}

export function StatsPanel({ stats }: Props) {
  return (
    <div className="inline-flex items-center gap-3 rounded-full border border-[var(--color-line)] bg-[var(--color-panel)]/80 px-3 py-1 font-[family-name:var(--font-mono)] text-xs text-[var(--color-ink-soft)]">
      <span>
        <strong className="text-[var(--color-ink)]">{stats?.documents ?? '—'}</strong> docs
      </span>
      <span className="h-3 w-px bg-[var(--color-line)]" />
      <span>
        <strong className="text-[var(--color-ink)]">{stats?.chunks ?? '—'}</strong> chunks
      </span>
    </div>
  )
}
