import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import api from '../api/client'
import Modal from '../components/Modal'

export default function Stock() {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [target, setTarget] = useState<any>(null)
  const [form, setForm] = useState({ type: 'in' as 'in'|'out'|'adjust'|'writeoff', quantity: 1, cost: 0, note: '' })

  const { data: list } = useQuery<any[]>({
    queryKey: ['stock'],
    queryFn: async () => (await api.get('/stock')).data,
  })
  const move = useMutation({
    mutationFn: async () => (await api.post('/stock/movement', { product_id: target.product_id, ...form })).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['stock'] }); setOpen(false) },
  })

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Складские остатки</h1>
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="table">
          <thead><tr><th>SKU</th><th>Название</th><th>Ед.</th><th>Остаток</th><th>Резерв</th><th>Доступно</th><th>Цена</th><th></th></tr></thead>
          <tbody>
            {(list ?? []).map((s) => (
              <tr key={s.product_id}>
                <td className="font-mono text-xs">{s.sku}</td>
                <td>{s.name}</td>
                <td>{s.unit}</td>
                <td className={Number(s.quantity) <= 0 ? 'text-red-600 font-medium' : ''}>{Number(s.quantity).toFixed(2)}</td>
                <td>{Number(s.reserved).toFixed(2)}</td>
                <td className="font-medium">{Number(s.available).toFixed(2)}</td>
                <td>{Number(s.price).toFixed(2)}</td>
                <td className="text-right">
                  <button className="btn-secondary text-xs" onClick={() => { setTarget(s); setForm({ type: 'in', quantity: 1, cost: Number(s.cost), note: '' }); setOpen(true) }}>
                    Движение
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title={`Движение: ${target?.name ?? ''}`}
        footer={<div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setOpen(false)}>Отмена</button>
          <button className="btn-primary" onClick={() => move.mutate()} disabled={form.quantity <= 0}>Применить</button>
        </div>}>
        <select className="input" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value as any })}>
          <option value="in">Приход</option>
          <option value="out">Расход</option>
          <option value="adjust">Установить остаток</option>
          <option value="writeoff">Списание</option>
        </select>
        <div className="grid grid-cols-2 gap-3">
          <input className="input" type="number" min={0.01} step={0.1} value={form.quantity} onChange={(e) => setForm({ ...form, quantity: +e.target.value })} placeholder="Кол-во" />
          <input className="input" type="number" min={0} value={form.cost} onChange={(e) => setForm({ ...form, cost: +e.target.value })} placeholder="Себест." />
        </div>
        <textarea className="input" rows={2} placeholder="Комментарий" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
      </Modal>
    </div>
  )
}
