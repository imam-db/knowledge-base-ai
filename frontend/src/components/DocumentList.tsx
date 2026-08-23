import type { DocumentInfo } from '../types'

type Props = {
  documents: DocumentInfo[]
  loading: boolean
  error: string | null
  deletingId?: string | null
  onDelete: (documentId: string) => void
}

export function DocumentList({ documents, loading, error, deletingId, onDelete }: Props) {
  if (loading) {
    return <p className="text-sm text-[var(--color-ink-soft)]">Memuat dokumen…</p>
  }

  if (error) {
    return (
      <div className="rounded-xl border border-[var(--color-danger)]/20 bg-[var(--color-danger-soft)] px-4 py-3 text-sm text-[var(--color-danger)]">
        {error}
      </div>
    )
  }

  if (!documents.length) {
    return (
      <p className="rounded-xl border border-dashed border-[var(--color-line)] bg-white/70 px-4 py-6 text-sm text-[var(--color-ink-soft)]">
        Belum ada dokumen ter-index. Jalankan ingest dulu.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-[var(--color-line)] bg-white shadow-sm">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-[var(--color-paper)] text-xs uppercase tracking-wide text-[var(--color-ink-soft)]">
          <tr>
            <th className="px-4 py-3 font-semibold">Document</th>
            <th className="px-4 py-3 font-semibold">Pages</th>
            <th className="px-4 py-3 font-semibold">Uploaded</th>
            <th className="px-4 py-3 font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.document_id} className="border-t border-[var(--color-line)]">
              <td className="px-4 py-3 font-medium text-[var(--color-ink)]">{doc.name}</td>
              <td className="px-4 py-3 text-[var(--color-ink-soft)]">{doc.pages}</td>
              <td className="px-4 py-3 text-[var(--color-ink-soft)]">{doc.uploaded_at || '—'}</td>
              <td className="px-4 py-3">
                <button
                  type="button"
                  disabled={deletingId === doc.document_id}
                  onClick={() => {
                    if (!window.confirm(`Hapus ${doc.name}? Chunk dan file akan dihapus.`)) return
                    onDelete(doc.document_id)
                  }}
                  className="text-sm font-medium text-[var(--color-danger)] transition hover:text-[var(--color-danger)]/80 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {deletingId === doc.document_id ? 'Menghapus…' : 'Hapus'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
