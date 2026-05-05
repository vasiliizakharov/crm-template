const cfg: Record<string, { cls: string; label: string }> = {
  new:        { cls: 'bg-slate-200 text-slate-800',   label: 'Принят' },
  diagnosing: { cls: 'bg-amber-100 text-amber-800',   label: 'Диагностика' },
  awaiting:   { cls: 'bg-yellow-100 text-yellow-800', label: 'Ожидание' },
  in_repair:  { cls: 'bg-blue-100 text-blue-800',     label: 'В работе' },
  ready:      { cls: 'bg-green-100 text-green-800',   label: 'Готов' },
  issued:     { cls: 'bg-emerald-200 text-emerald-900', label: 'Выдан' },
  cancelled:  { cls: 'bg-red-100 text-red-800',       label: 'Отменён' },
  warranty:   { cls: 'bg-purple-100 text-purple-800', label: 'Гарантия' },
}

export default function OrderStatusBadge({ status }: { status: string }) {
  const c = cfg[status] ?? { cls: 'bg-slate-100', label: status }
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${c.cls}`}>{c.label}</span>
}
