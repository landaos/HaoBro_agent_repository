import { Outlet } from 'react-router-dom'
import loginBg from '/assets/images/登录界面 .png'

export default function AuthLayout() {
  return (
    <div
      className="min-h-screen flex items-center bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: `url(${loginBg})` }}
    >
      {/* 登录卡片 — 居中偏右，盖住背景图中的登录区域 */}
      <div className="w-full flex justify-end -mt-7" style={{ paddingRight: 'calc(15% + 6px)', marginTop: 'calc(-1.625rem + 17px)' }}>
        <div className="w-full max-w-md bg-white/90 dark:bg-gray-900/90 rounded-2xl shadow-2xl p-8">
          <Outlet />
        </div>
      </div>
    </div>
  )
}