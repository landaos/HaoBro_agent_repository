/* ============================================================
 * 后端 API 类型定义
 * 对应 agent-backend 的数据结构
 * ============================================================ */

/** 用户信息 */
export interface UserInfo {
  user_id?: string
  username?: string
  email?: string
  phone?: string
  gender?: number
  status?: number
  created_at?: string
  updated_at?: string
}

// ════════════════════════════════════════════════════════════
// 通用类型
// ════════════════════════════════════════════════════════════

export interface ApiResponse<T = unknown> {
  success?: boolean
  message?: string
  data?: T
  items?: T[]
  total?: number
}

export interface ChatSession {
  id: string
  title: string
}

/** 会话列表 */
export interface Conversation {
  id: string
  session_id: string
  user_id: string
  title: string | null
  created_at: string | null
  updated_at: string | null
}

/** 单条消息 */
export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  extra_data?: Record<string, unknown>
  created_at: string | null
}

/** 会话详情（含消息列表） */
export interface ConversationDetail {
  conversation: Conversation
  messages: Message[]
}

/** SSE 流式数据块 */
export interface SSEMessage {
  type: 'start' | 'response' | 'done' | 'error' | 'reset'
  content?: string
  session_id?: string
}

// ════════════════════════════════════════════════════════════
// 文档管理类型
// ════════════════════════════════════════════════════════════

/** 文档列表项 */
export interface KnowledgeDocument {
  id: number
  kb_id: number
  title: string
  file_name: string
  file_type: string
  file_size: number | null
  chunk_count: number
  status: DocumentStatus
  error_message: string | null
  tags: string[]
  uploader_id: number
  created_at: string
  updated_at: string | null
}

export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed'

/** 文档详情 */
export interface KnowledgeDocumentDetail extends KnowledgeDocument {
  content: string | null
  metadata: Record<string, unknown>
}

/** 上传响应 */
export interface DocumentUploadResponse {
  document: KnowledgeDocument
  message: string
}

/** 批量上传响应 */
export interface BatchUploadResponse {
  documents: KnowledgeDocument[]
  failed_count: number
  errors: Array<{ filename: string; error: string }>
}

/** 删除响应 */
export interface DeleteResponse {
  status: string
  deleted_vector_count: number
  message: string
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ════════════════════════════════════════════════════════════
// 知识库类型
// ════════════════════════════════════════════════════════════

export interface KnowledgeBase {
  id: number
  user_id: number
  name: string
  description: string | null
  document_count: number
  created_at: string
  updated_at: string | null
}

export interface KnowledgeBaseListResponse {
  items: KnowledgeBase[]
  total: number
}
