import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import Sidebar from '../components/layout/Sidebar'
import { useUserStore } from '../stores/useUserStore'

// 页面背景图映射
const pageBackgrounds: Record<string, string> = {
  '/chat': '/assets/images/美人2.png',
  '/knowledge': '/assets/images/美人1.png',
  '/sessions': '/assets/images/美人3.png',
  '/profile': '/assets/images/美人4.png',
  '/settings': '/assets/images/美人4.png',
  '/about': '/assets/images/美人4.png',
}

export default function MainLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const isLogin = useUserStore((s) => s.isLogin)

  useEffect(() => {
    if (!isLogin) {
      navigate('/login', { replace: true })
    }
  }, [isLogin, navigate])

  if (!isLogin) return null

  // 匹配当前路径的背景图
  const bgImage = Object.entries(pageBackgrounds).find(([path]) =>
    location.pathname.startsWith(path)
  )?.[1]

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-bg)]">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
      />
      <main
        className="flex-1 overflow-y-auto relative"
        style={
          bgImage
            ? {
                backgroundImage: `url(${bgImage})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundAttachment: 'fixed',
              }
            : undefined
        }
      >
        {/* 仅聊天页完全无遮罩，其他页面保留轻遮罩 */}
        {bgImage && !location.pathname.startsWith('/chat') && (
          <div className="absolute inset-0 bg-white/40 pointer-events-none" />
        )}
        <div className="relative z-10 h-full">
          <Outlet />
        </div>
      </main>
    </div>
  )
}