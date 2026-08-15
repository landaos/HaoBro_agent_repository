/**
 * 知识库管理 API
 */
import client from './client'
import { endpoints } from './endpoints'
import type {
  KnowledgeBase,
  KnowledgeBaseListResponse,
} from '../types/api'

export const knowledgeBaseApi = {
  /** 获取当前用户的所有知识库 */
  list: async () => {
    const res = await client.get<KnowledgeBaseListResponse>(
      endpoints.knowledgeBaseList,
    )
    return res.data
  },

  /** 创建知识库 */
  create: async (data: { name: string; description?: string }) => {
    const res = await client.post<KnowledgeBase>(
      endpoints.knowledgeBaseCreate,
      data,
    )
    return res.data
  },

  /** 删除知识库 */
  delete: async (kbId: number) => {
    const res = await client.delete(endpoints.knowledgeBaseDelete(kbId))
    return res.data
  },
}
