import { NavLink, useNavigate } from 'react-router-dom'
import {
  MessageSquare,
  History,
  Settings,
  User,
  Info,
  LogOut,
  Columns2,
  LibraryBig,
  Sparkles,
} from 'lucide-react'
import { useUserStore } from '../../stores/useUserStore'

const navItems = [
  { path: '/chat', icon: MessageSquare, label: 'AI 对话' },
  { path: '/knowledge', icon: LibraryBig, label: '知识库' },
  { path: '/sessions', icon: History, label: '历史会话' },
]

const bottomItems = [
  { path: '/profile', icon: User, label: '个人信息' },
  { path: '/settings', icon: Settings, label: '设置' },
  { path: '/about', icon: Info, label: '关于' },
]

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const navigate = useNavigate()
  const logout = useUserStore((s) => s.logout)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside
      className={`flex flex-col border-r border-[var(--color-border)] bg-[var(--color-card)] shrink-0 transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-60'
      }`}
    >
      <div className="flex items-center justify-between px-5 h-16">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
              <Sparkles size={14} className="text-white" />
            </div>
            <h1 className="text-base font-bold text-[var(--color-text)] truncate">小易问答助手</h1>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg text-[var(--color-text-tertiary)] hover:bg-[var(--color-bg-secondary)] hover:text-[var(--color-text-secondary)] transition-colors"
          title={collapsed ? '展开侧栏' : '收起侧栏'}
        >
          <Columns2
            size={18}
            className={`transition-transform duration-300 ${collapsed ? 'rotate-180' : ''}`}
          />
        </button>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/chat'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-[var(--color-accent-bg)] text-[var(--color-accent)] font-medium'
                  : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] hover:text-[var(--color-text)]'
              } ${collapsed ? 'justify-center' : ''}`
            }
            title={collapsed ? label : undefined}
          >
            <Icon size={18} />
            {!collapsed && label}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-3 border-t border-[var(--color-border)] space-y-1">
        {bottomItems.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-[var(--color-accent-bg)] text-[var(--color-accent)] font-medium'
                  : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] hover:text-[var(--color-text)]'
              } ${collapsed ? 'justify-center' : ''}`
            }
            title={collapsed ? label : undefined}
          >
            <Icon size={18} />
            {!collapsed && label}
          </NavLink>
        ))}
        <button
          onClick={handleLogout}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm w-full text-[var(--color-text-secondary)] hover:bg-red-50 hover:text-red-600 transition-colors ${
            collapsed ? 'justify-center' : ''
          }`}
          title={collapsed ? '退出登录' : undefined}
        >
          <LogOut size={18} />
          {!collapsed && '退出登录'}
        </button>
      </div>
    </aside>
  )
}