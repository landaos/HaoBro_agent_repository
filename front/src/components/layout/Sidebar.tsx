import { NavLink, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { MessageSquare, History, Settings, User, Info, LogOut, Columns2, LibraryBig } from 'lucide-react'
import { useUserStore } from '../../stores/useUserStore'
import logoImg from '/assets/images/logo.png'

const navItems = [
  { path: '/chat', icon: MessageSquare, label: 'nav.chat' },
  { path: '/knowledge', icon: LibraryBig, label: 'nav.knowledge' },
  { path: '/sessions', icon: History, label: 'nav.sessions' },
]

const bottomItems = [
  { path: '/profile', icon: User, label: 'nav.profile' },
  { path: '/settings', icon: Settings, label: 'nav.settings' },
  { path: '/about', icon: Info, label: 'nav.about' },
]

interface SidebarProps { collapsed: boolean; onToggle: () => void }

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const logout = useUserStore((s) => s.logout)

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <aside className={`flex flex-col border-r border-[var(--color-border)] bg-[var(--color-card)]/90 backdrop-blur-md shrink-0 transition-all duration-300 ${collapsed ? 'w-16' : 'w-60'}`}>
      <div className="flex items-center justify-between px-5 h-16">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <img src={logoImg} alt="logo" className="w-7 h-7 rounded-lg object-cover" />
            <h1 className="text-base font-bold text-[var(--color-text)] truncate">{t('app.name')}</h1>
          </div>
        )}
        <button onClick={onToggle} className="p-1.5 rounded-lg text-[var(--color-text-tertiary)] hover:bg-[var(--color-bg-secondary)] hover:text-[var(--color-text-secondary)] transition-colors"
          title={collapsed ? t('nav.expand') : t('nav.collapse')}>
          <Columns2 size={18} className={`transition-transform duration-300 ${collapsed ? 'rotate-180' : ''}`} />
        </button>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink key={path} to={path} end={path === '/chat'}
            className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${isActive ? 'bg-[var(--color-accent-bg)] text-[var(--color-accent)] font-medium' : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] hover:text-[var(--color-text)]'} ${collapsed ? 'justify-center' : ''}`}
            title={collapsed ? t(label) : undefined}>
            <Icon size={18} />{!collapsed && t(label)}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-3 border-t border-[var(--color-border)] space-y-1">
        {bottomItems.map(({ path, icon: Icon, label }) => (
          <NavLink key={path} to={path}
            className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${isActive ? 'bg-[var(--color-accent-bg)] text-[var(--color-accent)] font-medium' : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] hover:text-[var(--color-text)]'} ${collapsed ? 'justify-center' : ''}`}
            title={collapsed ? t(label) : undefined}>
            <Icon size={18} />{!collapsed && t(label)}
          </NavLink>
        ))}
        <button onClick={handleLogout}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm w-full text-[var(--color-text-secondary)] hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 transition-colors ${collapsed ? 'justify-center' : ''}`}
          title={collapsed ? t('nav.logout') : undefined}>
          <LogOut size={18} />{!collapsed && t('nav.logout')}
        </button>
      </div>
    </aside>
  )
}