/**
 * 知识库 & 文档管理 API
 */
import client from './client'
import { endpoints } from './endpoints'
import type {
  KnowledgeDocument,
  KnowledgeDocumentDetail,
  DocumentUploadResponse,
  BatchUploadResponse,
  DeleteResponse,
  PaginatedResponse,
} from '../types/api'

export const knowledgeApi = {
  // ──────────────── 上传 ────────────────

  /** 上传单个文档 */
  upload: async (kbId: number, file: File, title?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (title) formData.append('title', title)
    const res = await client.post<DocumentUploadResponse>(
      endpoints.documentUpload(kbId),
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 0 },
    )
    return res.data
  },

  /** 批量上传文档 */
  batchUpload: async (kbId: number, files: File[]) => {
    const formData = new FormData()
    files.forEach((f) => formData.append('files', f))
    const res = await client.post<BatchUploadResponse>(
      endpoints.documentBatchUpload(kbId),
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 0 },
    )
    return res.data
  },

  // ──────────────── 查询 ────────────────

  /** 文档列表 */
  list: async (
    kbId: number,
    params?: {
      page?: number
      page_size?: number
      status?: string
      file_type?: string
      search?: string
    },
  ) => {
    const res = await client.get<PaginatedResponse<KnowledgeDocument>>(
      endpoints.documentList(kbId),
      { params },
    )
    return res.data
  },

  /** 文档详情 */
  detail: async (kbId: number, docId: number) => {
    const res = await client.get<KnowledgeDocumentDetail>(
      endpoints.documentDetail(kbId, docId),
    )
    return res.data
  },

  // ──────────────── 删除 ────────────────

  /** 删除单个文档 */
  deleteById: async (kbId: number, docId: number) => {
    const res = await client.delete<DeleteResponse>(
      endpoints.documentDelete(kbId, docId),
    )
    return res.data
  },

  /** 批量删除 */
  batchDelete: async (kbId: number, docIds: number[]) => {
    const res = await client.post<DeleteResponse>(
      endpoints.documentBatchDelete(kbId),
      { doc_ids: docIds },
    )
    return res.data
  },

  // ──────────────── 重新处理 ────────────────

  /** 重新处理文档 */
  reprocess: async (kbId: number, docId: number) => {
    const res = await client.post<DocumentUploadResponse>(
      endpoints.documentReprocess(kbId, docId),
    )
    return res.data
  },
}
