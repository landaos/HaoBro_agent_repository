import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { UserPlus, Sparkles } from 'lucide-react'
import { authApi } from '../api/auth'
import { useUserStore } from '../stores/useUserStore'

export default function Register() {
  const navigate = useNavigate()
  const login = useUserStore((s) => s.login)
  const [form, setForm] = useState({
    username: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (key: string, value: string) =>
    setForm((f) => ({ ...f, [key]: value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.username || !form.password || !form.email) {
      setError('请填写必填字段')
      return
    }
    if (form.password !== form.confirmPassword) {
      setError('两次密码不一致')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await authApi.register({
        username: form.username,
        password: form.password,
        confirm_password: form.confirmPassword,
        email: form.email,
        phone: form.phone || undefined,
      })
      login(res.token, res.user)
      navigate('/chat')
    } catch (err: unknown) {
      const detail = (err as { detail?: string })?.detail
      setError(detail || '注册失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="mx-auto w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mb-3">
          <Sparkles size={22} className="text-white" />
        </div>
        <h1 className="text-xl font-bold text-[var(--color-text)]">创建账号</h1>
        <p className="mt-1 text-sm text-[var(--color-text-tertiary)]">注册小易问答助手</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="px-4 py-2.5 rounded-lg text-sm bg-red-50 text-red-600 border border-red-200">
            {error}
          </div>
        )}

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">
            用户名 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={form.username}
            onChange={(e) => handleChange('username', e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:border-transparent transition-all"
            placeholder="输入用户名"
          />
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">
            邮箱 <span className="text-red-500">*</span>
          </label>
          <input
            type="email"
            value={form.email}
            onChange={(e) => handleChange('email', e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:border-transparent transition-all"
            placeholder="输入邮箱"
          />
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">手机号</label>
          <input
            type="tel"
            value={form.phone}
            onChange={(e) => handleChange('phone', e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:border-transparent transition-all"
            placeholder="选填"
          />
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">
            密码 <span className="text-red-500">*</span>
          </label>
          <input
            type="password"
            value={form.password}
            onChange={(e) => handleChange('password', e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:border-transparent transition-all"
            placeholder="至少6位"
          />
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">
            确认密码 <span className="text-red-500">*</span>
          </label>
          <input
            type="password"
            value={form.confirmPassword}
            onChange={(e) => handleChange('confirmPassword', e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:border-transparent transition-all"
            placeholder="再次输入密码"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-sm font-medium hover:from-blue-600 hover:to-indigo-700 disabled:opacity-50 transition-all"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <UserPlus size={16} />
          )}
          注册
        </button>
      </form>

      <p className="text-center text-sm text-[var(--color-text-tertiary)]">
        已有账号？{' '}
        <Link to="/login" className="text-blue-600 hover:underline font-medium">
          去登录
        </Link>
      </p>
    </div>
  )
}