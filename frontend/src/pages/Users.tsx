import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import api from '../api/client'
import Modal from '../components/Modal'

export default function Users() {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const empty = { email: '', full_name: '', phone: '', role: 'manager', branch_id: null, password: '', is_active: true }
  const [form, setForm] = useState<any>(empty)
  const [editing, setEditing] = useState<any>(null)

  const { data: list } = useQuery<any[]>({
    queryKey: ['users'], queryFn: async () => (await api.get('/users')).data,
  })
  const { data: branches } = useQuery<any[]>({
    queryKey: ['branches'], queryFn: async () => (await api.get('/branches')).data,
  })
  const save = useMutation({
    mutationFn: async () => editing
      ? (await api.put(`/users/${editing.id}`, form)).data
      : (await api.post('/users', form)).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }); setOpen(false); setEditing(null); setForm(empty) },
  })

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Сотрудники</h1>
        <button className="btn-primary" onClick={() => { setEditing(null); setForm(empty); setOpen(true) }}>+ Добавить</button>
      </div>
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="table">
          <thead><tr><th>Email</th><th>ФИО</th><th>Телефон</th><th>Роль</th><th>Филиал</th><th>Активен</th><th></th></tr></thead>
          <tbody>
            {(list ?? []).map((u) => (
              <tr key={u.id}>
                <td>{u.email}</td><td>{u.full_name}</td><td>{u.phone}</td>
                <td><span className="text-xs uppercase">{u.role}</span></td>
                <td>{branches?.find((b: any) => b.id === u.branch_id)?.name ?? '—'}</td>
                <td>{u.is_active ? '✓' : '—'}</td>
                <td className="text-right">
                  <button className="text-brand-600 text-sm" onClick={() => { setEditing(u); setForm({ ...u, password: '' }); setOpen(true) }}>править</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Modal open={open} onClose={() => setOpen(false)} title={editing ? 'Редактирование сотрудника' : 'Новый сотрудник'}
        footer={<div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setOpen(false)}>Отмена</button>
          <button className="btn-primary" onClick={() => save.mutate()}>Сохранить</button>
        </div>}>
        <input className="input" placeholder="email" disabled={!!editing} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input className="input" placeholder="ФИО" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        <input className="input" placeholder="Телефон" value={form.phone || ''} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        <div className="grid grid-cols-2 gap-3">
          <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            <option value="admin">admin</option>
            <option value="manager">manager</option>
            <option value="warehouse">warehouse</option>
            <option value="master">master</option>
            <option value="accountant">accountant</option>
          </select>
          <select className="input" value={form.branch_id ?? ''} onChange={(e) => setForm({ ...form, branch_id: e.target.value ? +e.target.value : null })}>
            <option value="">— филиал —</option>
            {(branches ?? []).map((b: any) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </div>
        <input className="input" type="password" placeholder={editing ? 'новый пароль (если меняется)' : 'пароль'} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <label className="text-sm flex items-center gap-2"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Активен</label>
      </Modal>
    </div>
  )
}
