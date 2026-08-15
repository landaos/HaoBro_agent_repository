# ============================================
# user_service.py - 用户管理服务
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 类：UserService
#
# 1. register(db, user_data) -> User
#    - 检查用户名/邮箱是否已存在（唯一性校验）
#    - 密码哈希（passlib bcrypt）
#    - 创建用户，默认分配 viewer 角色
#    - 写入 audit_log 记录
#    - 返回用户对象（不含密码）
#
# 2. authenticate(db, username, password) -> User | None
#    - 根据用户名或邮箱查找用户
#    - 验证密码（passlib verify）
#    - 检查 is_active
#    - 更新 last_login_at
#    - 写入 audit_log（login / login_failed）
#    - 返回用户对象或 None
#
# 3. get_by_id(db, user_id) -> User | None
#    - 按 ID 查询用户
#    - 连表查询角色和权限信息
#
# 4. get_list(db, page, page_size, filters) -> (list[User], total)
#    - 分页查询用户列表
#    - 支持按用户名/邮箱/角色/状态过滤
#    - 不返回 password_hash 字段
#
# 5. update(db, user_id, update_data) -> User
#    - 更新用户信息（display_name, email, phone 等）
#    - 不允许修改 username（唯一标识，创建后不改）
#    - 写入 audit_log
#
# 6. update_role(db, user_id, role_id) -> User
#    - 变更用户角色
#    - 不允许将超级管理员降级
#    - 写入 audit_log
#
# 7. set_active_status(db, user_id, is_active) -> User
#    - 启用/禁用用户
#    - 不允许禁用自己
#    - 不允许禁用超级管理员
#    - 写入 audit_log
#
# 8. change_password(db, user_id, old_password, new_password) -> bool
#    - 验证旧密码
#    - 新密码哈希后更新
#    - 写入 audit_log
#
# 9. delete(db, user_id) -> bool
#    - 软删除（设置 is_active=False）
#    - 不允许删除自己
#    - 写入 audit_log
#
# ═══════════════════════════════════════════
# 密码策略（在 schema 层校验）：
# ═══════════════════════════════════════════
#
# - 最少 8 位
# - 至少包含一个字母和一个数字
# - 不能与用户名/邮箱相似
# - 不能是常见密码（如 123456, password）
# ═══════════════════════════════════════════


    
