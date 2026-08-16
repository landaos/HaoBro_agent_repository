import { useEffect, useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { useTranslation } from 'react-i18next'
import { X, Loader2, AlertCircle, FileText, RefreshCw } from 'lucide-react'
import { knowledgeApi } from '../../api/knowledge'
import type { KnowledgeDocumentDetail } from '../../types/api'

interface DocumentDetailDrawerProps {
  kbId: number
  docId: number | null
  onClose: () => void
}

type Tab = 'content' | 'metadata'

export default function DocumentDetailDrawer({
  kbId,
  docId,
  onClose,
}: DocumentDetailDrawerProps) {
  const { t } = useTranslation()
  const [tab, setTab] = useState<Tab>('content')
  const [detail, setDetail] = useState<KnowledgeDocumentDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!docId) {
      setDetail(null)
      return
    }
    setLoading(true)
    setError(false)
    setTab('content')
    knowledgeApi
      .detail(kbId, docId)
      .then(setDetail)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [kbId, docId])

  const handleReprocess = async () => {
    if (!docId) return
    try {
      await knowledgeApi.reprocess(kbId, docId)
      // 重新加载详情
      const updated = await knowledgeApi.detail(kbId, docId)
      setDetail(updated)
    } catch {
      // ignore
    }
  }

  return (
    <Dialog.Root open={!!docId} onOpenChange={(open) => { if (!open) onClose() }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 z-40" />
        <Dialog.Content className="fixed top-0 right-0 h-full w-[640px] max-w-[90vw] bg-[var(--color-card)] shadow-xl flex flex-col z-50">
          {/* 标题栏 */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)] shrink-0">
            <Dialog.Title className="text-base font-medium text-[var(--color-text)] truncate flex items-center gap-2">
              <FileText size={16} className="text-[var(--color-text-tertiary)] shrink-0" />
              {detail?.file_name || `文档 #${docId}`}
            </Dialog.Title>
            <div className="flex items-center gap-1">
              {detail?.status !== 'completed' && (
                <button
                  onClick={handleReprocess}
                  className="p-1.5 rounded text-[var(--color-text-tertiary)] hover:text-[var(--color-accent)] hover:bg-[var(--color-accent-bg)] transition-colors cursor-pointer"
                  title={t('knowledge.reprocess')}
                >
                  <RefreshCw size={16} />
                </button>
              )}
              <Dialog.Close className="p-1.5 rounded text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg-secondary)] transition-colors">
                <X size={18} />
              </Dialog.Close>
            </div>
          </div>

          {/* Tab 切换 */}
          <div className="flex border-b border-[var(--color-border)] px-6 shrink-0">
            <button
              onClick={() => setTab('content')}
              className="px-4 py-3 text-sm border-b-2 transition-colors cursor-pointer"
              style={{
                borderColor: tab === 'content' ? 'var(--color-accent)' : 'transparent',
                color: tab === 'content' ? 'var(--color-accent)' : 'var(--color-text-secondary)',
              }}
            >
              {t('knowledge.detail')}
            </button>
            <button
              onClick={() => setTab('metadata')}
              className="px-4 py-3 text-sm border-b-2 transition-colors cursor-pointer"
              style={{
                borderColor: tab === 'metadata' ? 'var(--color-accent)' : 'transparent',
                color: tab === 'metadata' ? 'var(--color-accent)' : 'var(--color-text-secondary)',
              }}
            >
              元数据
            </button>
          </div>

          {/* 内容区 */}
          <div className="flex-1 overflow-y-auto p-6">
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 size={24} className="animate-spin text-[var(--color-text-tertiary)]" />
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center py-20 text-[var(--color-text-tertiary)] gap-2">
                <AlertCircle size={20} />
                <span className="text-sm">{t('common.error')}</span>
              </div>
            ) : !detail ? null : tab === 'content' ? (
              /* 文档内容 */
              <div>
                {/* 摘要信息 */}
                <div className="grid grid-cols-2 gap-3 mb-6 p-4 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)] text-sm">
                  <div>
                    <span className="text-[var(--color-text-tertiary)]">{t('knowledge.title')}: </span>
                    <span className="text-[var(--color-text)]">{detail.file_name}</span>
                  </div>
                  <div>
                    <span className="text-[var(--color-text-tertiary)]">类型: </span>
                    <span className="text-[var(--color-text)]">{detail.file_type}</span>
                  </div>
                  <div>
                    <span className="text-[var(--color-text-tertiary)]">{t('knowledge.chunks')}: </span>
                    <span className="text-[var(--color-text)]">{detail.chunk_count}</span>
                  </div>
                  <div>
                    <span className="text-[var(--color-text-tertiary)]">状态: </span>
                    <span className="text-[var(--color-text)]">
                      {t(`knowledge.status_${detail.status}` as any)}
                    </span>
                  </div>
                  {detail.error_message && (
                    <div className="col-span-2">
                      <span className="text-[var(--color-danger)]">
                        错误: {detail.error_message}
                      </span>
                    </div>
                  )}
                </div>

                {/* 文档内容渲染（Markdown 文本预览） */}
                {detail.content ? (
                  <pre className="text-sm text-[var(--color-text)] whitespace-pre-wrap font-sans leading-relaxed bg-[var(--color-bg-secondary)] p-4 rounded-lg border border-[var(--color-border)]">
                    {detail.content.slice(0, 5000)}
                    {detail.content.length > 5000 && '...'}
                  </pre>
                ) : (
                  <p className="text-sm text-[var(--color-text-tertiary)] italic">
                    暂无内容
                  </p>
                )}
              </div>
            ) : (
              /* 元数据 */
              <div>
                <h3 className="text-sm font-medium text-[var(--color-text)] mb-3">文档元数据</h3>
                {detail.metadata && Object.keys(detail.metadata).length > 0 ? (
                  <div className="space-y-2">
                    {Object.entries(detail.metadata).map(([key, val]) => (
                      <div
                        key={key}
                        className="flex items-start gap-2 py-2 border-b border-[var(--color-border)] last:border-0"
                      >
                        <span className="text-xs font-medium text-[var(--color-text-secondary)] min-w-[100px] shrink-0">
                          {key}
                        </span>
                        <span className="text-xs text-[var(--color-text)] break-all font-mono">
                          {typeof val === 'object' ? JSON.stringify(val, null, 2) : String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-[var(--color-text-tertiary)] italic">
                    {t('knowledge.noMetadata')}
                  </p>
                )}
              </div>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
