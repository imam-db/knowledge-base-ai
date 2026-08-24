import { useCallback, useRef, useState, type DragEvent } from 'react'

type Props = {
  uploading: boolean
  onUpload: (file: File) => void
}

const ACCEPT = '.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document'

export function DocumentUpload({ uploading, onUpload }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const pickFile = useCallback(
    (file: File | undefined | null) => {
      if (!file || uploading) return
      onUpload(file)
    },
    [onUpload, uploading],
  )

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragging(false)
    pickFile(event.dataTransfer.files?.[0])
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={`rounded-2xl border border-dashed px-4 py-6 transition ${
        dragging
          ? 'border-[var(--color-accent)] bg-[var(--color-accent-soft)]'
          : 'border-[var(--color-line)] bg-white/70'
      }`}
    >
      <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-[var(--color-ink)]">Upload document</p>
          <p className="mt-1 text-xs text-[var(--color-ink-soft)]">
            PDF or DOCX, max 20MB. Uploading the same filename replaces the previous document.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            className="hidden"
            disabled={uploading}
            onChange={(e) => {
              pickFile(e.target.files?.[0])
              e.target.value = ''
            }}
          />
          <button
            type="button"
            disabled={uploading}
            onClick={() => inputRef.current?.click()}
            className="rounded-xl bg-[var(--color-ink)] px-4 py-2 font-[family-name:var(--font-mono)] text-sm font-medium text-[var(--color-accent-bright)] transition hover:bg-[var(--color-accent-deep)] enabled:active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {uploading ? 'Processing…' : 'Choose file'}
          </button>
        </div>
      </div>
      {uploading && (
        <p className="mt-4 text-sm font-medium text-[var(--color-accent-deep)]">
          Processing document…
        </p>
      )}
    </div>
  )
}
