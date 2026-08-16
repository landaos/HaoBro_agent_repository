import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Lock, Save, X, Eye, EyeOff, User } from 'lucide-react'
import * as Dialog from '@radix-ui/react-dialog'
import { authApi } from '../api/auth'
import { useUserStore } from '../stores/useUserStore'
import type { UserInfo } from '../types/api'

export default function Profile() {
  const { t } = useTranslation()
  const { userInfo, setUserInfo, token } = useUserStore()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ username: '', email: '', phone: '', gender: 0 })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const [pwdOpen, setPwdOpen] = useState(false)
  const [pwdForm, setPwdForm] = useState({ oldPassword: '', newPassword: '', confirmPassword: '' })
  const [showPwd, setShowPwd] = useState({ old: false, new: false, confirm: false })
  const [pwdLoading, setPwdLoading] = useState(false)
  const [pwdError, setPwdError] = useState('')

  useEffect(() => {
    if (token) {
      authApi.getProfile().then((res) => {
        const data = (res.data || res) as UserInfo | undefined
        if (data) {
          setUserInfo({
            user_id: data.user_id,
            username: data.username || '',
            email: data.email || '',
            phone: data.phone || '',
            gender: data.gender ?? 0,
            status: data.status,
            created_at: data.created_at,
            updated_at: data.updated_at,
          })
        }
      }).catch(() => {})
    }
  }, [token])

  useEffect(() => {
    if (userInfo) {
      setForm({
        username: userInfo.username || '',
        email: userInfo.email || '',
        phone: userInfo.phone || '',
        gender: userInfo.gender ?? 0,
      })
    }
  }, [userInfo])

  const handleSave = async () => {
    setLoading(true)
    try {
      const payload: Record<string, unknown> = {}
      if (form.username) payload.username = form.username
      if (form.phone) payload.phone = form.phone
      if (form.gender) payload.gender = form.gender
      const res = await authApi.updateProfile(payload)
      const newToken = (res as { token?: string }).token
      if (newToken) {
        useUserStore.getState().setToken(newToken)
      }
      const userField = (res as { user?: Record<string, unknown> }).user
      if (userField) {
        setUserInfo({
          user_id: (userField.user_id as string) || userInfo?.user_id,
          username: (userField.username as string) || form.username,
          email: (userField.email as string) || form.email,
          phone: (userField.phone as string) || form.phone,
          gender: (userField.gender as number) ?? form.gender,
        })
        setMessage(t('profile.saveSuccess'))
      }
      setEditing(false)
    } catch {
      setMessage(t('profile.saveFailed'))
    } finally {
      setLoading(false)
      setTimeout(() => setMessage(''), 2000)
    }
  }

  const handlePasswordChange = async () => {
    const { oldPassword, newPassword, confirmPassword } = pwdForm
    if (!oldPassword || !newPassword || !confirmPassword) {
      setPwdError(t('profile.fillAllFields'))
      return
    }
    if (newPassword.length < 6) {
      setPwdError(t('profile.passwordMinLength'))
      return
    }
    if (newPassword === oldPassword) {
      setPwdError(t('profile.samePassword'))
      return
    }
    if (newPassword !== confirmPassword) {
      setPwdError(t('profile.passwordMismatch'))
      return
    }
    setPwdLoading(true)
    setPwdError('')
    try {
      const res = await authApi.updatePassword(oldPassword, newPassword, confirmPassword)
      if (res.token) {
        useUserStore.getState().setToken(res.token)
      }
      setPwdOpen(false)
      setPwdForm({ oldPassword: '', newPassword: '', confirmPassword: '' })
      setMessage(t('profile.passwordChanged'))
      setTimeout(() => setMessage(''), 2000)
    } catch (err: unknown) {
      const detail = (err as { detail?: string })?.detail
      setPwdError(detail || t('profile.passwordError'))
    } finally {
      setPwdLoading(false)
    }
  }

  const genderLabel = (g: number) => {
    if (g === 1) return t('profile.male')
    if (g === 2) return t('profile.female')
    return t('profile.unknown')
  }

  const inputClass = 'w-48 px-3 py-1.5 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]'

  return (
    <div className="max-w-2xl mx-auto py-8 px-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-[var(--color-text)]">{t('profile.title')}</h1>
        {!editing ? (
          <button onClick={() => setEditing(true)} className="px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] transition-colors">
            {t('profile.edit')}
          </button>
        ) : (
          <div className="flex gap-2">
            <button onClick={() => setEditing(false)} className="px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] transition-colors">
              <X size={14} className="inline mr-1" />{t('profile.cancel')}
            </button>
            <button onClick={handleSave} disabled={loading} className="px-4 py-2 text-sm rounded-lg bg-rose-400 text-white hover:bg-rose-500 disabled:opacity-50 transition-colors">
              <Save size={14} className="inline mr-1" />{t('profile.save')}
            </button>
          </div>
        )}
      </div>

      {message && (
        <div className="mb-4 px-4 py-2 rounded-lg text-sm bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800">{message}</div>
      )}

      <div className="bg-[var(--color-card)] rounded-xl border border-[var(--color-border)] divide-y divide-[var(--color-border)]">
        <div className="flex items-center gap-4 p-6">
          <div className="w-16 h-16 rounded-full bg-rose-100 dark:bg-rose-900/40 flex items-center justify-center text-rose-500 dark:text-rose-300 text-xl font-bold">
            {userInfo?.username ? userInfo.username[0].toUpperCase() : <User size={24} />}
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--color-text)]">{userInfo?.username || '-'}</p>
            <p className="text-xs text-[var(--color-text-tertiary)]">{userInfo?.email || '-'}</p>
          </div>
        </div>

        <div className="flex items-center justify-between px-6 py-4">
          <span className="text-sm text-[var(--color-text-tertiary)]">{t('profile.username')}</span>
          {editing ? (
            <input value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} className={inputClass} />
          ) : (
            <span className="text-sm text-[var(--color-text)]">{form.username || '-'}</span>
          )}
        </div>

        <div className="flex items-center justify-between px-6 py-4">
          <span className="text-sm text-[var(--color-text-tertiary)]">{t('profile.email')}</span>
          <span className="text-sm text-[var(--color-text)]">{form.email || '-'}</span>
        </div>

        <div className="flex items-center justify-between px-6 py-4">
          <span className="text-sm text-[var(--color-text-tertiary)]">{t('profile.phone')}</span>
          {editing ? (
            <input value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} className={inputClass} />
          ) : (
            <span className="text-sm text-[var(--color-text)]">{form.phone || '-'}</span>
          )}
        </div>

        <div className="flex items-center justify-between px-6 py-4">
          <span className="text-sm text-[var(--color-text-tertiary)]">{t('profile.gender')}</span>
          {editing ? (
            <div className="flex gap-3">
              {[{ value: 1, label: t('profile.male') }, { value: 2, label: t('profile.female') }].map((g) => (
                <label key={g.value} className="flex items-center gap-1.5 cursor-pointer">
                  <input type="radio" name="gender" value={g.value} checked={form.gender === g.value} onChange={(e) => setForm((f) => ({ ...f, gender: Number(e.target.value) }))} className="text-rose-500" />
                  <span className="text-sm text-[var(--color-text)]">{g.label}</span>
                </label>
              ))}
            </div>
          ) : (
            <span className="text-sm text-[var(--color-text)]">{genderLabel(form.gender)}</span>
          )}
        </div>
      </div>

      <button
        onClick={() => { setPwdOpen(true); setPwdError('') }}
        className="mt-6 flex items-center gap-2 px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] transition-colors"
      >
        <Lock size={14} />
        {t('profile.changePassword')}
      </button>

      <Dialog.Root open={pwdOpen} onOpenChange={(open) => { setPwdOpen(open); if (!open) setPwdError('') }}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/40 z-50" />
          <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-[var(--color-card)] rounded-xl shadow-xl p-6 w-[420px] max-w-[90vw] z-50">
            <div className="flex items-center justify-between mb-5">
              <Dialog.Title className="text-base font-medium text-[var(--color-text)]">{t('profile.changePassword')}</Dialog.Title>
              <Dialog.Close className="text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)]">
                <X size={16} />
              </Dialog.Close>
            </div>

            {pwdError && (
              <div className="mb-4 px-4 py-2 rounded-lg text-sm bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800">
                {pwdError}
              </div>
            )}

            <div className="space-y-4">
              {(['oldPassword', 'newPassword', 'confirmPassword'] as const).map((field) => (
                <div key={field} className="space-y-1.5">
                  <label className="block text-sm text-[var(--color-text-secondary)]">
                    {field === 'oldPassword' ? t('profile.oldPassword') : field === 'newPassword' ? t('profile.newPassword') : t('profile.confirmPassword')}
                  </label>
                  <div className="relative">
                    <input
                      type={showPwd[field === 'oldPassword' ? 'old' : field === 'newPassword' ? 'new' : 'confirm'] ? 'text' : 'password'}
                      value={pwdForm[field]}
                      onChange={(e) => setPwdForm((f) => ({ ...f, [field]: e.target.value }))}
                      className="w-full px-4 py-2.5 pr-10 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
                      placeholder={field === 'oldPassword' ? t('profile.oldPasswordPlaceholder') : field === 'newPassword' ? t('profile.newPasswordPlaceholder') : t('profile.confirmPasswordPlaceholder')}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPwd((s) => ({ ...s, [field === 'oldPassword' ? 'old' : field === 'newPassword' ? 'new' : 'confirm']: !s[field === 'oldPassword' ? 'old' : field === 'newPassword' ? 'new' : 'confirm'] }))}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)]"
                    >
                      {showPwd[field === 'oldPassword' ? 'old' : field === 'newPassword' ? 'new' : 'confirm'] ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <Dialog.Close className="px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] transition-colors">{t('profile.cancel')}</Dialog.Close>
              <button
                onClick={handlePasswordChange}
                disabled={pwdLoading}
                className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-rose-400 text-white hover:bg-rose-500 disabled:opacity-50 transition-colors"
              >
                {pwdLoading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Lock size={14} />}
                {t('profile.confirmModify')}
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  )
}