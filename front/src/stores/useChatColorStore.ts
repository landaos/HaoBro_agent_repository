import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface ChatColorPreset {
  name: string
  value: string
}

export const CHAT_COLOR_PRESETS: ChatColorPreset[] = [
  { name: '白色', value: '#ffffff' },
  { name: '金色', value: '#ffd700' },
  { name: '玫瑰金', value: '#e8a87c' },
  { name: '橙色', value: '#ffa500' },
  { name: '浅粉', value: '#ffb6c1' },
  { name: '薄荷绿', value: '#98fb98' },
  { name: '天蓝', value: '#87ceeb' },
  { name: '薰衣草', value: '#e6e6fa' },
]

interface ChatColorState {
  chatColor: string
  setChatColor: (color: string) => void
}

export const useChatColorStore = create<ChatColorState>()(
  persist(
    (set) => ({
      chatColor: '#ffffff',
      setChatColor: (chatColor) => set({ chatColor }),
    }),
    { name: 'chat-color' }
  )
)