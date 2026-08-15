import { endpoints } from './endpoints'

function getToken() {
  return localStorage.getItem('jwt_token') || ''
}

async function request(url: string, options: RequestInit = {}) {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> || {}),
  }
  const res = await fetch(url, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '请求失败' }))
    throw { status: res.status, ...err }
  }
  return res.json()
}

export const authApi = {
  login: async (username: string, password: string) => {
    return request(endpoints.userLogin, {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },

  register: async (data: { username: string; email: string; password: string; confirm_password: string; phone?: string }) => {
    return request(endpoints.userRegister, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  logout: async () => {
    return request(endpoints.userLogout, { method: 'POST' })
  },

  getProfile: async () => {
    return request(endpoints.userDetail)
  },

  updateProfile: async (data: Record<string, unknown>) => {
    return request(endpoints.userUpdate, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  updatePassword: async (old_password: string, new_password: string, confirm_password: string) => {
    return request(endpoints.userResetPassword, {
      method: 'POST',
      body: JSON.stringify({ old_password, new_password, confirm_password }),
    })
  },
}