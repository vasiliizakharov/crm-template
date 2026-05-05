import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import api from '../api/client'
import Modal from '../components/Modal'

export default function Salaries() {
  const qc = useQueryClient()
  const [openRule, setOpenRule] = useState(false)
  const [openCalc, setOpenCalc] = useState(false)
  const [rule, setRule] = useState<any>({ user_id: 0, base_salary: 0, work_share_pct: 0, parts_share_pct: 0, revenue_share_pct: 0 })
  const today = new Date().toISOString().slice(0, 10)
  const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)
  const [calc, setCalc] = useState<any>({ user_id: 0, period_start: monthAgo, period_end: today, bonus_amount: 0, deduction_amount: 0, save: false })
  const [calcResult, setCalcResult] = useState<any>(null)

  const { data: rules } = useQuery<any[]>({
    queryKey: ['salary-rules'], queryFn: async () => (await api.get('/salaries/rules')).data,
  })
  const { data: records } = useQuery<any[]>({
    queryKey: ['salary-records'], queryFn: async () => (await api.get('/salaries/records')).data,
  })
  const { data: users } = useQuery<any[]>({
    queryKey: ['users'], queryFn: async () => (await api.get('/users')).data,
  })

  const saveRule = useMutation({
    mutationFn: async () => (await api.post('/salaries/rules', rule)).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['salary-rules'] }); setOpenRule(false) },
  })
  const doCalc = useMutation({
    mutationFn: async () => (await api.post('/salaries/calc', calc)).data,
    onSuccess: (r) => { setCalcResult(r); qc.invalidateQueries({ queryKey: ['salary-records'] }) },
  })
  const pay = useMutation({
    mutationFn: async (id: number) => (await api.post(`/salaries/records/${id}/pay`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['salary-records'] }),
  })

  const userMap = new Map((users ?? []).map((u: any) => [u.id, u]))
  const fmt = (v: any) => Number(v ?? 0).toLocaleString('ru-RU', { minimumFractionDigits: 2 })

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Зарплата</h1>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={() => setOpenRule(true)}>+ Правило</button>
          <button className="btn-primary" onClick={() => { setCalcResult(null); setOpenCalc(true) }}>Рассчитать</button>
        </div>
      </div>

      <div className="card mb-4">
        <h2 className="font-semibold mb-3">Правила начисления</h2>
        <table className="table">
          <thead><tr><th>Сотрудник</th><th>Оклад</th><th>% работы</th><th>% запчасти</th><th>% выручка</th><th>Период</th></tr></thead>
          <tbody>
            {(rules ?? []).map((r) => (
              <tr key={r.id}>
                <td>{userMap.get(r.user_id)?.full_name ?? r.user_id}</td>
                <td>{fmt(r.base_salary)} ₽</td>
                <td>{r.work_share_pct}%</td>
                <td>{r.parts_share_pct}%</td>
                <td>{r.revenue_share_pct}%</td>
                <td className="text-xs text-slate-500">{r.valid_from} → {r.valid_to ?? '∞'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-3">Сохранённые расчёты</h2>
        <table className="table">
          <thead><tr><th>Сотрудник</th><th>Период</th><th>Оклад</th><th>Работы</th><th>Запчасти</th><th>Выручка</th><th>Премия</th><th>Удержания</th><th>ИТОГО</th><th></th></tr></thead>
          <tbody>
            {(records ?? []).map((r) => (
              <tr key={r.id}>
                <td>{userMap.get(r.user_id)?.full_name ?? r.user_id}</td>
                <td className="text-xs">{r.period_start} → {r.period_end}</td>
                <td>{fmt(r.base_amount)}</td>
                <td>{fmt(r.works_amount)}</td>
                <td>{fmt(r.parts_amount)}</td>
                <td>{fmt(r.revenue_amount)}</td>
                <td>{fmt(r.bonus_amount)}</td>
                <td>{fmt(r.deduction_amount)}</td>
                <td className="font-bold">{fmt(r.total_amount)}</td>
                <td>{r.paid ? <span className="text-emerald-700 text-xs">выплачено</span>
                  : <button className="btn-primary text-xs" onClick={() => pay.mutate(r.id)}>Выплатить</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal open={openRule} onClose={() => setOpenRule(false)} title="Новое правило"
        footer={<div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setOpenRule(false)}>Отмена</button>
          <button className="btn-primary" onClick={() => saveRule.mutate()} disabled={!rule.user_id}>Сохранить</button>
        </div>}>
        <select className="input" value={rule.user_id} onChange={(e) => setRule({ ...rule, user_id: +e.target.value })}>
          <option value={0}>— сотрудник —</option>
          {(users ?? []).map((u: any) => <option key={u.id} value={u.id}>{u.full_name} · {u.role}</option>)}
        </select>
        <div className="grid grid-cols-2 gap-3">
          <input className="input" type="number" min={0} placeholder="Оклад" value={rule.base_salary} onChange={(e) => setRule({ ...rule, base_salary: +e.target.value })} />
          <input className="input" type="number" min={0} max={100} placeholder="% работы" value={rule.work_share_pct} onChange={(e) => setRule({ ...rule, work_share_pct: +e.target.value })} />
          <input className="input" type="number" min={0} max={100} placeholder="% наценки запчастей" value={rule.parts_share_pct} onChange={(e) => setRule({ ...rule, parts_share_pct: +e.target.value })} />
          <input className="input" type="number" min={0} max={100} placeholder="% выручки (менеджер)" value={rule.revenue_share_pct} onChange={(e) => setRule({ ...rule, revenue_share_pct: +e.target.value })} />
        </div>
      </Modal>

      <Modal open={openCalc} onClose={() => setOpenCalc(false)} title="Расчёт зарплаты"
        footer={<div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setOpenCalc(false)}>Закрыть</button>
          <button className="btn-secondary" onClick={() => { setCalc({ ...calc, save: false }); doCalc.mutate() }}>Предпросмотр</button>
          <button className="btn-primary" onClick={() => { setCalc({ ...calc, save: true }); doCalc.mutate() }}>Сохранить</button>
        </div>}>
        <select className="input" value={calc.user_id} onChange={(e) => setCalc({ ...calc, user_id: +e.target.value })}>
          <option value={0}>— сотрудник —</option>
          {(users ?? []).map((u: any) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
        </select>
        <div className="grid grid-cols-2 gap-3">
          <input className="input" type="date" value={calc.period_start} onChange={(e) => setCalc({ ...calc, period_start: e.target.value })} />
          <input className="input" type="date" value={calc.period_end} onChange={(e) => setCalc({ ...calc, period_end: e.target.value })} />
          <input className="input" type="number" placeholder="Премия" value={calc.bonus_amount} onChange={(e) => setCalc({ ...calc, bonus_amount: +e.target.value })} />
          <input className="input" type="number" placeholder="Удержания" value={calc.deduction_amount} onChange={(e) => setCalc({ ...calc, deduction_amount: +e.target.value })} />
        </div>
        {calcResult && (
          <div className="bg-slate-50 p-3 rounded text-sm">
            <div>Оклад: <b>{fmt(calcResult.base_amount)}</b></div>
            <div>Работы: <b>{fmt(calcResult.works_amount)}</b></div>
            <div>Запчасти (% наценки): <b>{fmt(calcResult.parts_amount)}</b></div>
            <div>Выручка (менеджер): <b>{fmt(calcResult.revenue_amount)}</b></div>
            <div>Премия: <b>{fmt(calcResult.bonus_amount)}</b></div>
            <div>Удержания: <b>{fmt(calcResult.deduction_amount)}</b></div>
            <div className="text-lg mt-1">ИТОГО: <b>{fmt(calcResult.total_amount)} ₽</b></div>
          </div>
        )}
      </Modal>
    </div>
  )
}
