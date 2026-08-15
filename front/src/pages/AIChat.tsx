import { useState, useRef, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Send, Bot, User, Loader2, Sparkles, BookOpen } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import rehypeHighlight from 'rehype-highlight'
import rehypeRaw from 'rehype-raw'
import { useSSE } from '../hooks/useSSE'
import { endpoints } from '../api/endpoints'
import { sessionsApi } from '../api/sessions'
import { useThemeStore } from '../stores/useThemeStore'
import { useKnowledgeBaseStore } from '../stores/useKnowledgeBaseStore'
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
  '帮我解释一下什么是 RAG',
  '写一首关于夏天的诗',
  '推荐几本提升思维的书',
]

export default function AIChat() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const theme = useThemeStore((s) => s.theme)
  const { start, loading } = useSSE()

  // 知识库选择
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

  // 页面加载时获取知识库列表
  useEffect(() => {
    fetchList()
  }, [fetchList])

  useEffect(() => {
    currentSessionId.current = sessionId || ''
  }, [sessionId])

  // ── 加载历史消息 ──
  useEffect(() => {
    if (!sessionId) {
      setMessages([])
      return
    }
    setLoadingHistory(true)
    sessionsApi
      .get(sessionId)
      .then((data) => {
        const msgs: ChatMessage[] = data.messages
          .filter((m) => m.role === 'user' || m.role === 'assistant')
          .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))
        setMessages(msgs)
        currentSessionId.current = sessionId
      })
      .catch(() => {
        setMessages([])
        toast.error('加载历史消息失败')
      })
      .finally(() => setLoadingHistory(false))
  }, [sessionId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ── 发送消息 ──
  const handleSend = useCallback(
    async (query: string) => {
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

      await start(
        endpoints.chatStream,
        {
          message: query,
          session_id: sid,
          kb_id: kbId, // 绑定当前选中的知识库
        },
        {
          onStart: (newSessionId) => {
            if (newSessionId) {
              currentSessionId.current = newSessionId
              if (!sessionId) {
                window.history.replaceState(null, '', `/chat/${newSessionId}`)
              }
            }
          },
          onResponse: (content) => updateAssistant(content),
          onDone: () => {},
          onError: (error) => updateAssistant(`\n\n> **错误**: ${error}`),
          onReset: () => {
            setMessages((prev) => {
              const newMsgs = [...prev]
              if (newMsgs.length > 0 && newMsgs[newMsgs.length - 1].role === 'assistant') {
                newMsgs.pop()
              }
              return newMsgs
            })
          },
        },
      )
    },
    [loading, sessionId, start, navigate, kbId],
  )

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend(input)
    }
  }

  const handleNewSession = () => {
    currentSessionId.current = ''
    setMessages([])
    navigate('/chat')
  }

  const isReady = loading || loadingHistory

  const selectedKB = kbList.find((k) => k.id === kbId)

  return (
    <div className="h-full flex flex-col">
      {/* 顶部操作栏 */}
      {(messages.length > 0 || kbList.length > 0) && (
        <div className="shrink-0 px-6 py-3 border-b border-[var(--color-border)] bg-[var(--color-bg)]">
          <div className="max-w-3xl mx-auto flex items-center justify-between">
            {/* 知识库选择器 */}
            <div className="flex items-center gap-2">
              <BookOpen size={14} className="text-[var(--color-text-tertiary)] shrink-0" />
              {kbLoading ? (
                <Loader2 size={12} className="animate-spin text-[var(--color-text-tertiary)]" />
              ) : kbList.length === 0 ? (
                <span className="text-xs text-[var(--color-text-tertiary)]">{t('knowledge.noKBForChat')}</span>
              ) : (
                <select
                  value={kbId ?? ''}
                  onChange={(e) => setSelectedId(Number(e.target.value))}
                  className="text-xs px-2 py-1 rounded border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-text)] outline-none cursor-pointer max-w-[200px]"
                >
                  <option value="">不绑定知识库</option>
                  {kbList.map((kb) => (
                    <option key={kb.id} value={kb.id}>
                      {kb.name}
                    </option>
                  ))}
                </select>
              )}
              {selectedKB && (
                <span className="text-xs text-[var(--color-text-tertiary)] hidden sm:inline">
                  {selectedKB.document_count} 文档
                </span>
              )}
            </div>

            <button
              onClick={handleNewSession}
              className="px-3 py-1.5 text-xs rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] transition-colors"
            >
              {t('chat.newSession')}
            </button>
          </div>
        </div>
      )}

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && !isReady && (
            <div className="py-16 text-center space-y-6">
              <div className="flex justify-center">
                <div className="w-16 h-16 rounded-2xl bg-[var(--color-accent-bg)] flex items-center justify-center">
                  <Sparkles size={28} className="text-[var(--color-accent)]" />
                </div>
              </div>
              <h2 className="font-heading text-xl text-[var(--color-text)]">{t('chat.welcome')}</h2>
              <div className="flex flex-wrap justify-center gap-2 max-w-md mx-auto">
                {quickQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="px-4 py-2 text-xs rounded-full border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {loadingHistory && (
            <div className="flex justify-center py-4">
              <Loader2 size={20} className="animate-spin text-[var(--color-text-tertiary)]" />
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-lg bg-[var(--color-accent-bg)] flex items-center justify-center shrink-0">
                  <Bot size={16} className="text-[var(--color-accent)]" />
                </div>
              )}
              <div className={`max-w-[75%] ${msg.role === 'user' ? 'order-first' : ''}`}>
                {msg.role === 'user' ? (
                  <div className="px-4 py-2.5 rounded-2xl bg-[var(--color-accent)] text-white text-sm">
                    {msg.content}
                  </div>
                ) : (
                  <div className={`prose prose-sm max-w-none markdown-body${theme === 'dark' ? ' prose-invert' : ''}`}>
                    <ReactMarkdown rehypePlugins={[rehypeHighlight, rehypeRaw]}>
                      {msg.content || '...'}
                    </ReactMarkdown>
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
              <div className="w-8 h-8 rounded-lg bg-[var(--color-accent-bg)] flex items-center justify-center shrink-0 animate-pulse">
                <Bot size={16} className="text-[var(--color-accent)]" />
              </div>
              <div className="flex flex-col gap-1.5 py-1">
                <div className="flex gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[var(--color-accent)] animate-bounce" style={{ animationDelay: '0ms', animationDuration: '0.8s' }} />
                  <span className="w-2.5 h-2.5 rounded-full bg-[var(--color-accent)] animate-bounce" style={{ animationDelay: '200ms', animationDuration: '0.8s' }} />
                  <span className="w-2.5 h-2.5 rounded-full bg-[var(--color-accent)] animate-bounce" style={{ animationDelay: '400ms', animationDuration: '0.8s' }} />
                </div>
                <span className="text-xs text-[var(--color-text-tertiary)] mt-1">思考中...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 输入框 */}
      <div className="border-t border-[var(--color-border)] bg-[var(--color-card)] px-6 py-4">
        <div className="max-w-3xl mx-auto flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('chat.input')}
            rows={1}
            className="flex-1 px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] resize-none focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
          />
          <button
            onClick={() => handleSend(input)}
            disabled={!input.trim() || loading}
            className="flex items-center justify-center w-10 h-10 rounded-lg bg-[var(--color-accent)] text-white hover:bg-blue-700 disabled:opacity-40 transition-colors shrink-0"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
      </div>
    </div>
  )
}
