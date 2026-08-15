/**
 * 后端 API 端点
 * 所有路径都会通过 Vite proxy 代理到后端
 */

const API_PREFIX = '/api/v1'

export const endpoints = {
  // 健康检查
  health: `${API_PREFIX}/health`,

  // 对话（SSE 流式）
  chatStream: `${API_PREFIX}/chat`,

  // 用户认证
  userLogin: `${API_PREFIX}/user/login`,
  userRegister: `${API_PREFIX}/user/register`,
  userLogout: `${API_PREFIX}/user/logout`,
  userDetail: `${API_PREFIX}/user/detail/`,
  userUpdate: `${API_PREFIX}/user/update/`,
  userResetPassword: `${API_PREFIX}/user/reset-password`,

  // 会话 CRUD
  conversationsList: `${API_PREFIX}/conversations`,
  conversationDetail: (sessionId: string) => `${API_PREFIX}/conversations/${sessionId}`,

  // ──────────────── 文档管理（知识库）────────────────

  /** 上传文档 */
  documentUpload: (kbId: number) => `${API_PREFIX}/knowledge-bases/${kbId}/documents/upload`,
  /** 批量上传 */
  documentBatchUpload: (kbId: number) => `${API_PREFIX}/knowledge-bases/${kbId}/documents/batch-upload`,
  /** 文档列表（分页） */
  documentList: (kbId: number) => `${API_PREFIX}/knowledge-bases/${kbId}/documents`,
  /** 文档详情 */
  documentDetail: (kbId: number, docId: number) => `${API_PREFIX}/knowledge-bases/${kbId}/documents/${docId}`,
  /** 删除文档 */
  documentDelete: (kbId: number, docId: number) => `${API_PREFIX}/knowledge-bases/${kbId}/documents/${docId}`,
  /** 批量删除 */
  documentBatchDelete: (kbId: number) => `${API_PREFIX}/knowledge-bases/${kbId}/documents/batch-delete`,
  /** 重新处理 */
  documentReprocess: (kbId: number, docId: number) => `${API_PREFIX}/knowledge-bases/${kbId}/documents/${docId}/reprocess`,

  // ──────────────── 知识库 CRUD ────────────────

  /** 知识库列表 */
  knowledgeBaseList: `${API_PREFIX}/knowledge-bases`,
  /** 知识库详情 */
  knowledgeBaseDetail: (kbId: number) => `${API_PREFIX}/knowledge-bases/${kbId}`,
  /** 创建知识库 */
  knowledgeBaseCreate: `${API_PREFIX}/knowledge-bases`,
  /** 删除知识库 */
  knowledgeBaseDelete: (kbId: number) => `${API_PREFIX}/knowledge-bases/${kbId}`,
} as const
