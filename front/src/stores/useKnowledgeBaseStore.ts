import { create } from 'zustand'
import { toast } from 'sonner'
import { knowledgeBaseApi } from '../api/knowledgeBases'
import type { KnowledgeBase } from '../types/api'

interface KnowledgeBaseState {
  /** 当前用户的所有知识库 */
  list: KnowledgeBase[]
  /** 当前选中的知识库 ID */
  selectedId: number | null
  /** 加载中 */
  loading: boolean

  setList: (list: KnowledgeBase[]) => void
  setSelectedId: (id: number | null) => void
  setLoading: (loading: boolean) => void

  /** 加载知识库列表 */
  fetchList: () => Promise<void>
  /** 创建知识库 */
  create: (name: string, description?: string) => Promise<KnowledgeBase>
  /** 删除知识库 */
  delete: (kbId: number) => Promise<void>
}

export const useKnowledgeBaseStore = create<KnowledgeBaseState>((set, get) => ({
  list: [],
  selectedId: null,
  loading: false,

  setList: (list) => set({ list }),
  setSelectedId: (id) => set({ selectedId: id }),
  setLoading: (loading) => set({ loading }),

  fetchList: async () => {
    set({ loading: true })
    try {
      const res = await knowledgeBaseApi.list()
      const items = res.items
      set({ list: items })
      // 校验当前选中的 ID 是否还在新列表里（如切换账号后旧 ID 已失效）
      const { selectedId } = get()
      const stillExists = items.some((k) => k.id === selectedId)
      if (!stillExists) {
        set({ selectedId: items.length > 0 ? items[0].id : null })
      }
    } catch {
      // ignore
      toast.error('加载知识库列表失败')
    } finally {
      set({ loading: false })
    }
  },

  create: async (name, description) => {
    const kb = await knowledgeBaseApi.create({ name, description })
    set((s) => ({ list: [...s.list, kb], selectedId: kb.id }))
    return kb
  },

  delete: async (kbId) => {
    await knowledgeBaseApi.delete(kbId)
    set((s) => {
      const newList = s.list.filter((k) => k.id !== kbId)
      const newSelected = s.selectedId === kbId
        ? (newList.length > 0 ? newList[0].id : null)
        : s.selectedId
      return { list: newList, selectedId: newSelected }
    })
  },
}))
