import { useState, useRef, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Send, User, Loader2, BookOpen } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import rehypeHighlight from 'rehype-highlight'
import rehypeRaw from 'rehype-raw'
import { useSSE } from '../hooks/useSSE'
import { endpoints } from '../api/endpoints'
import { sessionsApi } from '../api/sessions'
import { useThemeStore } from '../stores/useThemeStore'
import { useKnowledgeBaseStore } from '../stores/useKnowledgeBaseStore'
import { useChatColorStore } from '../stores/useChatColorStore'
import { toast } from 'sonner'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

function generateSessionId(): string {
  const ts = Date.now().toString(36)
  const rand = Math.random().toString(36).slice(2, 6)
  return `chat_${ts}_${rand}`
}

const quickQuestions = [
  '量子计算与传统计算的核心区别是什么？',
  '如何用Python实现一个简单的神经网络？',
  '区块链技术的基本原理是什么？',
]

export default function AIChat() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const theme = useThemeStore((s) => s.theme)
  const chatColor = useChatColorStore((s) => s.chatColor)
  const { start, loading } = useSSE()

  const {
    list: kbList,
    selectedId: kbId,
    loading: kbLoading,
    fetchList,
    setSelectedId,
  } = useKnowledgeBaseStore()

  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const currentSessionId = useRef(sessionId || '')

  useEffect(() => { fetchList() }, [fetchList])

  useEffect(() => { currentSessionId.current = sessionId || '' }, [sessionId])

  useEffect(() => {
    if (!sessionId) { setMessages([]); return }
    setLoadingHistory(true)
    sessionsApi.get(sessionId)
      .then((data) => {
        const msgs: ChatMessage[] = data.messages
          .filter((m) => m.role === 'user' || m.role === 'assistant')
          .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))
        setMessages(msgs)
        currentSessionId.current = sessionId
      })
      .catch(() => { setMessages([]); toast.error(t('chat.loadHistoryError')) })
      .finally(() => setLoadingHistory(false))
  }, [sessionId])

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const handleSend = useCallback(async (query: string) => {
    if (!query.trim() || loading) return
    const userMsg: ChatMessage = { role: 'user', content: query }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    const sid = currentSessionId.current || generateSessionId()
    const updateAssistant = (content: string) => {
      setMessages((prev) => {
        const newMsgs = [...prev]
        const last = newMsgs[newMsgs.length - 1]
        if (last?.role === 'assistant') {
          newMsgs[newMsgs.length - 1] = { ...last, content: last.content + content }
        } else {
          newMsgs.push({ role: 'assistant', content })
        }
        return newMsgs
      })
    }
    await start(endpoints.chatStream, { message: query, session_id: sid, kb_id: kbId }, {
      onStart: (newSessionId) => {
        if (newSessionId) { currentSessionId.current = newSessionId; if (!sessionId) window.history.replaceState(null, '', `/chat/${newSessionId}`) }
      },
      onResponse: (content) => updateAssistant(content),
      onDone: () => {},
      onError: (error) => updateAssistant(`\n\n> **${t('chat.error')}**: ${error}`),
      onReset: () => {
        setMessages((prev) => { const newMsgs = [...prev]; if (newMsgs.length > 0 && newMsgs[newMsgs.length - 1].role === 'assistant') newMsgs.pop(); return newMsgs })
      },
    })
  }, [loading, sessionId, start, navigate, kbId, t])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(input) }
  }

  const handleNewSession = () => { currentSessionId.current = ''; setMessages([]); navigate('/chat') }

  const isReady = loading || loadingHistory
  const selectedKB = kbList.find((k) => k.id === kbId)

  return (
    <div className="h-full flex flex-col">
      {(messages.length > 0 || kbList.length > 0) && (
        <div className="shrink-0 px-6 py-3 border-b border-[var(--color-border)] bg-[var(--color-card)]/50 backdrop-blur-sm">
          <div className="max-w-3xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen size={14} className="text-[var(--color-text-tertiary)] shrink-0" />
              {kbLoading ? (
                <Loader2 size={12} className="animate-spin text-[var(--color-text-tertiary)]" />
              ) : kbList.length === 0 ? (
                <span className="text-xs text-[var(--color-text-tertiary)]">{t('knowledge.noKBForChat')}</span>
              ) : (
                <select value={kbId ?? ''} onChange={(e) => setSelectedId(Number(e.target.value))}
                  className="text-xs px-2 py-1 rounded border border-[var(--color-border)] bg-[var(--color-card)]/80 text-[var(--color-text)] outline-none cursor-pointer max-w-[200px]">
                  <option value="">{t('chat.noKB')}</option>
                  {kbList.map((kb) => (<option key={kb.id} value={kb.id}>{kb.name}</option>))}
                </select>
              )}
              {selectedKB && <span className="text-xs text-[var(--color-text-tertiary)] hidden sm:inline">{selectedKB.document_count} {t('common.documents')}</span>}
            </div>
            <button onClick={handleNewSession} className="px-3 py-1.5 text-xs rounded-md border border-[var(--color-border)] bg-[var(--color-card)]/80 text-[var(--color-text-secondary)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] transition-colors">
              {t('chat.newSession')}
            </button>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && !isReady && (
            <div className="py-16 text-center space-y-6">
              <h2 className="font-heading text-xl text-white drop-shadow-md">{t('chat.welcome')}</h2>
              <div className="flex flex-wrap justify-center gap-2 max-w-md mx-auto">
                {quickQuestions.map((q) => (
                  <button key={q} onClick={() => handleSend(q)}
                    className="px-4 py-2 text-xs rounded-full border border-white/30 bg-white/10 backdrop-blur-sm text-white/90 hover:bg-white/20 hover:border-white/50 transition-colors">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {loadingHistory && <div className="flex justify-center py-4"><Loader2 size={20} className="animate-spin text-[var(--color-text-tertiary)]" /></div>}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-lg bg-rose-100 dark:bg-rose-900/40 flex items-center justify-center shrink-0">
                  <span className="text-rose-500 dark:text-rose-300 text-xs font-bold">艺</span>
                </div>
              )}
              <div className={`max-w-[75%] ${msg.role === 'user' ? 'order-first' : ''}`}>
                {msg.role === 'user' ? (
                  <div className="px-4 py-2.5 rounded-2xl bg-rose-400 text-white text-sm">{msg.content}</div>
                ) : (
                  <div style={{ color: chatColor }} className="prose prose-sm max-w-none markdown-body [&_*]:text-inherit [&_code]:text-white [&_pre]:text-white [&_blockquote]:text-white [&_a]:text-rose-300 [&_:not(pre)>code]:bg-gray-700 [&_:not(pre)>code]:text-emerald-300 bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                    <ReactMarkdown rehypePlugins={[rehypeHighlight, rehypeRaw]}>{msg.content || '...'}</ReactMarkdown>
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-[var(--color-bg-tertiary)] flex items-center justify-center shrink-0">
                  <User size={16} className="text-[var(--color-text-secondary)]" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 items-start">
              <div className="w-8 h-8 rounded-lg bg-rose-100 dark:bg-rose-900/40 flex items-center justify-center shrink-0">
                <span className="text-rose-500 dark:text-rose-300 text-xs font-bold">艺</span>
              </div>
              <div className="flex flex-col gap-1.5 py-1">
                <div className="flex gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-400 animate-bounce" style={{ animationDelay: '0ms', animationDuration: '0.8s' }} />
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-400 animate-bounce" style={{ animationDelay: '200ms', animationDuration: '0.8s' }} />
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-400 animate-bounce" style={{ animationDelay: '400ms', animationDuration: '0.8s' }} />
                </div>
                <span className="text-xs text-[var(--color-text-tertiary)] mt-1">{t('chat.thinking')}</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t border-[var(--color-border)] bg-[var(--color-card)]/60 backdrop-blur-sm px-6 py-4">
        <div className="max-w-3xl mx-auto flex gap-3">
          <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
            placeholder={t('chat.input')} rows={1}
            className="flex-1 px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)]/80 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] resize-none focus:outline-none focus:ring-2 focus:ring-rose-400" />
          <button onClick={() => handleSend(input)} disabled={!input.trim() || loading}
            className="flex items-center justify-center w-10 h-10 rounded-lg bg-rose-400 text-white hover:bg-rose-500 disabled:opacity-40 transition-colors shrink-0">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
      </div>
    </div>
  )
}