import { useEffect, useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import * as Dialog from '@radix-ui/react-dialog'
import { Upload, FileText, Trash2, Loader2, CheckCircle2, AlertCircle, RefreshCw, Search, Filter, Plus, BookOpen, ChevronDown } from 'lucide-react'
import { knowledgeApi } from '../api/knowledge'
import { useKnowledgeBaseStore } from '../stores/useKnowledgeBaseStore'
import type { KnowledgeDocument, DocumentStatus } from '../types/api'
import EmptyState from '../components/common/EmptyState'
import ConfirmDialog from '../components/common/ConfirmDialog'
import DocumentDetailDrawer from '../components/knowledge/DocumentDetailDrawer'

interface UploadFile {
  file: File
  status: 'pending' | 'uploading' | 'success' | 'fail'
  error?: string
}

const STATUS_BADGE: Record<DocumentStatus, { color: string; bg: string }> = {
  pending:    { color: 'var(--color-text-tertiary)', bg: 'var(--color-bg-tertiary)' },
  processing: { color: '#2563eb', bg: '#eff6ff' },
  completed:  { color: '#16a34a', bg: '#f0fdf4' },
  failed:     { color: '#dc2626', bg: '#fef2f2' },
}

export default function KnowledgeBase() {
  const { t } = useTranslation()

  const { list: kbList, selectedId, loading: kbLoading, fetchList, create, delete: deleteKB, setSelectedId } = useKnowledgeBaseStore()

  const [docs, setDocs] = useState<KnowledgeDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [refreshKey, setRefreshKey] = useState(0)
  const pageSize = 20

  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [deleteTarget, setDeleteTarget] = useState<KnowledgeDocument | null>(null)
  const [showDeleteKB, setShowDeleteKB] = useState(false)
  const [detailDocId, setDetailDocId] = useState<number | null>(null)

  const [showCreateKB, setShowCreateKB] = useState(false)
  const [newKBName, setNewKBName] = useState('')
  const [newKBDesc, setNewKBDesc] = useState('')
  const [creatingKB, setCreatingKB] = useState(false)

  const searchTimer = useRef<number | undefined>(undefined)

  useEffect(() => { fetchList() }, [fetchList])

  useEffect(() => {
    let cancelled = false
    if (!selectedId) { setDocs([]); setTotal(0); setLoading(false); return }
    setLoading(true)
    knowledgeApi.list(selectedId, { page, page_size: pageSize, status: statusFilter || undefined, search: search || undefined })
      .then((res) => { if (cancelled) return; setDocs(res.items); setTotal(res.total) })
      .catch(() => { if (cancelled) return; toast.error(t('common.error')) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [selectedId, page, search, statusFilter, refreshKey, t])

  const handleSearchChange = (val: string) => { setSearch(val); clearTimeout(searchTimer.current); searchTimer.current = setTimeout(() => setPage(1), 400) }

  const handleFilesSelected = async (files: FileList) => {
    if (!selectedId) { toast.error(t('knowledge.noKBForChat')); return }
    const fileList = Array.from(files).filter((f) => {
      const ext = f.name.split('.').pop()?.toLowerCase()
      if (!ext || !['pdf', 'txt', 'md', 'docx', 'pptx', 'csv', 'xlsx', 'xls'].includes(ext)) { toast.error(`${t('knowledge.notSupported')}: ${f.name}`); return false }
      if (f.size > 200 * 1024 * 1024) { toast.error(`${t('knowledge.tooLarge')}: ${f.name} (${t('knowledge.over200MB')})`); return false }
      return true
    })
    if (fileList.length === 0) return

    const newFiles: UploadFile[] = fileList.map((f) => ({ file: f, status: 'pending' as const }))
    setUploadFiles(newFiles)
    setUploading(true)
    try {
      setUploadFiles(newFiles.map((f) => ({ ...f, status: 'uploading' as const })))
      const results: Array<{ file: File; status: 'success' | 'fail'; error?: string }> = []
      for (let i = 0; i < fileList.length; i += 10) {
        const batch = fileList.slice(i, i + 10)
        const res = await knowledgeApi.batchUpload(selectedId, batch)
        const failedSet = new Set(res.errors.map((e) => e.filename))
        const failMap = new Map(res.errors.map((e) => [e.filename, e.error]))
        for (const f of batch) { results.push({ file: f, status: failedSet.has(f.name) ? 'fail' : 'success', error: failMap.get(f.name) }) }
      }
      setUploadFiles(results.map((r) => ({ file: r.file, status: r.status, error: r.error })))
    } catch (e: any) {
      setUploadFiles(newFiles.map((f) => ({ ...f, status: 'fail' as const, error: e?.response?.data?.detail || e?.message || t('knowledge.uploadFailed') })))
    }
    setUploading(false)
    setRefreshKey((k) => k + 1)
    setTimeout(() => setUploadFiles([]), 10_000)
  }

  const dismissUploadResult = (index: number) => { setUploadFiles((prev) => prev.filter((_, i) => i !== index)) }

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragOver(true) }
  const handleDragLeave = () => setDragOver(false)
  const handleDrop = (e: React.DragEvent) => { e.preventDefault(); setDragOver(false); if (e.dataTransfer.files.length > 0) handleFilesSelected(e.dataTransfer.files) }

  const handleDeleteDoc = async () => {
    if (!deleteTarget || !selectedId) return
    try { const res = await knowledgeApi.deleteById(selectedId, deleteTarget.id); toast.success(res.message); setDocs((prev) => prev.filter((d) => d.id !== deleteTarget.id)); setTotal((t) => t - 1) }
    catch { toast.error(t('common.error')) }
    setDeleteTarget(null)
  }

  const handleCreateKB = async () => {
    if (!newKBName.trim()) return; setCreatingKB(true)
    try { await create(newKBName.trim(), newKBDesc.trim() || undefined); toast.success(t('knowledge.createSuccess')); setShowCreateKB(false); setNewKBName(''); setNewKBDesc('') }
    catch { toast.error(t('knowledge.createFailed')) }
    finally { setCreatingKB(false) }
  }

  const handleDeleteKB = async () => {
    if (!selectedId) return
    try { await deleteKB(selectedId); toast.success(t('knowledge.deleteKBSuccess')); setShowDeleteKB(false) }
    catch { toast.error(t('knowledge.deleteKBFailed')) }
  }

  const formatSize = (bytes: number | null) => {
    if (!bytes) return '-'; if (bytes < 1024) return `${bytes}B`; if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`; return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
  }
  const formatDate = (dateStr: string) => new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })

  const selectedKB = kbList.find((k) => k.id === selectedId)

  return (
    <div className="max-w-5xl mx-auto py-8 px-6">
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <BookOpen size={20} className="text-[var(--color-accent)] shrink-0" />
        <h1 className="font-heading text-xl font-semibold text-[var(--color-text)] mr-2">{t('knowledge.title')}</h1>

        <div className="relative flex-1 min-w-[200px] max-w-xs">
          {kbLoading ? (
            <Loader2 size={16} className="animate-spin text-[var(--color-text-tertiary)]" />
          ) : kbList.length === 0 ? (
            <span className="text-sm text-[var(--color-text-tertiary)]">{t('knowledge.noKB')}</span>
          ) : (
            <select value={selectedId ?? ''} onChange={(e) => setSelectedId(Number(e.target.value))}
              className="w-full px-3 py-2 text-sm rounded-md border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-text)] outline-none appearance-none focus:border-[var(--color-accent)] transition-colors cursor-pointer">
              {kbList.map((kb) => (<option key={kb.id} value={kb.id}>{kb.name} ({kb.document_count} {t('common.documents')})</option>))}
            </select>
          )}
          <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-tertiary)] pointer-events-none" />
        </div>

        <button onClick={() => setShowCreateKB(true)} className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-md bg-[var(--color-accent)] text-white hover:opacity-90 transition-colors cursor-pointer shrink-0">
          <Plus size={14} />{t('knowledge.createKB')}
        </button>

        {selectedKB && (
          <button onClick={() => setShowDeleteKB(true)} className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-md border border-[var(--color-border)] text-[var(--color-danger)] hover:bg-[var(--color-danger-bg)] transition-colors cursor-pointer shrink-0">
            <Trash2 size={14} />{t('knowledge.deleteKB')}
          </button>
        )}
      </div>

      {selectedKB?.description && <p className="text-xs text-[var(--color-text-tertiary)] mb-4 -mt-3">{selectedKB.description}</p>}

      {selectedId ? (
        <>
          <div onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-lg p-10 text-center transition-colors ${dragOver ? 'border-[var(--color-accent)] bg-[var(--color-accent-bg)]' : 'border-[var(--color-border)] hover:border-[var(--color-text-tertiary)]'}`}>
            <input ref={fileInputRef} id="kb-file-upload" type="file" multiple accept=".pdf,.docx,.pptx,.txt,.md,.csv,.xlsx,.xls" className="hidden"
              onChange={(e) => { if (e.target.files) handleFilesSelected(e.target.files); e.target.value = '' }} />
            <Upload size={24} className="mx-auto mb-3 text-[var(--color-text-tertiary)]" />
            <p className="text-sm text-[var(--color-text-secondary)] mb-1">{t('knowledge.dragDrop')}</p>
            <p className="text-xs text-[var(--color-text-tertiary)] mb-4">{t('knowledge.fileTypes')}</p>
            <label htmlFor="kb-file-upload" className="inline-block px-4 py-2 text-sm rounded-md bg-[var(--color-accent)] text-white hover:opacity-90 transition-colors cursor-pointer">
              {t('knowledge.upload')}
            </label>
          </div>

          {uploadFiles.length > 0 && (
            <div className="mt-4 space-y-2">
              {uploadFiles.map((uf, i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-3 rounded-lg bg-[var(--color-card)] border border-[var(--color-border)]">
                  {uf.status === 'success' ? <CheckCircle2 size={16} className="text-[var(--color-success)] shrink-0" />
                    : uf.status === 'fail' ? <AlertCircle size={16} className="text-[var(--color-danger)] shrink-0" />
                    : <Loader2 size={16} className="animate-spin text-[var(--color-accent)] shrink-0" />}
                  <span className="text-sm text-[var(--color-text)] flex-1 truncate">{uf.file.name}</span>
                  <span className="text-xs text-[var(--color-text-tertiary)]">{formatSize(uf.file.size)}</span>
                  {uf.status === 'fail' && uf.error && <span className="text-xs text-[var(--color-danger)] max-w-[200px] truncate" title={uf.error}>{uf.error}</span>}
                  {uf.status !== 'pending' && uf.status !== 'uploading' && (
                    <button onClick={() => dismissUploadResult(i)} className="p-0.5 rounded text-[var(--color-text-tertiary)] hover:text-[var(--color-danger)] hover:bg-[var(--color-danger-bg)] transition-colors shrink-0 cursor-pointer" title={t('common.close')}>
                      <span className="text-xs font-bold">&times;</span>
                    </button>
                  )}
                </div>
              ))}
              {!uploading && uploadFiles.every((f) => f.status === 'success') && <p className="text-xs text-[var(--color-success)] text-center">{t('knowledge.success')}</p>}
            </div>
          )}

          <div className="mt-8 flex items-center gap-3">
            <div className="relative flex-1">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-tertiary)]" />
              <input type="text" value={search} onChange={(e) => handleSearchChange(e.target.value)} placeholder={t('knowledge.searchPlaceholder')}
                className="w-full pl-9 pr-4 py-2 text-sm rounded-md border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-text)] outline-none focus:border-[var(--color-accent)] transition-colors" />
            </div>
            <div className="relative">
              <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-tertiary)]" />
              <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
                className="pl-9 pr-8 py-2 text-sm rounded-md border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-text)] outline-none appearance-none focus:border-[var(--color-accent)] transition-colors">
                <option value="">{t('knowledge.allStatus')}</option>
                <option value="completed">{t('knowledge.status_completed')}</option>
                <option value="processing">{t('knowledge.status_processing')}</option>
                <option value="failed">{t('knowledge.status_failed')}</option>
                <option value="pending">{t('knowledge.status_pending')}</option>
              </select>
            </div>
          </div>

          <div className="mt-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium text-[var(--color-text)]">
                {t('knowledge.documentList')}
                <span className="text-[var(--color-text-tertiary)] ml-1">({t('knowledge.total')} {total} {t('knowledge.items')})</span>
              </h2>
              <button onClick={() => setRefreshKey((k) => k + 1)} className="p-1.5 rounded bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg-tertiary)] transition-colors" title={t('common.retry')}>
                <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              </button>
            </div>

            {loading ? (
              <div className="space-y-3">{[1, 2, 3, 4].map((i) => (<div key={i} className="h-16 bg-[var(--color-bg-tertiary)] rounded-lg animate-pulse" />))}</div>
            ) : docs.length === 0 ? (
              <EmptyState icon={<FileText size={48} />} message={search || statusFilter ? t('knowledge.noMatch') : t('knowledge.empty')} />
            ) : (
              <>
                <div className="space-y-2">
                  {docs.map((doc) => (
                    <div key={doc.id} onClick={() => setDetailDocId(doc.id)}
                      className="flex items-center justify-between px-4 py-3 rounded-lg bg-[var(--color-card)] border border-[var(--color-border)] hover:border-[var(--color-accent)] cursor-pointer transition-colors">
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <FileText size={16} className="text-[var(--color-text-tertiary)] shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm text-[var(--color-text)] truncate">{doc.file_name}</p>
                          <div className="flex items-center gap-2 text-xs text-[var(--color-text-tertiary)] mt-0.5">
                            <span>{formatSize(doc.file_size)}</span><span>|</span><span>{doc.chunk_count} chunks</span><span>|</span><span>{formatDate(doc.created_at)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 ml-3">
                        <span className="px-2 py-0.5 rounded text-xs font-medium" style={{ color: STATUS_BADGE[doc.status]?.color, backgroundColor: STATUS_BADGE[doc.status]?.bg }}>
                          {t(`knowledge.status_${doc.status}` as any)}
                        </span>
                        <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(doc) }}
                          className="p-1.5 rounded text-[var(--color-text-tertiary)] hover:text-[var(--color-danger)] hover:bg-[var(--color-danger-bg)] transition-colors cursor-pointer">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {total > pageSize && (
                  <div className="flex items-center justify-center gap-2 mt-6">
                    <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}
                      className="px-3 py-1.5 text-sm rounded border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer">
                      {t('knowledge.prevPage')}
                    </button>
                    <span className="text-sm text-[var(--color-text-tertiary)]">{page} / {Math.ceil(total / pageSize)}</span>
                    <button disabled={page >= Math.ceil(total / pageSize)} onClick={() => setPage((p) => p + 1)}
                      className="px-3 py-1.5 text-sm rounded border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer">
                      {t('knowledge.nextPage')}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </>
      ) : (
        <EmptyState icon={<BookOpen size={48} />} message={t('knowledge.noKB')} action={
          <button onClick={() => setShowCreateKB(true)} className="px-4 py-2 text-sm rounded-md bg-[var(--color-accent)] text-white hover:opacity-90 transition-colors cursor-pointer">
            {t('knowledge.createFirst')}
          </button>
        } />
      )}

      <ConfirmDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)} title={t('common.confirm')} message={t('knowledge.deleteConfirm')} variant="danger" confirmText={t('common.delete')} onConfirm={handleDeleteDoc} />
      <ConfirmDialog open={showDeleteKB} onOpenChange={setShowDeleteKB} title={t('common.confirm')} message={t('knowledge.deleteKBConfirm')} variant="danger" confirmText={t('common.delete')} onConfirm={handleDeleteKB} />

      <DocumentDetailDrawer kbId={selectedId ?? 0} docId={detailDocId} onClose={() => setDetailDocId(null)} />

      <Dialog.Root open={showCreateKB} onOpenChange={setShowCreateKB}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/40 z-[100]" />
          <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] max-w-[90vw] bg-[var(--color-card)] rounded-xl shadow-xl p-6 z-[100]">
            <Dialog.Title className="text-base font-medium text-[var(--color-text)] mb-4">{t('knowledge.createKB')}</Dialog.Title>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">{t('knowledge.kbName')}</label>
                <input value={newKBName} onChange={(e) => setNewKBName(e.target.value)} placeholder={t('knowledge.kbNamePlaceholder')} autoFocus
                  className="w-full px-3 py-2 text-sm rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text)] outline-none focus:border-[var(--color-accent)] transition-colors" />
              </div>
              <div>
                <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">{t('knowledge.kbDescription')}</label>
                <textarea value={newKBDesc} onChange={(e) => setNewKBDesc(e.target.value)} placeholder={t('knowledge.kbDescriptionPlaceholder')} rows={3}
                  className="w-full px-3 py-2 text-sm rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text)] outline-none focus:border-[var(--color-accent)] transition-colors resize-none" />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => { setShowCreateKB(false); setNewKBName(''); setNewKBDesc('') }}
                className="px-4 py-2 text-sm rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] transition-colors cursor-pointer">
                {t('common.cancel')}
              </button>
              <button onClick={handleCreateKB} disabled={!newKBName.trim() || creatingKB}
                className="px-4 py-2 text-sm rounded-md bg-[var(--color-accent)] text-white hover:opacity-90 disabled:opacity-40 transition-colors cursor-pointer">
                {creatingKB ? <Loader2 size={14} className="animate-spin" /> : t('common.confirm')}
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  )
}