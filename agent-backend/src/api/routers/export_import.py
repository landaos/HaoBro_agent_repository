# ============================================
# export_import.py - 数据导入导出 API 路由
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的路由：
# ═══════════════════════════════════════════
#
# 所有路由挂载在 /api/v1/export-import 下
# 需要权限：require_permission("system:export") / require_permission("system:import")
#
# 导出接口：
#
# 1. POST /export-import/export/knowledge-bases
#    - 导出知识库（JSON 格式）
#    - 请求体：{kb_ids: list[int] | null（null=导出所有）}
#    - 响应：application/json（文件下载）
#    - 权限：require_permission("system:export")
#
# 2. POST /export-import/export/knowledge-bases/{kb_id}/csv
#    - 导出知识库文档列表为 CSV
#    - 响应：text/csv（文件下载）
#    - 权限：require_permission("system:export")
#
# 3. POST /export-import/export/knowledge-bases/{kb_id}/markdown
#    - 导出知识库文档为 Markdown
#    - 响应：text/markdown（文件下载）
#    - 权限：require_permission("system:export")
#
# 导入接口：
#
# 4. POST /export-import/import/knowledge-bases
#    - 从 JSON 导入知识库
#    - 请求体：multipart/form-data（file）
#    - 响应：ImportResultResponse
#    - 权限：require_permission("system:import")
#
# 5. POST /export-import/import/knowledge-bases/{kb_id}/csv
#    - 从 CSV 导入文档到指定知识库
#    - 请求体：multipart/form-data（file）
#    - 响应：ImportResultResponse
#    - 权限：require_permission("system:import")
#
# ═══════════════════════════════════════════
# 注意事项：
# ═══════════════════════════════════════════
#
# 1. 大文件导入通过 task_queue 异步处理
# 2. 导入接口返回 task_id，前端轮询处理结果
# 3. 导出接口直接返回文件流
# 4. 审计日志记录每次导入/导出操作
# 5. 文件大小限制：导入文件 ≤ 100MB
# ═══════════════════════════════════════════
