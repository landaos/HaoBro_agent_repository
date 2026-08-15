# ============================================
# feedback.py - 用户反馈收集服务
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的代码：
# ═══════════════════════════════════════════
#
# 一、反馈数据模型：
#    表名：feedbacks（或存在 messages 表的 metadata 字段中）
#    - id: UUID
#    - message_id: UUID（关联到 messages 表）
#    - session_id: str
#    - user_id: str
#    - rating: int（1=差, 2=一般, 3=好, 4=很好, 5=非常好）
#    - feedback_type: str（"rating" | "correction" | "report"）
#    - comment: Text | None（用户补充的文字反馈）
#    - created_at: DateTime
#
# 二、API 接口（在 api/routers/chat.py 中加）：
#    POST /chat/feedback
#    请求体：
#    {
#        "message_id": "uuid",
#        "rating": 4,
#        "feedback_type": "rating",
#        "comment": "回答很准确，但希望能引用文档编号"
#    }
#
# 三、存储函数：
#    async def save_feedback(db: AsyncSession, feedback: FeedbackCreate) -> Feedback
#    async def get_feedback_stats(db: AsyncSession, start_date: datetime, end_date: datetime) -> dict
#        # 返回统计数据：平均分、总数、各分数分布
#
# 四、RAG 质量追踪：
#    在 agent 输出中记录：
#    - 本次回答引用了哪些文档（doc_ids）
#    - 用户是否认为回答有帮助
#    定期分析：哪些文档被引用后用户评分高/低
#
# ═══════════════════════════════════════════
# 建议前端在每条回复底部加：
#   👍 有帮助  👎 没帮助  📝 反馈
# 数据积累起来后可以做 RAG 质量看板
# ═══════════════════════════════════════════
