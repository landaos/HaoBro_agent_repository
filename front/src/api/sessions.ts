/**
 * 会话管理 API — 对应后端 /api/v1/conversations
 */
import client from './client'
import { endpoints } from './endpoints'
import type { Conversation, ConversationDetail } from '../types/api'

export interface ListResponse {
  data: Conversation[]
  total: number
}

export const sessionsApi = {
  /** 获取会话列表（user_id 由后端从 JWT 提取） */
  list: async () => {
    const res = await client.get<ListResponse>(endpoints.conversationsList)
    return res.data
  },

  /** 获取会话详情（含消息） */
  get: async (sessionId: string) => {
    const res = await client.get<ConversationDetail>(endpoints.conversationDetail(sessionId))
    return res.data
  },

  /** 更新会话 */
  update: async (sessionId: string, data: { title?: string }) => {
    const res = await client.put<Conversation>(endpoints.conversationDetail(sessionId), data)
    return res.data
  },

  /** 删除会话（返回 204 No Content） */
  delete: async (sessionId: string) => {
    await client.delete(endpoints.conversationDetail(sessionId))
  },
}
