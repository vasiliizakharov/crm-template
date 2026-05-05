import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import api from '../api/client'
import Modal from '../components/Modal'

export default function Products() {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const empty = { kind: 'part', sku: '', name: '', description: '', unit: 'шт', cost: 0, price: 0, is_active: true }
  const [form, setForm] = useState<any>(empty)

  const { data: list } = useQuery<any[]>({
    queryKey: ['products'],
    queryFn: async () => (await api.get('/products')).data,
  })

  const save = useMutation({
    mutationFn: async () => editing
      ? (await api.put(`/products/${editing.id}`, form)).data
      : (await api.post('/products', form)).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['products'] }); setOpen(false); setEditing(null); setForm(empty) },
  })
  const del = useMutation({
    mutationFn: async (id: number) => (await api.delete(`/products/${id}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['products'] }),
  })

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Товары и услуги</h1>
        <button className="btn-primary" onClick={() => { setForm(empty); setEditing(null); setOpen(true) }}>+ Добавить</button>
      </div>
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="table">
          <thead><tr><th>Тип</th><th>SKU</th><th>Название</th><th>Цена</th><th>Себест.</th><th>Активен</th><th></th></tr></thead>
          <tbody>
            {(list ?? []).map((p) => (
              <tr key={p.id}>
                <td><span className="text-xs uppercase">{p.kind}</span></td>
                <td className="font-mono text-xs">{p.sku}</td>
                <td>{p.name}</td>
                <td>{Number(p.price).toFixed(2)}</td>
                <td>{Number(p.cost).toFixed(2)}</td>
                <td>{p.is_active ? '✓' : '—'}</td>
                <td className="text-right">
                  <button className="text-brand-600 text-sm mr-3" onClick={() => { setEditing(p); setForm(p); setOpen(true) }}>править</button>
                  <button className="text-red-600 text-sm" onClick={() => confirm('Отключить?') && del.mutate(p.id)}>отключить</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title={editing ? 'Редактирование' : 'Новая позиция'}
        footer={<div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setOpen(false)}>Отмена</button>
          <button className="btn-primary" onClick={() => save.mutate()} disabled={!form.name}>Сохранить</button>
        </div>}>
        <select className="input" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
          <option value="part">Запчасть</option>
          <option value="service">Услуга</option>
        </select>
        <input className="input" placeholder="SKU / артикул" value={form.sku || ''} onChange={(e) => setForm({ ...form, sku: e.target.value })} />
        <input className="input" placeholder="Название" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <textarea className="input" rows={2} placeholder="Описание" value={form.description || ''} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <div className="grid grid-cols-3 gap-3">
          <input className="input" placeholder="Ед. изм." value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
          <input className="input" type="number" min={0} placeholder="Себестоимость" value={form.cost} onChange={(e) => setForm({ ...form, cost: +e.target.value })} />
          <input className="input" type="number" min={0} placeholder="Цена" value={form.price} onChange={(e) => setForm({ ...form, price: +e.target.value })} />
        </div>
      </Modal>
    </div>
  )
}
