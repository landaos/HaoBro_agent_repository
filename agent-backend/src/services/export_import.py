# ============================================
# export_import.py - 批量导入导出服务
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 类：ExportImportService
#
# 一、导出功能
#
# 1. export_knowledge_bases(db, user_id, kb_ids: list[int] | None) -> bytes
#    - 导出知识库（JSON 格式）
#    - 如果 kb_ids 为空，导出用户所有知识库
#    - 包含：知识库元信息 + 关联的文档内容
#    - 不包含：向量数据（向量不可移植）
#    - 返回 JSON bytes（可压缩为 .json.gz）
#    - 导出文件结构：
#      {
#          "version": "1.0",
#          "exported_at": "2026-07-17T10:00:00Z",
#          "exported_by": user_id,
#          "knowledge_bases": [
#              {
#                  "name": "产品手册",
#                  "description": "...",
#                  "documents": [
#                      {"title": "README.md", "content": "...", "file_type": "md"}
#                  ]
#              }
#          ]
#      }
#
# 2. export_to_csv(db, kb_id, user_id) -> str
#    - 导出知识库文档为 CSV 格式（方便用 Excel 打开）
#    - 列：id, title, file_type, chunk_count, status, created_at, updated_at
#    - CSV 编码：utf-8-bom（Excel 兼容）
#
# 3. export_to_markdown(db, kb_id, user_id) -> str
#    - 将知识库所有文档合并为一个 Markdown 文件
#    - 按文件夹层级整理
#    - 适合导出后阅读
#
# 二、导入功能
#
# 4. import_knowledge_bases(db, user_id, json_data: bytes) -> ImportResult
#    - 从 JSON 格式导入知识库
#    - 校验 JSON 结构
#    - 逐个导入知识库 + 文档
#    - 自动处理名称冲突（追加时间后缀）
#    - 导入的文档自动触发 processing
#    - 返回 ImportResult：
#      {
#          "total": 5,
#          "success": 4,
#          "failed": 1,
#          "errors": [{"name": "产品手册", "error": "名称已存在"}]
#      }
#
# 5. import_from_csv(db, user_id, csv_data: str, kb_id: int) -> ImportResult
#    - 从 CSV 导入文档到指定知识库
#    - 列：title, content（file_type 自动从 title 后缀识别）
#    - 返回同上
#
# ═══════════════════════════════════════════
# 安全与限制：
# ═══════════════════════════════════════════
#
# 1. 导入时进行内容安全检查（prompt injection 检测）
# 2. 单次导入文档数上限：500（防止 OOM）
# 3. 导出文件大小上限：100MB（超出则分卷导出）
# 4. 导入操作记录 audit_log
# 5. 大型导入通过 task_queue 异步执行
# ═══════════════════════════════════════════
