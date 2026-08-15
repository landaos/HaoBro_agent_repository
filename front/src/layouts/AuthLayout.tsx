import { Outlet } from 'react-router-dom'

export default function AuthLayout() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)]">
      <div className="w-full max-w-md mx-auto p-8">
        <div className="bg-[var(--color-card)] rounded-2xl shadow-lg border border-[var(--color-border)] p-8">
          <Outlet />
        </div>
      </div>
    </div>
  )
}