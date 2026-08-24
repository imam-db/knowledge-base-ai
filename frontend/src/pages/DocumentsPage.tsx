import { useCallback, useEffect, useState } from 'react'
import { DocumentList } from '../components/DocumentList'
import { DocumentUpload } from '../components/DocumentUpload'
import { deleteDocument, getDocuments, uploadDocument } from '../services/api'
import type { DocumentInfo } from '../types'

export function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [listError, setListError] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const refreshDocuments = useCallback(async () => {
    const res = await getDocuments()
    setDocuments(res.documents)
    setListError(null)
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await getDocuments()
        if (!cancelled) {
          setDocuments(res.documents)
          setListError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setListError(err instanceof Error ? err.message : 'Failed to load documents')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const handleUpload = async (file: File) => {
    setUploading(true)
    setUploadError(null)
    setDeleteError(null)
    setSuccess(null)
    try {
      const result = await uploadDocument(file)
      await refreshDocuments()
      setSuccess(
        `Uploaded ${result.document_name} (${result.chunks_created} chunks).`,
      )
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (documentId: string) => {
    setDeletingId(documentId)
    setDeleteError(null)
    setSuccess(null)
    try {
      const result = await deleteDocument(documentId)
      await refreshDocuments()
      setSuccess(`Deleted ${result.document_name} (${result.chunks_deleted} chunks).`)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Delete failed')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <div className="mb-5">
        <h1 className="font-[family-name:var(--font-display)] text-2xl text-[var(--color-ink)]">
          Documents
        </h1>
        <p className="mt-1 font-[family-name:var(--font-mono)] text-sm text-[var(--color-ink-soft)]">
          Documents indexed in the knowledge base.
        </p>
      </div>

      <div className="mb-5 space-y-3">
        <DocumentUpload uploading={uploading} onUpload={(file) => void handleUpload(file)} />
        {success && (
          <div className="rounded-xl border border-[var(--color-accent)]/20 bg-[var(--color-accent-soft)] px-4 py-3 text-sm text-[var(--color-accent-deep)]">
            {success}
          </div>
        )}
        {uploadError && (
          <div className="rounded-xl border border-[var(--color-danger)]/20 bg-[var(--color-danger-soft)] px-4 py-3 text-sm text-[var(--color-danger)]">
            {uploadError}
          </div>
        )}
        {deleteError && (
          <div className="rounded-xl border border-[var(--color-danger)]/20 bg-[var(--color-danger-soft)] px-4 py-3 text-sm text-[var(--color-danger)]">
            {deleteError}
          </div>
        )}
      </div>

      <DocumentList
        documents={documents}
        loading={loading}
        error={listError}
        deletingId={deletingId}
        onDelete={(id) => void handleDelete(id)}
      />
    </div>
  )
}
