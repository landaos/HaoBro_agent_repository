import { useState, useEffect } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import Sidebar from '../components/layout/Sidebar'
import { useUserStore } from '../stores/useUserStore'

export default function MainLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const navigate = useNavigate()
  const isLogin = useUserStore((s) => s.isLogin)

  useEffect(() => {
    if (!isLogin) {
      navigate('/login', { replace: true })
    }
  }, [isLogin, navigate])

  if (!isLogin) return null

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-bg)]">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
      />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}