import { ReactNode } from 'react'

export default function Modal({ open, onClose, title, children, footer }:
  { open: boolean; onClose: () => void; title: string; children: ReactNode; footer?: ReactNode }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] overflow-auto"
           onClick={(e) => e.stopPropagation()}>
        <div className="px-6 py-3 border-b flex justify-between items-center">
          <h3 className="font-semibold">{title}</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-800">✕</button>
        </div>
        <div className="px-6 py-4 space-y-3">{children}</div>
        {footer && <div className="px-6 py-3 border-t bg-slate-50">{footer}</div>}
      </div>
    </div>
  )
}
