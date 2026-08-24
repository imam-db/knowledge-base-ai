import type { HealthResponse } from '../types'

type Props = {
  health: HealthResponse | null
  loading: boolean
}

export function HealthIndicator({ health, loading }: Props) {
  if (loading) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-[var(--color-panel)]/80 px-3 py-1 font-[family-name:var(--font-mono)] text-xs font-medium text-[var(--color-ink-soft)]">
        Checking…
      </span>
    )
  }

  const ready =
    health?.status === 'healthy' &&
    health.embedding === 'loaded' &&
    health.vector_db === 'connected'

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 font-[family-name:var(--font-mono)] text-xs font-medium ${
        ready
          ? 'bg-[var(--color-accent-soft)] text-[var(--color-accent-deep)]'
          : 'bg-[var(--color-danger-soft)] text-[var(--color-danger)]'
      }`}
    >
      <span>{ready ? '🟢' : '🔴'}</span>
      <span>{ready ? 'System Ready' : 'API Offline'}</span>
    </span>
  )
}
