import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { UserPlus } from 'lucide-react'
import { authApi } from '../api/auth'
import { useUserStore } from '../stores/useUserStore'
import logoImg from '/assets/images/logo.png'

export default function Register() {
  const { t } = useTranslation()
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
      setError(t('auth.fillRequired'))
      return
    }
    if (form.password !== form.confirmPassword) {
      setError(t('auth.passwordMismatch'))
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
      setError(detail || t('auth.registerFailed'))
    } finally {
      setLoading(false)
    }
  }

  const inputClass = 'w-full px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] focus:outline-none focus:ring-2 focus:ring-rose-400 focus:border-transparent transition-all'

  return (
    <div className="space-y-6">
      <div className="text-center">
        <img
          src={logoImg}
          alt="小艺问答助手"
          className="mx-auto w-16 h-16 rounded-xl object-cover shadow-md mb-3"
        />
        <h1 className="text-xl font-bold text-[var(--color-text)]">{t('auth.createAccount')}</h1>
        <p className="mt-1 text-sm text-[var(--color-text-tertiary)]">{t('auth.registerTitle')}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="px-4 py-2.5 rounded-lg text-sm bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800">
            {error}
          </div>
        )}

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">
            {t('auth.username')} <span className="text-red-500">*</span>
          </label>
          <input type="text" value={form.username} onChange={(e) => handleChange('username', e.target.value)} className={inputClass} placeholder={t('auth.usernamePlaceholder')} />
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">
            {t('auth.email')} <span className="text-red-500">*</span>
          </label>
          <input type="email" value={form.email} onChange={(e) => handleChange('email', e.target.value)} className={inputClass} placeholder={t('auth.emailPlaceholder')} />
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">{t('auth.phone')}</label>
          <input type="tel" value={form.phone} onChange={(e) => handleChange('phone', e.target.value)} className={inputClass} placeholder={t('auth.phonePlaceholder')} />
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">
            {t('auth.password')} <span className="text-red-500">*</span>
          </label>
          <input type="password" value={form.password} onChange={(e) => handleChange('password', e.target.value)} className={inputClass} placeholder={t('auth.passwordMinPlaceholder')} />
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">
            {t('auth.confirmPassword')} <span className="text-red-500">*</span>
          </label>
          <input type="password" value={form.confirmPassword} onChange={(e) => handleChange('confirmPassword', e.target.value)} className={inputClass} placeholder={t('auth.confirmPasswordPlaceholder')} />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-rose-400 to-pink-500 text-white text-sm font-medium hover:from-rose-500 hover:to-pink-600 disabled:opacity-50 transition-all shadow-md shadow-rose-200"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <UserPlus size={16} />
          )}
          {t('auth.register')}
        </button>
      </form>

      <p className="text-center text-sm text-[var(--color-text-tertiary)]">
        {t('auth.hasAccount')}{' '}
        <Link to="/login" className="text-rose-500 hover:underline font-medium">
          {t('auth.toLogin')}
        </Link>
      </p>
    </div>
  )
}