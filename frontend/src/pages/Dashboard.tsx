import { useQuery } from '@tanstack/react-query'
import api from '../api/client'

interface Summary {
  period_start: string; period_end: string
  orders_total: number
  orders_by_status: Record<string, number>
  revenue: number; expense: number; profit: number; avg_check: number
}

export default function Dashboard() {
  const { data: s } = useQuery<Summary>({
    queryKey: ['summary'],
    queryFn: async () => (await api.get('/reports/summary')).data,
  })
  const { data: stockVal } = useQuery({
    queryKey: ['stock-value'],
    queryFn: async () => (await api.get('/reports/stock-value')).data,
  })

  const fmt = (v: any) => Number(v ?? 0).toLocaleString('ru-RU', { minimumFractionDigits: 2 })

  const cards = [
    { title: 'Заказы за 30 дн.',     v: s?.orders_total ?? 0,                            cls: 'bg-blue-500' },
    { title: 'Выручка, ₽',           v: fmt(s?.revenue),                                  cls: 'bg-emerald-500' },
    { title: 'Расход, ₽',            v: fmt(s?.expense),                                  cls: 'bg-rose-500' },
    { title: 'Прибыль, ₽',           v: fmt(s?.profit),                                   cls: 'bg-violet-500' },
    { title: 'Средний чек, ₽',       v: fmt(s?.avg_check),                                cls: 'bg-amber-500' },
    { title: 'Склад (себест.), ₽',   v: fmt(stockVal?.by_cost),                           cls: 'bg-cyan-600' },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Панель управления</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {cards.map((c) => (
          <div key={c.title} className={`${c.cls} text-white rounded-lg shadow p-5`}>
            <div className="text-sm opacity-90">{c.title}</div>
            <div className="text-2xl font-bold mt-1">{c.v}</div>
          </div>
        ))}
      </div>
      <div className="card">
        <h2 className="font-semibold mb-3">Заказы по статусам</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
          {Object.entries(s?.orders_by_status ?? {}).map(([k, v]) => (
            <div key={k} className="bg-slate-50 rounded p-3 text-center">
              <div className="text-slate-500 text-xs uppercase">{k}</div>
              <div className="text-xl font-semibold">{v}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
