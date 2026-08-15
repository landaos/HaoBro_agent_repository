import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { Plus, MessageSquare, Trash2, Pencil } from 'lucide-react'
import { sessionsApi } from '../api/sessions'
import type { Conversation } from '../types/api'
import EmptyState from '../components/common/EmptyState'
import ConfirmDialog from '../components/common/ConfirmDialog'

export default function Sessions() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [sessions, setSessions] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Conversation | null>(null)
  // 编辑状态
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const editRef = useRef<HTMLInputElement>(null)

  const loadSessions = async () => {
    setLoading(true)
    try {
      const res = await sessionsApi.list()
      setSessions(res.data || [])
    } catch {
      toast.error('加载会话列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSessions()
  }, [])

  // 编辑框聚焦
  useEffect(() => {
    if (editingId) editRef.current?.focus()
  }, [editingId])

  // ── 开始编辑 ──
  const startEdit = (session: Conversation) => {
    setEditingId(session.session_id)
    setEditValue(session.title || '')
  }

  // ── 保存编辑 ──
  const saveEdit = async () => {
    if (!editingId) return
    const trimmed = editValue.trim()
    // 如果没变化或为空，直接取消编辑
    const original = sessions.find((s) => s.session_id === editingId)
    if (!trimmed || trimmed === original?.title) {
      setEditingId(null)
      return
    }
    try {
      const updated = await sessionsApi.update(editingId, { title: trimmed })
      setSessions((prev) => prev.map((s) => (s.session_id === editingId ? { ...s, ...updated } : s)))
    } catch {
      toast.error('修改标题失败')
    }
    setEditingId(null)
  }

  // ── 取消编辑 ──
  const cancelEdit = () => {
    setEditingId(null)
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await sessionsApi.delete(deleteTarget.session_id)
      setSessions((prev) => prev.filter((s) => s.session_id !== deleteTarget.session_id))
    } catch {
      toast.error('删除会话失败')
    }
    setDeleteTarget(null)
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    return d.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="max-w-3xl mx-auto py-8 px-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-heading text-xl font-semibold text-[var(--color-text)]">{t('sessions.title')}</h1>
        <button
          onClick={() => {
            navigate('/chat')
          }}
          className="flex items-center gap-2 px-4 py-2 rounded-md bg-[var(--color-accent)] text-white text-sm hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          {t('chat.newSession')}
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-[var(--color-bg-tertiary)] rounded-lg animate-pulse" />
          ))}
        </div>
      ) : sessions.length === 0 ? (
        <EmptyState
          icon={<MessageSquare size={48} />}
          message={t('sessions.empty')}
          action={
            <button
              onClick={() => navigate('/chat')}
              className="px-4 py-2 text-sm rounded-md bg-[var(--color-accent)] text-white"
            >
              {t('chat.newSession')}
            </button>
          }
        />
      ) : (
        <div className="space-y-2">
          {sessions.map((session) => (
            <div
              key={session.session_id}
              onClick={() => !editingId && navigate(`/chat/${session.session_id}`)}
              className="group flex items-center justify-between px-4 py-3 rounded-lg bg-[var(--color-card)] border border-[var(--color-border)] hover:border-[var(--color-accent)] cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <MessageSquare size={16} className="text-[var(--color-text-tertiary)] shrink-0" />
                {editingId === session.session_id ? (
                  <input
                    ref={editRef}
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => {
                      e.stopPropagation()
                      if (e.key === 'Enter') saveEdit()
                      if (e.key === 'Escape') cancelEdit()
                    }}
                    onBlur={saveEdit}
                    onClick={(e) => e.stopPropagation()}
                    className="flex-1 min-w-0 px-2 py-0.5 text-sm rounded border border-[var(--color-accent)] bg-[var(--color-bg)] text-[var(--color-text)] outline-none"
                  />
                ) : (
                  <>
                    <span className="text-sm text-[var(--color-text)] truncate">
                      {session.title || t('chat.newSession')}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        startEdit(session)
                      }}
                      className="p-0.5 rounded text-[var(--color-text-tertiary)] opacity-0 group-hover:opacity-100 hover:text-[var(--color-accent)] transition-all"
                    >
                      <Pencil size={12} />
                    </button>
                  </>
                )}
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-xs text-[var(--color-text-tertiary)]">
                  {formatDate(session.created_at)}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setDeleteTarget(session)
                  }}
                  className="p-1 rounded text-[var(--color-text-tertiary)] hover:text-[var(--color-danger)] hover:bg-[var(--color-danger-bg)] transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={() => setDeleteTarget(null)}
        title={t('common.confirm')}
        message={t('sessions.deleteConfirm')}
        variant="danger"
        confirmText={t('common.delete')}
        onConfirm={handleDelete}
      />
    </div>
  )
}
