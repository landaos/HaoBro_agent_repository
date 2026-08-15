import { useRef, useState, useCallback } from 'react'
import type { SSEMessage } from '../types/api'

type SSECallbacks = {
  onStart?: (sessionId?: string) => void
  onResponse?: (content: string, sessionId?: string) => void
  onDone?: (sessionId?: string) => void
  onError?: (error: string) => void
  onReset?: () => void
}

/**
 * SSE 流式请求 Hook
 *
 * 解析格式：
 *   data: {"type":"start","session_id":"xxx"}
 *   data: {"type":"response","content":"字"}
 *   data: {"type":"done","session_id":"xxx"}
 *   data: {"type":"error","content":"msg"}
 */
export function useSSE() {
  const abortRef = useRef<AbortController | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const start = useCallback(
    async (url: string, body: Record<string, unknown>, callbacks: SSECallbacks) => {
      setLoading(true)
      setError(null)
      // 先中断上一次请求（如有），再创建新控制器
      abortRef.current?.abort()
      abortRef.current = new AbortController()

      try {
        const token = localStorage.getItem('jwt_token')
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(body),
          signal: abortRef.current.signal,
        })

        if (!response.ok) {
          callbacks.onError?.(`HTTP ${response.status}`)
          setError(`HTTP ${response.status}`)
          setLoading(false)
          return
        }

        const reader = response.body?.getReader()
        if (!reader) {
          callbacks.onError?.('No response body')
          setError('No response body')
          setLoading(false)
          return
        }

        const decoder = new TextDecoder()
        let buffer = ''

        // 累积文本块，批量刷新
        const textBuffer: string[] = []
        const FLUSH_THRESHOLD = 3
        let lastSessionId: string | undefined

        const flush = () => {
          if (textBuffer.length === 0) return
          const content = textBuffer.join('')
          textBuffer.length = 0
          callbacks.onResponse?.(content, lastSessionId)
        }

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            try {
              const data = JSON.parse(line.slice(6)) as SSEMessage

              switch (data.type) {
                case 'start':
                  lastSessionId = data.session_id
                  callbacks.onStart?.(data.session_id)
                  break

                case 'response':
                  if (data.session_id) lastSessionId = data.session_id
                  if (data.content) {
                    textBuffer.push(data.content)
                    if (textBuffer.length >= FLUSH_THRESHOLD) flush()
                  }
                  break

                case 'done':
                  flush()
                  callbacks.onDone?.(data.session_id || lastSessionId)
                  break

                case 'error':
                  flush()
                  callbacks.onError?.(data.content || 'Unknown error')
                  setError(data.content || 'Unknown error')
                  break

                case 'reset':
                  textBuffer.length = 0
                  callbacks.onReset?.()
                  break
              }
            } catch {
              // 跳过 JSON 解析失败的行
            }
          }
        }
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : '未知错误'
        const errName = err instanceof Error ? err.name : 'Unknown'
        console.warn(`[SSE] ${errName}: ${errMsg}`)
        if (err instanceof Error && err.name !== 'AbortError') {
          callbacks.onError?.(errMsg)
          setError(errMsg)
        } else if (err instanceof Error && err.name === 'AbortError') {
          // 在 UI 上也提示用户请求被中断
          callbacks.onError?.('连接被中断，请重试')
          setError('连接被中断')
        }
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  const abort = useCallback(() => {
    abortRef.current?.abort()
    setLoading(false)
  }, [])

  return { start, abort, loading, error }
}
