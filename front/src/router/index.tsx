import { lazy, Suspense } from 'react'
import type { RouteObject } from 'react-router-dom'
import MainLayout from '../layouts/MainLayout'
import AuthLayout from '../layouts/AuthLayout'

const Login = lazy(() => import('../pages/Login'))
const Register = lazy(() => import('../pages/Register'))
const AIChat = lazy(() => import('../pages/AIChat'))
const Sessions = lazy(() => import('../pages/Sessions'))
const Profile = lazy(() => import('../pages/Profile'))
const Settings = lazy(() => import('../pages/Settings'))
const AboutUs = lazy(() => import('../pages/AboutUs'))
const KnowledgeBase = lazy(() => import('../pages/KnowledgeBase'))

const LazyLoad = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={
    <div className="flex items-center justify-center h-full py-20 text-[var(--color-text-tertiary)] text-sm">
      加载中...
    </div>
  }>{children}</Suspense>
)

const routes: RouteObject[] = [
  {
    path: '/login',
    element: <AuthLayout />,
    children: [{ index: true, element: <LazyLoad><Login /></LazyLoad> }],
  },
  {
    path: '/register',
    element: <AuthLayout />,
    children: [{ index: true, element: <LazyLoad><Register /></LazyLoad> }],
  },
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <LazyLoad><AIChat /></LazyLoad> },
      { path: 'chat', element: <LazyLoad><AIChat /></LazyLoad> },
      { path: 'chat/:sessionId', element: <LazyLoad><AIChat /></LazyLoad> },
      { path: 'sessions', element: <LazyLoad><Sessions /></LazyLoad> },
      { path: 'profile', element: <LazyLoad><Profile /></LazyLoad> },
      { path: 'settings', element: <LazyLoad><Settings /></LazyLoad> },
      { path: 'about', element: <LazyLoad><AboutUs /></LazyLoad> },
      { path: 'knowledge', element: <LazyLoad><KnowledgeBase /></LazyLoad> },
    ],
  },
]

export default routes
