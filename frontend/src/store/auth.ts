import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface User {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'manager' | 'warehouse' | 'master' | 'accountant'
  branch_id?: number | null
  is_active: boolean
}

interface AuthState {
  token: string | null
  user: User | null
  setAuth: (t: string, u: User) => void
  logout: () => void
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'service-crm-auth' },
  ),
)

export const can = (role: User['role'] | undefined, allowed: User['role'][]) =>
  !!role && allowed.includes(role)
