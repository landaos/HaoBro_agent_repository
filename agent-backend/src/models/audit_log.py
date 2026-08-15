# ============================================
# audit_log.py - 审计日志表（ORM 模型）
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的模型：
# ═══════════════════════════════════════════
#
# 表名：audit_logs
#
# 字段：
#   id:              BigInteger, 主键, 自增（BigInteger 因为日志量可能很大）
#   user_id:         Integer, 外键 → users.id, 非空, 索引
#   username:        String(64), 可空（冗余字段，用户删除后仍可追溯）
#   action:          String(50), 非空（操作类型）
#   resource:        String(100), 非空（操作资源类型）
#   resource_id:     String(50), 可空（操作资源 ID）
#   detail:          JSONB, 默认 {}（操作详情，记录变更前后的值）
#   ip_address:      String(45), 可空（客户端 IP，支持 IPv6）
#   user_agent:      String(512), 可空（客户端 UA）
#   status_code:     Integer, 可空（HTTP 状态码）
#   duration_ms:     Integer, 可空（请求耗时，毫秒）
#   created_at:      DateTime, 默认 now(), 索引（按时间查日志是高频操作）
#
# ═══════════════════════════════════════════
# action 取值规范：
# ═══════════════════════════════════════════
#
#   登录/登出:
#     login, logout, login_failed
#
#   用户管理:
#     user_create, user_update, user_delete, user_disable
#
#   角色管理:
#     role_create, role_update, role_delete, role_assign
#
#   知识库管理:
#     kb_create, kb_update, kb_delete, kb_archive
#
#   文档管理:
#     doc_upload, doc_delete, doc_reprocess
#
#   系统操作:
#     export, import, stats_view
#
# ═══════════════════════════════════════════
# 数据量预估与归档策略：
# ═══════════════════════════════════════════
#
# 假设日均 5000 次操作（50 用户 × 100 次/天），
# 1 年 ≈ 180 万条，约 500MB-1GB。
#
# 生产环境建议：
#   1. 主表只保留 90 天的数据
#   2. 超过 90 天的自动归档到 audit_logs_archive 表
#   3. archive 表按月分区（PARTITION BY RANGE）
#   4. 归档脚本通过 APScheduler 定时运行（每周一次）
#   5. 超过 1 年的数据可压缩存储或导出后删除
#
# ═══════════════════════════════════════════
# 数据库索引：
# ═══════════════════════════════════════════
#
# 必须创建的索引：
#   idx_audit_user_id ON audit_logs(user_id)
#   idx_audit_action ON audit_logs(action)
#   idx_audit_resource ON audit_logs(resource)
#   idx_audit_created_at ON audit_logs(created_at DESC)
#
# 建议创建的索引：
#   idx_audit_user_time ON audit_logs(user_id, created_at DESC)  # 复合索引
#   idx_audit_detail_gin ON audit_logs USING GIN (detail)        # JSON 查询
# ═══════════════════════════════════════════
