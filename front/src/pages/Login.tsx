import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Eye, EyeOff, LogIn } from 'lucide-react'
import { authApi } from '../api/auth'
import { useUserStore } from '../stores/useUserStore'
import logoImg from '/assets/images/logo.png'

export default function Login() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const login = useUserStore((s) => s.login)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !password) {
      setError(t('auth.fillUsernameAndPassword'))
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await authApi.login(username, password)
      login(res.token, res.user)
      navigate('/chat')
    } catch (err: unknown) {
      const detail = (err as { detail?: string })?.detail
      setError(detail || t('auth.loginFailed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <img
          src={logoImg}
          alt="小艺问答助手"
          className="mx-auto w-16 h-16 rounded-xl object-cover shadow-md mb-3"
        />
        <h1 className="text-xl font-bold text-[var(--color-text)]">{t('app.name')}</h1>
        <p className="mt-1 text-sm text-[var(--color-text-tertiary)]">{t('auth.loginTitle')}</p>
      </div>

      <form onSubmit={handleLogin} className="space-y-4">
        {error && (
          <div className="px-4 py-2.5 rounded-lg text-sm bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800">
            {error}
          </div>
        )}

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">{t('auth.username')}</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] focus:outline-none focus:ring-2 focus:ring-rose-400 focus:border-transparent transition-all"
            placeholder={t('auth.usernamePlaceholder')}
          />
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-[var(--color-text)]">{t('auth.password')}</label>
          <div className="relative">
            <input
              type={showPwd ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 pr-10 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-placeholder)] focus:outline-none focus:ring-2 focus:ring-rose-400 focus:border-transparent transition-all"
              placeholder={t('auth.passwordPlaceholder')}
            />
            <button
              type="button"
              onClick={() => setShowPwd(!showPwd)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)]"
            >
              {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-rose-400 to-pink-500 text-white text-sm font-medium hover:from-rose-500 hover:to-pink-600 disabled:opacity-50 transition-all shadow-md shadow-rose-200"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <LogIn size={16} />
          )}
          {t('auth.login')}
        </button>
      </form>

      <p className="text-center text-sm text-[var(--color-text-tertiary)]">
        {t('auth.noAccount')}{' '}
        <Link to="/register" className="text-rose-500 hover:underline font-medium">
          {t('auth.toRegister')}
        </Link>
      </p>
    </div>
  )
}