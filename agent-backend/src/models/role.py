# ============================================
# role.py - 角色与权限表（ORM 模型）
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的模型：
# ═══════════════════════════════════════════
#
# 1. 角色表（roles）
#    表名：roles
#    字段：
#       id:             Integer, 主键, 自增
#       name:           String(50), 唯一, 非空, 索引（角色名：admin / editor / viewer）
#       description:    String(255), 可空（角色描述）
#       is_system:      Boolean, 默认 False（系统内置角色不可删除）
#       created_at:     DateTime, 默认 now()
#    关系：
#       users:          one-to-many → User
#       permissions:    many-to-many → Permission（通过关联表）
#
# 2. 权限表（permissions）
#    表名：permissions
#    字段：
#       id:             Integer, 主键, 自增
#       code:           String(100), 唯一, 非空, 索引（权限标识）
#       module:         String(50), 非空（所属模块）
#       description:    String(255), 可空
#    关系：
#       roles:          many-to-many → Role（通过关联表）
#
# 3. 角色-权限关联表（role_permission）
#    表名：role_permission
#    字段：
#       role_id:        Integer, 外键 → roles.id, 联合主键
#       permission_id:  Integer, 外键 → permissions.id, 联合主键
#
# ═══════════════════════════════════════════
# 权限标识（code）命名规范：
# ═══════════════════════════════════════════
#
#   格式：{module}:{action}
#   action 取值：create / read / update / delete / manage
#
#   系统管理模块：
#     user:create       创建用户
#     user:read         查看用户
#     user:update       编辑用户
#     user:delete       删除用户
#     role:manage       管理角色（含分配权限）
#
#   知识库模块：
#     knowledge_base:create    创建知识库
#     knowledge_base:read      查看知识库
#     knowledge_base:update    编辑知识库
#     knowledge_base:delete    删除知识库
#
#   文档模块：
#     document:upload      上传文档
#     document:read        查看文档
#     document:delete      删除文档
#
#   系统模块：
#     system:view_stats    查看统计
#     system:export        导出数据
#     system:import        导入数据
#     system:view_audit    查看审计日志
#
# ═══════════════════════════════════════════
# 系统内置角色：
# ═══════════════════════════════════════════
#
#   admin（管理员）：
#     - 拥有所有权限
#     - 管理角色分配
#     - is_system = True
#
#   editor（编辑者）：
#     - 知识库：create / read / update / delete（自己创建的）
#     - 文档：upload / read / delete（自己上传的）
#     - 查看统计
#
#   viewer（查看者）：
#     - 知识库：read
#     - 文档：read
#
# ═══════════════════════════════════════════
# 数据库索引：
# ═══════════════════════════════════════════
#
# 必须创建的索引：
#   idx_roles_name ON roles(name) UNIQUE
#   idx_permissions_code ON permissions(code) UNIQUE
#   idx_permissions_module ON permissions(module)
# ═══════════════════════════════════════════
