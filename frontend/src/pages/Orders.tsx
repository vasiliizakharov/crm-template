import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import OrderStatusBadge from '../components/OrderStatusBadge'
import Modal from '../components/Modal'
import { useAuth } from '../store/auth'

interface Order {
  id: number; number: string
  customer: { id: number; full_name: string; phone?: string }
  master?: { full_name: string } | null
  status: string; payment_status: string
  total_amount: number; paid_amount: number
  created_at: string
}

export default function Orders() {
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)
  const role = useAuth((s) => s.user?.role)

  const { data: orders } = useQuery<Order[]>({
    queryKey: ['orders', statusFilter, search],
    queryFn: async () => (await api.get('/orders', { params: { status: statusFilter || undefined, q: search || undefined } })).data,
  })
  const { data: customers } = useQuery({
    queryKey: ['customers-mini'],
    queryFn: async () => (await api.get('/customers', { params: { limit: 500 } })).data,
  })

  const [form, setForm] = useState({ customer_id: 0, declared_problem: '', estimated_cost: 0 })
  const create = useMutation({
    mutationFn: async () => (await api.post('/orders', form)).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['orders'] }); setOpen(false) },
  })

  const canCreate = role === 'admin' || role === 'manager'

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Заказы</h1>
        {canCreate && <button className="btn-primary" onClick={() => setOpen(true)}>+ Новый заказ</button>}
      </div>
      <div className="card mb-4 flex gap-3 items-end">
        <div>
          <label className="text-xs text-slate-500">Статус</label>
          <select className="input" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">— все —</option>
            <option value="new">Принят</option>
            <option value="diagnosing">Диагностика</option>
            <option value="awaiting">Ожидание</option>
            <option value="in_repair">В работе</option>
            <option value="ready">Готов</option>
            <option value="issued">Выдан</option>
            <option value="cancelled">Отменён</option>
            <option value="warranty">Гарантия</option>
          </select>
        </div>
        <div className="flex-1">
          <label className="text-xs text-slate-500">Поиск (№ заказа)</label>
          <input className="input" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="СЦ-..." />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="table">
          <thead><tr>
            <th>№</th><th>Клиент</th><th>Мастер</th><th>Статус</th><th>Оплата</th>
            <th>Сумма</th><th>Оплачено</th><th>Создан</th>
          </tr></thead>
          <tbody>
            {(orders ?? []).map((o) => (
              <tr key={o.id}>
                <td><Link className="text-brand-600 hover:underline" to={`/orders/${o.id}`}>{o.number}</Link></td>
                <td>{o.customer.full_name}<div className="text-xs text-slate-500">{o.customer.phone}</div></td>
                <td>{o.master?.full_name || '—'}</td>
                <td><OrderStatusBadge status={o.status} /></td>
                <td><span className="text-xs uppercase">{o.payment_status}</span></td>
                <td>{Number(o.total_amount).toFixed(2)} ₽</td>
                <td>{Number(o.paid_amount).toFixed(2)} ₽</td>
                <td className="text-xs text-slate-500">{new Date(o.created_at).toLocaleString('ru-RU')}</td>
              </tr>
            ))}
            {!orders?.length && (
              <tr><td colSpan={8} className="text-center text-slate-500 py-8">Нет заказов</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title="Новый заказ"
        footer={
          <div className="flex justify-end gap-2">
            <button className="btn-secondary" onClick={() => setOpen(false)}>Отмена</button>
            <button className="btn-primary" onClick={() => create.mutate()} disabled={!form.customer_id}>Создать</button>
          </div>
        }>
        <div>
          <label className="text-xs text-slate-500">Клиент</label>
          <select className="input" value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: +e.target.value })}>
            <option value={0}>— выберите —</option>
            {(customers ?? []).map((c: any) => (
              <option key={c.id} value={c.id}>{c.full_name} {c.phone ? `· ${c.phone}` : ''}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-500">Заявленная неисправность</label>
          <textarea className="input" rows={3} value={form.declared_problem}
            onChange={(e) => setForm({ ...form, declared_problem: e.target.value })} />
        </div>
        <div>
          <label className="text-xs text-slate-500">Предварительная стоимость, ₽</label>
          <input type="number" min={0} className="input" value={form.estimated_cost}
            onChange={(e) => setForm({ ...form, estimated_cost: +e.target.value })} />
        </div>
      </Modal>
    </div>
  )
}
