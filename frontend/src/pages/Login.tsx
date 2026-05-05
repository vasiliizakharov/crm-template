import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../store/auth'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const setAuth = useAuth((s) => s.setAuth)
  const nav = useNavigate()

  async function submit(e: FormEvent) {
    e.preventDefault()
    setErr(null); setBusy(true)
    try {
      const { data } = await api.post('/auth/login-json', { email, password })
      setAuth(data.access_token, data.user)
      nav('/', { replace: true })
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'Ошибка авторизации')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <form onSubmit={submit} className="bg-white rounded-lg shadow p-8 w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-bold text-center">Service CRM</h1>
        <p className="text-sm text-slate-500 text-center">Вход в систему</p>
        <input className="input" type="email" placeholder="email" value={email}
               onChange={(e) => setEmail(e.target.value)} required autoFocus />
        <input className="input" type="password" placeholder="пароль" value={password}
               onChange={(e) => setPassword(e.target.value)} required />
        {err && <div className="text-red-600 text-sm">{err}</div>}
        <button type="submit" disabled={busy} className="btn-primary w-full">
          {busy ? 'Вход...' : 'Войти'}
        </button>
      </form>
    </div>
  )
}
