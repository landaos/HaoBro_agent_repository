# ============================================
# order.py - 订单相关工具
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的工具函数（langchain Tool）：
# ═══════════════════════════════════════════
#
# 1. dingdan_get(dingdan_id: str) -> str
#    - 从现有 kefu_agent.py 迁移
#    - 功能：按订单 ID 查询订单详情
#    - 输入：dingdan_id（字符串）
#    - 输出：格式化的订单信息字符串
#
# 2. tuihuo(dingdan_id: str, why: str) -> str
#    - 从现有 kefu_agent.py 迁移
#    - 功能：取消订单（模拟操作）
#    - 输入：dingdan_id（字符串），why（取消原因）
#    - 输出：取消结果字符串
#
# 3. 将来可以增加的：
#    - create_order(user_id, product_id, quantity) → 创建订单
#    - get_order_status(order_id) → 查询物流状态
#    - modify_order(order_id, changes) → 改单
#
# ═══════════════════════════════════════════
# 每个工具函数最终包装成 @tool 装饰器：
#   from langchain_core.tools import tool
#   @tool
#   def dingdan_get(dingdan_id: str) -> str:
#       """查询订单信息"""
#       ...
# ═══════════════════════════════════════════
