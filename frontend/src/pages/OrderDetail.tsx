import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import api from '../api/client'
import OrderStatusBadge from '../components/OrderStatusBadge'
import Modal from '../components/Modal'

export default function OrderDetail() {
  const { id } = useParams()
  const qc = useQueryClient()
  const [statusOpen, setStatusOpen] = useState(false)
  const [newStatus, setNewStatus] = useState('')
  const [note, setNote] = useState('')
  const [payOpen, setPayOpen] = useState(false)
  const [payAmount, setPayAmount] = useState(0)
  const [payMethod, setPayMethod] = useState<'cash'|'card'|'transfer'|'sbp'|'other'>('cash')
  const [itemOpen, setItemOpen] = useState(false)
  const [item, setItem] = useState({ kind: 'service' as 'part'|'service', name: '', quantity: 1, unit_price: 0, unit_cost: 0, master_share_pct: 50, product_id: 0 })

  const { data: order } = useQuery<any>({
    queryKey: ['order', id],
    queryFn: async () => (await api.get(`/orders/${id}`)).data,
  })
  const { data: history } = useQuery<any[]>({
    queryKey: ['order-history', id],
    queryFn: async () => (await api.get(`/orders/${id}/history`)).data,
  })
  const { data: products } = useQuery<any[]>({
    queryKey: ['products-list'],
    queryFn: async () => (await api.get('/products')).data,
  })

  const changeStatus = useMutation({
    mutationFn: async () => (await api.patch(`/orders/${id}/status`, { status: newStatus, note })).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['order', id] }); qc.invalidateQueries({ queryKey: ['order-history', id] }); setStatusOpen(false); setNote('') },
  })
  const addItem = useMutation({
    mutationFn: async () => (await api.post(`/orders/${id}/items`, item)).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['order', id] }); setItemOpen(false) },
  })
  const pay = useMutation({
    mutationFn: async () => (await api.post(`/finance`, {
      order_id: Number(id), type: 'income', method: payMethod, amount: payAmount, category: 'order_payment',
    })).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['order', id] }); setPayOpen(false); setPayAmount(0) },
  })
  const delItem = useMutation({
    mutationFn: async (item_id: number) => (await api.delete(`/orders/${id}/items/${item_id}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['order', id] }),
  })

  if (!order) return <div>Загрузка...</div>

  return (
    <div>
      <div className="mb-4">
        <Link to="/orders" className="text-sm text-brand-600">← К заказам</Link>
      </div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{order.number}</h1>
        <div className="flex items-center gap-2">
          <OrderStatusBadge status={order.status} />
          <button className="btn-secondary" onClick={() => setStatusOpen(true)}>Сменить статус</button>
          <button className="btn-primary" onClick={() => setPayOpen(true)}>Принять оплату</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <div className="card">
          <div className="text-xs text-slate-500">Клиент</div>
          <div className="font-medium">{order.customer.full_name}</div>
          <div className="text-sm text-slate-600">{order.customer.phone}</div>
        </div>
        <div className="card">
          <div className="text-xs text-slate-500">Устройство</div>
          <div className="font-medium">{order.device ? `${order.device.device_type} ${order.device.brand ?? ''} ${order.device.model ?? ''}` : '—'}</div>
          <div className="text-sm text-slate-600">{order.device?.serial}</div>
        </div>
        <div className="card">
          <div className="text-xs text-slate-500">Сумма / Оплачено</div>
          <div className="font-medium text-lg">{Number(order.total_amount).toFixed(2)} ₽</div>
          <div className="text-sm text-emerald-700">{Number(order.paid_amount).toFixed(2)} ₽ ({order.payment_status})</div>
        </div>
      </div>

      <div className="card mb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><div className="text-xs text-slate-500">Заявленная неисправность</div><div className="text-sm">{order.declared_problem || '—'}</div></div>
          <div><div className="text-xs text-slate-500">Диагноз</div><div className="text-sm">{order.diagnosis || '—'}</div></div>
          <div><div className="text-xs text-slate-500">Что сделано</div><div className="text-sm">{order.work_done || '—'}</div></div>
          <div><div className="text-xs text-slate-500">Комплект / Внешний вид</div><div className="text-sm">{order.accessories || '—'} / {order.appearance || '—'}</div></div>
          <div><div className="text-xs text-slate-500">Менеджер / Мастер</div><div className="text-sm">{order.manager?.full_name || '—'} / {order.master?.full_name || '—'}</div></div>
          <div><div className="text-xs text-slate-500">Дедлайн / Гарантия до</div><div className="text-sm">{order.deadline_at ? new Date(order.deadline_at).toLocaleString('ru-RU') : '—'} / {order.warranty_until || '—'}</div></div>
        </div>
      </div>

      <div className="card mb-4">
        <div className="flex justify-between items-center mb-3">
          <h2 className="font-semibold">Состав заказа</h2>
          <button className="btn-secondary" onClick={() => setItemOpen(true)}>+ Позиция</button>
        </div>
        <table className="table">
          <thead><tr><th>Тип</th><th>Наименование</th><th>Кол-во</th><th>Себест.</th><th>Цена</th><th>% мастеру</th><th>Сумма</th><th></th></tr></thead>
          <tbody>
            {(order.items ?? []).map((it: any) => (
              <tr key={it.id}>
                <td><span className="text-xs uppercase">{it.kind}</span></td>
                <td>{it.name}</td>
                <td>{it.quantity}</td>
                <td>{Number(it.unit_cost).toFixed(2)}</td>
                <td>{Number(it.unit_price).toFixed(2)}</td>
                <td>{Number(it.master_share_pct).toFixed(1)}%</td>
                <td>{(Number(it.unit_price) * Number(it.quantity)).toFixed(2)}</td>
                <td><button className="text-red-600 text-xs" onClick={() => delItem.mutate(it.id)}>удалить</button></td>
              </tr>
            ))}
            {!order.items?.length && <tr><td colSpan={8} className="text-center text-slate-500 py-4">Пусто</td></tr>}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-3">История</h2>
        <ul className="space-y-2 text-sm">
          {(history ?? []).map((h) => (
            <li key={h.id} className="border-l-2 border-slate-300 pl-3">
              <div className="text-xs text-slate-500">{new Date(h.created_at).toLocaleString('ru-RU')} · {h.action}</div>
              <div className="text-slate-700">{h.note ?? JSON.stringify(h.after_state)}</div>
            </li>
          ))}
        </ul>
      </div>

      <Modal open={statusOpen} onClose={() => setStatusOpen(false)} title="Смена статуса"
        footer={<div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setStatusOpen(false)}>Отмена</button>
          <button className="btn-primary" onClick={() => changeStatus.mutate()} disabled={!newStatus}>Применить</button>
        </div>}>
        <select className="input" value={newStatus} onChange={(e) => setNewStatus(e.target.value)}>
          <option value="">— выбрать —</option>
          {['new','diagnosing','awaiting','in_repair','ready','issued','cancelled','warranty'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <textarea className="input" rows={2} placeholder="Комментарий" value={note} onChange={(e) => setNote(e.target.value)} />
      </Modal>

      <Modal open={payOpen} onClose={() => setPayOpen(false)} title="Приём оплаты"
        footer={<div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setPayOpen(false)}>Отмена</button>
          <button className="btn-primary" onClick={() => pay.mutate()} disabled={payAmount <= 0}>Принять</button>
        </div>}>
        <input className="input" type="number" min={0} value={payAmount} onChange={(e) => setPayAmount(+e.target.value)} />
        <select className="input" value={payMethod} onChange={(e) => setPayMethod(e.target.value as any)}>
          <option value="cash">Наличные</option><option value="card">Карта</option>
          <option value="transfer">Перевод</option><option value="sbp">СБП</option><option value="other">Другое</option>
        </select>
      </Modal>

      <Modal open={itemOpen} onClose={() => setItemOpen(false)} title="Добавить позицию"
        footer={<div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setItemOpen(false)}>Отмена</button>
          <button className="btn-primary" onClick={() => addItem.mutate()} disabled={!item.name || item.unit_price <= 0}>Добавить</button>
        </div>}>
        <select className="input" value={item.kind} onChange={(e) => setItem({ ...item, kind: e.target.value as any })}>
          <option value="service">Услуга</option>
          <option value="part">Запчасть</option>
        </select>
        {item.kind === 'part' && (
          <select className="input" value={item.product_id}
            onChange={(e) => {
              const p = (products ?? []).find((x: any) => x.id === +e.target.value)
              setItem({ ...item, product_id: +e.target.value, name: p?.name ?? item.name, unit_price: Number(p?.price ?? 0), unit_cost: Number(p?.cost ?? 0) })
            }}>
            <option value={0}>— выбрать запчасть —</option>
            {(products ?? []).filter((p: any) => p.kind === 'part').map((p: any) =>
              <option key={p.id} value={p.id}>{p.name} ({p.sku ?? ''})</option>
            )}
          </select>
        )}
        <input className="input" placeholder="Название" value={item.name} onChange={(e) => setItem({ ...item, name: e.target.value })} />
        <div className="grid grid-cols-2 gap-3">
          <input className="input" type="number" min={0.001} step={0.1} value={item.quantity} onChange={(e) => setItem({ ...item, quantity: +e.target.value })} placeholder="Кол-во" />
          <input className="input" type="number" min={0} value={item.unit_price} onChange={(e) => setItem({ ...item, unit_price: +e.target.value })} placeholder="Цена" />
          <input className="input" type="number" min={0} value={item.unit_cost} onChange={(e) => setItem({ ...item, unit_cost: +e.target.value })} placeholder="Себестоимость" />
          <input className="input" type="number" min={0} max={100} value={item.master_share_pct} onChange={(e) => setItem({ ...item, master_share_pct: +e.target.value })} placeholder="% мастеру" />
        </div>
      </Modal>
    </div>
  )
}
