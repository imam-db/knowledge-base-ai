import type { Source } from '../types'
import { useState } from 'react'

type Props = {
  sources: Source[]
}

export function SourceBadge({ sources }: Props) {
  const [open, setOpen] = useState(false)
  const [showTech, setShowTech] = useState(false)

  if (!sources.length) return null

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-2 rounded-full border border-[var(--color-line)] bg-[var(--color-paper)] px-3 py-1 text-xs font-medium text-[var(--color-ink-soft)] transition hover:border-[var(--color-accent)] hover:text-[var(--color-accent-deep)] active:scale-[0.98]"
      >
        <span>Sources ({sources.length})</span>
        <span className="text-[10px] uppercase tracking-wide">{open ? 'Hide' : 'Show'}</span>
      </button>

      {open && (
        <div className="mt-2 space-y-2 rounded-xl border border-[var(--color-line)] bg-[var(--color-paper)]/80 p-3">
          {sources.map((source, index) => (
            <div
              key={`${source.document}-${source.page}-${index}`}
              className="rounded-lg bg-[var(--color-panel)] px-3 py-2 text-sm text-[var(--color-ink-soft)] shadow-sm"
            >
              <div className="font-medium text-[var(--color-ink)]">
                {source.document.replace(/\.pdf$/i, '')} · Page {source.page}
              </div>
              {source.snippet && (
                <p className="mt-1 text-xs leading-relaxed text-[var(--color-ink-soft)]">
                  “{source.snippet}”
                </p>
              )}
              {showTech && (
                <div className="mt-1 flex flex-wrap gap-3 text-[10px] uppercase tracking-wide">
                  {source.chunk_id != null && <span>chunk {source.chunk_id}</span>}
                  {source.distance != null && <span>distance {source.distance.toFixed(2)}</span>}
                </div>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={() => setShowTech((v) => !v)}
            className="text-[10px] uppercase tracking-wide text-[var(--color-ink-soft)] hover:text-[var(--color-accent-deep)]"
          >
            {showTech ? 'Hide technical details' : 'Technical details'}
          </button>
        </div>
      )}
    </div>
  )
}
