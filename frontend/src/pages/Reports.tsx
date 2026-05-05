import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import api from '../api/client'

export default function Reports() {
  const today = new Date().toISOString().slice(0, 10)
  const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)
  const [start, setStart] = useState(monthAgo)
  const [end, setEnd] = useState(today)

  const { data: summary } = useQuery({
    queryKey: ['summary', start, end],
    queryFn: async () => (await api.get('/reports/summary', { params: { period_start: start, period_end: end } })).data,
  })
  const { data: top } = useQuery({
    queryKey: ['top-customers'],
    queryFn: async () => (await api.get('/reports/top-customers')).data,
  })
  const { data: stockVal } = useQuery({
    queryKey: ['stock-value'],
    queryFn: async () => (await api.get('/reports/stock-value')).data,
  })

  const fmt = (v: any) => Number(v ?? 0).toLocaleString('ru-RU', { minimumFractionDigits: 2 })

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Отчёты</h1>
      <div className="card mb-4 flex gap-3 items-end">
        <div><label className="text-xs text-slate-500">С</label><input type="date" className="input" value={start} onChange={(e) => setStart(e.target.value)} /></div>
        <div><label className="text-xs text-slate-500">По</label><input type="date" className="input" value={end} onChange={(e) => setEnd(e.target.value)} /></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="font-semibold mb-2">Сводка периода</h2>
          {summary && (
            <table className="w-full text-sm">
              <tbody>
                <tr><td className="text-slate-600">Заказов</td><td className="text-right font-medium">{summary.orders_total}</td></tr>
                <tr><td className="text-slate-600">Выручка</td><td className="text-right font-medium">{fmt(summary.revenue)} ₽</td></tr>
                <tr><td className="text-slate-600">Расход</td><td className="text-right font-medium">{fmt(summary.expense)} ₽</td></tr>
                <tr><td className="text-slate-600">Прибыль</td><td className="text-right font-medium">{fmt(summary.profit)} ₽</td></tr>
                <tr><td className="text-slate-600">Средний чек</td><td className="text-right font-medium">{fmt(summary.avg_check)} ₽</td></tr>
              </tbody>
            </table>
          )}
        </div>
        <div className="card">
          <h2 className="font-semibold mb-2">Склад</h2>
          {stockVal && (
            <table className="w-full text-sm">
              <tbody>
                <tr><td className="text-slate-600">Позиций</td><td className="text-right font-medium">{stockVal.positions}</td></tr>
                <tr><td className="text-slate-600">Стоимость по себест.</td><td className="text-right font-medium">{fmt(stockVal.by_cost)} ₽</td></tr>
                <tr><td className="text-slate-600">Стоимость по цене</td><td className="text-right font-medium">{fmt(stockVal.by_price)} ₽</td></tr>
              </tbody>
            </table>
          )}
        </div>
      </div>
      <div className="card mt-4">
        <h2 className="font-semibold mb-2">ТОП-10 клиентов</h2>
        <table className="table">
          <thead><tr><th>Клиент</th><th>Телефон</th><th>Заказов</th><th>Сумма</th></tr></thead>
          <tbody>
            {(top ?? []).map((c: any) => (
              <tr key={c.id}><td>{c.name}</td><td>{c.phone}</td><td>{c.orders}</td><td>{fmt(c.amount)} ₽</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
