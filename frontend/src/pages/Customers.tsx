import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import api from '../api/client'
import Modal from '../components/Modal'

export default function Customers() {
  const qc = useQueryClient()
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const empty = { full_name: '', phone: '', extra_phone: '', email: '', inn: '', address: '', notes: '', kind: 'individual', discount_pct: 0, blacklist: false }
  const [form, setForm] = useState<any>(empty)

  const { data: list } = useQuery<any[]>({
    queryKey: ['customers', q],
    queryFn: async () => (await api.get('/customers', { params: { q: q || undefined } })).data,
  })

  const save = useMutation({
    mutationFn: async () => editing
      ? (await api.put(`/customers/${editing.id}`, form)).data
      : (await api.post('/customers', form)).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['customers'] }); setOpen(false); setEditing(null); setForm(empty) },
  })
  const del = useMutation({
    mutationFn: async (id: number) => (await api.delete(`/customers/${id}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['customers'] }),
  })

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Клиенты</h1>
        <button className="btn-primary" onClick={() => { setForm(empty); setEditing(null); setOpen(true) }}>+ Добавить</button>
      </div>
      <input className="input mb-3 max-w-sm" placeholder="Поиск..." value={q} onChange={(e) => setQ(e.target.value)} />
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="table">
          <thead><tr><th>Имя</th><th>Телефон</th><th>Email</th><th>Скидка</th><th>Тип</th><th></th></tr></thead>
          <tbody>
            {(list ?? []).map((c) => (
              <tr key={c.id}>
                <td>{c.full_name}</td>
                <td>{c.phone}</td>
                <td>{c.email}</td>
                <td>{Number(c.discount_pct).toFixed(0)}%</td>
                <td>{c.kind === 'legal' ? 'Юр.' : 'Физ.'}</td>
                <td className="text-right">
                  <button className="text-brand-600 text-sm mr-3" onClick={() => { setEditing(c); setForm(c); setOpen(true) }}>править</button>
                  <button className="text-red-600 text-sm" onClick={() => confirm('Удалить?') && del.mutate(c.id)}>удалить</button>
                </td>
              </tr>
            ))}
            {!list?.length && <tr><td colSpan={6} className="text-center text-slate-500 py-8">Нет клиентов</td></tr>}
          </tbody>
        </table>
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title={editing ? 'Редактирование клиента' : 'Новый клиент'}
        footer={<div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setOpen(false)}>Отмена</button>
          <button className="btn-primary" onClick={() => save.mutate()} disabled={!form.full_name}>Сохранить</button>
        </div>}>
        <input className="input" placeholder="ФИО / Название" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        <div className="grid grid-cols-2 gap-3">
          <input className="input" placeholder="Телефон" value={form.phone || ''} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <input className="input" placeholder="Доп. телефон" value={form.extra_phone || ''} onChange={(e) => setForm({ ...form, extra_phone: e.target.value })} />
          <input className="input" placeholder="Email" value={form.email || ''} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="input" placeholder="ИНН" value={form.inn || ''} onChange={(e) => setForm({ ...form, inn: e.target.value })} />
        </div>
        <textarea className="input" rows={2} placeholder="Адрес" value={form.address || ''} onChange={(e) => setForm({ ...form, address: e.target.value })} />
        <textarea className="input" rows={2} placeholder="Заметки" value={form.notes || ''} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        <div className="grid grid-cols-2 gap-3">
          <select className="input" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
            <option value="individual">Физ. лицо</option>
            <option value="legal">Юр. лицо</option>
          </select>
          <input className="input" type="number" min={0} max={100} placeholder="Скидка %"
            value={form.discount_pct ?? 0} onChange={(e) => setForm({ ...form, discount_pct: +e.target.value })} />
        </div>
      </Modal>
    </div>
  )
}
