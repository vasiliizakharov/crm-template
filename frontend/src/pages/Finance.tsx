import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import api from '../api/client'
import Modal from '../components/Modal'

export default function Finance() {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<any>({ type: 'expense', method: 'cash', amount: 0, category: '', description: '', order_id: '' })

  const { data: list } = useQuery<any[]>({
    queryKey: ['finance'],
    queryFn: async () => (await api.get('/finance')).data,
  })
  const { data: bal } = useQuery<any>({
    queryKey: ['balance'],
    queryFn: async () => (await api.get('/finance/balance')).data,
  })
  const create = useMutation({
    mutationFn: async () => {
      const payload = { ...form, order_id: form.order_id ? Number(form.order_id) : null }
      if (!payload.order_id) delete payload.order_id
      return (await api.post('/finance', payload)).data
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['finance'] }); qc.invalidateQueries({ queryKey: ['balance'] }); setOpen(false) },
  })

  const fmt = (v: any) => Number(v ?? 0).toLocaleString('ru-RU', { minimumFractionDigits: 2 })

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Финансы</h1>
        <button className="btn-primary" onClick={() => setOpen(true)}>+ Операция</button>
      </div>
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="bg-emerald-100 rounded-lg p-4"><div className="text-xs text-emerald-700">Доходы</div><div className="text-2xl font-bold text-emerald-800">{fmt(bal?.income)} ₽</div></div>
        <div className="bg-rose-100 rounded-lg p-4"><div className="text-xs text-rose-700">Расходы</div><div className="text-2xl font-bold text-rose-800">{fmt(bal?.expense)} ₽</div></div>
        <div className="bg-violet-100 rounded-lg p-4"><div className="text-xs text-violet-700">Баланс</div><div className="text-2xl font-bold text-violet-800">{fmt(bal?.profit)} ₽</div></div>
      </div>
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="table">
          <thead><tr><th>Дата</th><th>Тип</th><th>Метод</th><th>Сумма</th><th>Заказ</th><th>Категория</th><th>Описание</th></tr></thead>
          <tbody>
            {(list ?? []).map((t) => (
              <tr key={t.id}>
                <td className="text-xs text-slate-500">{new Date(t.created_at).toLocaleString('ru-RU')}</td>
                <td><span className={`px-2 py-0.5 rounded-full text-xs ${t.type === 'income' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>{t.type === 'income' ? 'Доход' : 'Расход'}</span></td>
                <td className="text-xs uppercase">{t.method}</td>
                <td className="font-medium">{fmt(t.amount)} ₽</td>
                <td>{t.order_id ?? '—'}</td>
                <td>{t.category ?? '—'}</td>
                <td className="text-slate-600">{t.description}</td>
              </tr>
            ))}
            {!list?.length && <tr><td colSpan={7} className="text-center text-slate-500 py-8">Нет операций</td></tr>}
          </tbody>
        </table>
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title="Финансовая операция"
        footer={<div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setOpen(false)}>Отмена</button>
          <button className="btn-primary" onClick={() => create.mutate()} disabled={form.amount <= 0}>Сохранить</button>
        </div>}>
        <div className="grid grid-cols-2 gap-3">
          <select className="input" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
            <option value="income">Доход</option>
            <option value="expense">Расход</option>
          </select>
          <select className="input" value={form.method} onChange={(e) => setForm({ ...form, method: e.target.value })}>
            <option value="cash">Наличные</option><option value="card">Карта</option>
            <option value="transfer">Перевод</option><option value="sbp">СБП</option><option value="other">Другое</option>
          </select>
          <input className="input" type="number" min={0} value={form.amount} onChange={(e) => setForm({ ...form, amount: +e.target.value })} placeholder="Сумма" />
          <input className="input" placeholder="Категория" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          <input className="input" type="number" placeholder="ID заказа (опц.)" value={form.order_id} onChange={(e) => setForm({ ...form, order_id: e.target.value })} />
        </div>
        <textarea className="input" rows={3} placeholder="Описание" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      </Modal>
    </div>
  )
}
