# ============================================
# knowledge_base.py - 知识库管理服务
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 类：KnowledgeBaseService
#
# 1. create(db, user_id, kb_data) -> KnowledgeBase
#    - 验证同一用户下名称唯一
#    - 创建知识库
#    - 初始化该知识库的向量集合（调用 vector_store.create_collection）
#    - 写入 audit_log
#
# 2. get_by_id(db, kb_id, user_id) -> KnowledgeBase | None
#    - 按 ID 查询
#    - 校验权限：只有 owner 或 is_public=True 的可访问
#    - 返回知识库对象（含文档数量统计）
#
# 3. get_list(db, user_id, page, page_size, filters) -> (list[KnowledgeBase], total)
#    - 分页查询用户有权限访问的知识库
#    - 返回用户自己的 + is_public=True 的知识库
#    - 支持按名称搜索、按状态过滤
#    - 按 updated_at DESC 排序
#
# 4. update(db, kb_id, user_id, update_data) -> KnowledgeBase
#    - 校验当前用户是否为 owner
#    - 更新知识库信息（name, description, icon, is_public 等）
#    - 写入 audit_log
#
# 5. archive(db, kb_id, user_id) -> KnowledgeBase
#    - 归档知识库（status=archived）
#    - 只允许 owner 操作
#    - 归档后该知识库的文档不再参与检索
#    - 写入 audit_log
#
# 6. delete(db, kb_id, user_id) -> bool
#    - 软删除（status=deleted）
#    - 只允许 owner 操作
#    - 同时删除关联文档的向量数据（调用 vector_store.delete_collection）
#    - 写入 audit_log
#
# 7. get_stats(db, kb_id) -> dict
#    - 返回知识库统计数据
#    - document_count, chunk_count, 各文件类型分布
#    - 最近 7 天的访问量（如果实现了访问追踪）
#
# 8. clone(db, kb_id, user_id, new_name) -> KnowledgeBase
#    - 克隆知识库（复制文档记录，但不复制向量数据，需要重新处理）
#    - 写入 audit_log
#
# ═══════════════════════════════════════════
# 权限校验逻辑：
# ═══════════════════════════════════════════
#
# 知识库的 CRUD 权限的校验链路：
#   1. 路由层注入的 Depends(AuthDependency) 保证用户已登录
#   2. 路由层的 Depends(require_permission("knowledge_base:read")) 保证有操作权限
#   3. Service 层校验：owner_id == current_user.id
#     或 is_public=True（读操作）
#   4. 超级管理员可以访问所有知识库（is_superuser 检查）
# ═══════════════════════════════════════════
