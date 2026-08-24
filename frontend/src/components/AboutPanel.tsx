import { useEffect, useState } from 'react'
import { getAbout } from '../services/api'
import type { AboutResponse } from '../types'

type Props = {
  open: boolean
  onClose: () => void
}

function pct(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function AboutPanel({ open, onClose }: Props) {
  const [about, setAbout] = useState<AboutResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    let cancelled = false
    setLoading(true)
    setError(null)
    ;(async () => {
      try {
        const data = await getAbout()
        if (!cancelled) setAbout(data)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load about')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        aria-label="Close about panel"
        className="absolute inset-0 bg-[var(--color-ink)]/25 backdrop-blur-[2px]"
        onClick={onClose}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="about-title"
        className="relative flex h-full w-full max-w-lg flex-col border-l border-[var(--color-line)] bg-[var(--color-panel)] shadow-xl"
      >
        <header className="flex shrink-0 items-start justify-between gap-4 border-b border-[var(--color-line)] px-5 py-4">
          <div>
            <p className="font-[family-name:var(--font-mono)] text-xs uppercase tracking-wide text-[var(--color-accent)]">
              How it works
            </p>
            <h2
              id="about-title"
              className="mt-1 font-[family-name:var(--font-display)] text-xl text-[var(--color-ink)]"
            >
              {about?.title ?? 'About this demo'}
            </h2>
            {about?.tagline && (
              <p className="mt-1 text-sm text-[var(--color-ink-soft)]">{about.tagline}</p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 font-[family-name:var(--font-mono)] text-sm text-[var(--color-ink-soft)] transition hover:bg-[var(--color-paper-2)] hover:text-[var(--color-ink)]"
          >
            Close
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
          {loading && (
            <p className="text-sm text-[var(--color-ink-soft)]">Loading…</p>
          )}
          {error && (
            <p className="rounded-lg border border-[var(--color-danger)]/20 bg-[var(--color-danger-soft)] px-3 py-2 text-sm text-[var(--color-danger)]">
              {error}
            </p>
          )}
          {about?.show && !loading && !error && (() => {
            const pipeline = about.pipeline ?? []
            const guardrails = about.guardrails ?? []
            const tradeoffs = about.tradeoffs ?? []
            return (
            <div className="space-y-8">
              {about.stats && (
                <section>
                  <h3 className="font-[family-name:var(--font-mono)] text-xs uppercase tracking-wide text-[var(--color-ink-soft)]">
                    Live index
                  </h3>
                  <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
                    <StatCard label="Documents" value={String(about.stats.documents)} />
                    <StatCard label="Chunks" value={about.stats.chunks.toLocaleString()} />
                    <StatCard label="Top-K" value={String(about.stats.top_k)} />
                    <StatCard label="Chunk size" value={`${about.stats.chunk_size} chars`} />
                    <StatCard
                      label="Hybrid"
                      value={about.stats.hybrid_enabled ? 'On' : 'Off'}
                    />
                    <StatCard
                      label="LLM"
                      value={about.stats.llm_model.split('/').pop() ?? about.stats.llm_model}
                      mono
                    />
                  </div>
                  <p className="mt-2 font-[family-name:var(--font-mono)] text-[10px] leading-relaxed text-[var(--color-ink-soft)]">
                    Embedding: {about.stats.embedding_model}
                  </p>
                </section>
              )}

              {pipeline.length > 0 && (
                <section>
                  <h3 className="font-[family-name:var(--font-mono)] text-xs uppercase tracking-wide text-[var(--color-ink-soft)]">
                    Pipeline
                  </h3>
                  <ol className="mt-3 space-y-3">
                    {pipeline.map((step, index) => (
                      <li
                        key={step.label}
                        className="relative rounded-xl border border-[var(--color-line)] bg-[var(--color-paper)]/60 px-4 py-3"
                      >
                        <span className="font-[family-name:var(--font-mono)] text-[10px] text-[var(--color-accent)]">
                          {String(index + 1).padStart(2, '0')}
                        </span>
                        <p className="mt-0.5 font-medium text-[var(--color-ink)]">{step.label}</p>
                        <p className="mt-1 text-sm leading-relaxed text-[var(--color-ink-soft)]">
                          {step.detail}
                        </p>
                      </li>
                    ))}
                  </ol>
                </section>
              )}

              {about.problem && (
                <Section title="Why RAG" body={about.problem} />
              )}
              {about.approach && (
                <Section title="How it answers" body={about.approach} />
              )}

              {guardrails.length > 0 && (
                <BulletSection title="Guardrails" items={guardrails} />
              )}

              {about.eval && (
                <section>
                  <h3 className="font-[family-name:var(--font-mono)] text-xs uppercase tracking-wide text-[var(--color-ink-soft)]">
                    Retrieval eval
                  </h3>
                  <div className="mt-3 rounded-xl border border-[var(--color-accent)]/25 bg-[var(--color-accent-soft)]/50 px-4 py-3">
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                      <EvalMetric label="Hit@5" value={pct(about.eval.hit_at_5)} />
                      {about.eval.mrr != null && (
                        <EvalMetric label="MRR" value={about.eval.mrr.toFixed(3)} />
                      )}
                      {about.eval.unanswerable_empty_rate != null && (
                        <EvalMetric
                          label="Unanswerable guard"
                          value={pct(about.eval.unanswerable_empty_rate)}
                        />
                      )}
                    </div>
                    <p className="mt-3 text-xs text-[var(--color-ink-soft)]">
                      {about.eval.questions} gold questions · {about.eval.dataset}
                      {about.eval.note ? ` · ${about.eval.note}` : ''}
                    </p>
                  </div>
                </section>
              )}

              {tradeoffs.length > 0 && (
                <BulletSection title="Trade-offs & limits" items={tradeoffs} />
              )}
            </div>
            )
          })()}
        </div>
      </aside>
    </div>
  )
}

function Section({ title, body }: { title: string; body: string }) {
  return (
    <section>
      <h3 className="font-[family-name:var(--font-mono)] text-xs uppercase tracking-wide text-[var(--color-ink-soft)]">
        {title}
      </h3>
      <p className="mt-2 text-sm leading-relaxed text-[var(--color-ink)]">{body}</p>
    </section>
  )
}

function BulletSection({ title, items }: { title: string; items: string[] }) {
  return (
    <section>
      <h3 className="font-[family-name:var(--font-mono)] text-xs uppercase tracking-wide text-[var(--color-ink-soft)]">
        {title}
      </h3>
      <ul className="mt-2 space-y-2">
        {items.map((item) => (
          <li
            key={item}
            className="flex gap-2 text-sm leading-relaxed text-[var(--color-ink)]"
          >
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-accent)]" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

function StatCard({
  label,
  value,
  mono = false,
}: {
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div className="rounded-lg border border-[var(--color-line)] bg-[var(--color-panel)] px-3 py-2">
      <p className="font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-wide text-[var(--color-ink-soft)]">
        {label}
      </p>
      <p
        className={`mt-0.5 text-sm font-medium text-[var(--color-ink)] ${
          mono ? 'font-[family-name:var(--font-mono)] text-xs' : ''
        }`}
      >
        {value}
      </p>
    </div>
  )
}

function EvalMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-wide text-[var(--color-ink-soft)]">
        {label}
      </p>
      <p className="mt-0.5 font-[family-name:var(--font-display)] text-lg text-[var(--color-accent-deep)]">
        {value}
      </p>
    </div>
  )
}
