import { useEffect, useState } from 'react'
import { Lock, Save, X, Eye, EyeOff, User } from 'lucide-react'
import * as Dialog from '@radix-ui/react-dialog'
import { authApi } from '../api/auth'
import { useUserStore } from '../stores/useUserStore'
import type { UserInfo } from '../types/api'

export default function Profile() {
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
        setMessage('保存成功')
      }
      setEditing(false)
    } catch {
      setMessage('保存失败')
    } finally {
      setLoading(false)
      setTimeout(() => setMessage(''), 2000)
    }
  }

  const handlePasswordChange = async () => {
    const { oldPassword, newPassword, confirmPassword } = pwdForm
    if (!oldPassword || !newPassword || !confirmPassword) {
      setPwdError('请填写所有字段')
      return
    }
    if (newPassword.length < 6) {
      setPwdError('密码长度至少6位')
      return
    }
    if (newPassword === oldPassword) {
      setPwdError('新密码不能与原密码相同')
      return
    }
    if (newPassword !== confirmPassword) {
      setPwdError('两次输入的新密码不一致')
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
      setMessage('密码修改成功')
      setTimeout(() => setMessage(''), 2000)
    } catch (err: unknown) {
      const detail = (err as { detail?: string })?.detail
      setPwdError(detail || '密码修改失败')
    } finally {
      setPwdLoading(false)
    }
  }

  const genderLabel = (g: number) => {
    if (g === 1) return '男'
    if (g === 2) return '女'
    return '未知'
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-[var(--color-text)]">个人信息</h1>
        {!editing ? (
          <button onClick={() => setEditing(true)} className="px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] transition-colors">
            编辑
          </button>
        ) : (
          <div className="flex gap-2">
            <button onClick={() => setEditing(false)} className="px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] transition-colors">
              <X size={14} className="inline mr-1" />取消
            </button>
            <button onClick={handleSave} disabled={loading} className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors">
              <Save size={14} className="inline mr-1" />保存
            </button>
          </div>
        )}
      </div>

      {message && (
        <div className="mb-4 px-4 py-2 rounded-lg text-sm bg-green-50 text-green-700 border border-green-200">{message}</div>
      )}

      <div className="bg-[var(--color-card)] rounded-xl border border-[var(--color-border)] divide-y divide-[var(--color-border)]">
        <div className="flex items-center gap-4 p-6">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xl font-bold">
            {userInfo?.username ? userInfo.username[0].toUpperCase() : <User size={24} />}
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--color-text)]">{userInfo?.username || '-'}</p>
            <p className="text-xs text-[var(--color-text-tertiary)]">{userInfo?.email || '-'}</p>
          </div>
        </div>

        <div className="flex items-center justify-between px-6 py-4">
          <span className="text-sm text-[var(--color-text-tertiary)]">用户名</span>
          {editing ? (
            <input
              value={form.username}
              onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
              className="w-48 px-3 py-1.5 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
            />
          ) : (
            <span className="text-sm text-[var(--color-text)]">{form.username || '-'}</span>
          )}
        </div>

        <div className="flex items-center justify-between px-6 py-4">
          <span className="text-sm text-[var(--color-text-tertiary)]">邮箱</span>
          <span className="text-sm text-[var(--color-text)]">{form.email || '-'}</span>
        </div>

        <div className="flex items-center justify-between px-6 py-4">
          <span className="text-sm text-[var(--color-text-tertiary)]">手机号</span>
          {editing ? (
            <input
              value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              className="w-48 px-3 py-1.5 text-sm rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
            />
          ) : (
            <span className="text-sm text-[var(--color-text)]">{form.phone || '-'}</span>
          )}
        </div>

        <div className="flex items-center justify-between px-6 py-4">
          <span className="text-sm text-[var(--color-text-tertiary)]">性别</span>
          {editing ? (
            <div className="flex gap-3">
              {[{ value: 1, label: '男' }, { value: 2, label: '女' }].map((g) => (
                <label key={g.value} className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name="gender"
                    value={g.value}
                    checked={form.gender === g.value}
                    onChange={(e) => setForm((f) => ({ ...f, gender: Number(e.target.value) }))}
                    className="text-blue-600"
                  />
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
        修改密码
      </button>

      <Dialog.Root open={pwdOpen} onOpenChange={(open) => { setPwdOpen(open); if (!open) setPwdError('') }}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/40" />
          <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-[var(--color-card)] rounded-xl shadow-xl p-6 w-[420px] max-w-[90vw]">
            <div className="flex items-center justify-between mb-5">
              <Dialog.Title className="text-base font-medium text-[var(--color-text)]">修改密码</Dialog.Title>
              <Dialog.Close className="text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)]">
                <X size={16} />
              </Dialog.Close>
            </div>

            {pwdError && (
              <div className="mb-4 px-4 py-2 rounded-lg text-sm bg-red-50 text-red-600 border border-red-200">
                {pwdError}
              </div>
            )}

            <div className="space-y-4">
              {(['oldPassword', 'newPassword', 'confirmPassword'] as const).map((field) => (
                <div key={field} className="space-y-1.5">
                  <label className="block text-sm text-[var(--color-text-secondary)]">
                    {field === 'oldPassword' ? '原密码' : field === 'newPassword' ? '新密码' : '确认新密码'}
                  </label>
                  <div className="relative">
                    <input
                      type={showPwd[field === 'oldPassword' ? 'old' : field === 'newPassword' ? 'new' : 'confirm'] ? 'text' : 'password'}
                      value={pwdForm[field]}
                      onChange={(e) => setPwdForm((f) => ({ ...f, [field]: e.target.value }))}
                      className="w-full px-4 py-2.5 pr-10 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-sm text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
                      placeholder={field === 'oldPassword' ? '输入原密码' : field === 'newPassword' ? '输入新密码' : '再次输入新密码'}
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
              <Dialog.Close className="px-4 py-2 text-sm rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] transition-colors">取消</Dialog.Close>
              <button
                onClick={handlePasswordChange}
                disabled={pwdLoading}
                className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {pwdLoading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Lock size={14} />}
                确认修改
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  )
}