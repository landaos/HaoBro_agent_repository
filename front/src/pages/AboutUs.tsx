import { Sparkles } from 'lucide-react'

export default function AboutUs() {
  return (
    <div className="max-w-2xl mx-auto py-8 px-6">
      <div className="text-center mb-8">
        <div className="mx-auto w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mb-4">
          <Sparkles size={26} className="text-white" />
        </div>
        <h1 className="text-xl font-bold text-[var(--color-text)]">小易问答助手</h1>
        <p className="mt-2 text-sm text-[var(--color-text-tertiary)]">基于 RAG 技术的智能知识库问答系统</p>
      </div>

      <div className="bg-[var(--color-card)] rounded-xl border border-[var(--color-border)] p-6 space-y-6">
        <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
          小易问答助手是一套基于 RAG（检索增强生成）技术构建的企业级智能知识库问答系统。支持文档上传、向量检索、智能分段，结合大语言模型提供精准的知识问答服务。
        </p>

        <div>
          <h3 className="text-sm font-medium text-[var(--color-text)] mb-3">技术栈</h3>
          <div className="flex flex-wrap gap-2">
            {['React', 'TypeScript', 'FastAPI', 'LangChain', 'PostgreSQL', 'Redis', 'ChromaDB', 'DashScope'].map((tech) => (
              <span key={tech} className="px-2.5 py-1 text-xs rounded-full bg-blue-50 text-blue-600 font-medium">
                {tech}
              </span>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-[var(--color-text)] mb-3">功能特性</h3>
          <ul className="space-y-2">
            {[
              'AI 智能对话 — 基于大语言模型的自然语言问答',
              '知识库管理 — 文档上传、向量检索、智能分段',
              '用户系统 — 注册登录、个人信息管理、JWT 认证',
              '会话管理 — 历史对话保存与回顾',
            ].map((text) => (
              <li key={text} className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                {text}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}