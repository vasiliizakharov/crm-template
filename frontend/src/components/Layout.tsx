import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth, User } from '../store/auth'

type NavItem = { to: string; label: string; roles: User['role'][] }

const NAV: NavItem[] = [
  { to: '/',          label: 'Дашборд',  roles: ['admin','manager','warehouse','master','accountant'] },
  { to: '/orders',    label: 'Заказы',   roles: ['admin','manager','master'] },
  { to: '/customers', label: 'Клиенты',  roles: ['admin','manager'] },
  { to: '/products',  label: 'Товары',   roles: ['admin','warehouse','manager'] },
  { to: '/stock',     label: 'Склад',    roles: ['admin','warehouse','manager'] },
  { to: '/finance',   label: 'Финансы',  roles: ['admin','manager','accountant'] },
  { to: '/salaries',  label: 'Зарплата', roles: ['admin','accountant'] },
  { to: '/reports',   label: 'Отчёты',   roles: ['admin','manager','accountant'] },
  { to: '/users',     label: 'Сотрудники', roles: ['admin'] },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()

  const items = NAV.filter((i) => user && i.roles.includes(user.role))

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 bg-slate-900 text-slate-100 p-4 space-y-2">
        <Link to="/" className="block text-xl font-semibold mb-4 border-b border-slate-700 pb-3">
          Service CRM
        </Link>
        <nav className="space-y-1">
          {items.map((i) => (
            <NavLink key={i.to} to={i.to} end
              className={({ isActive }) =>
                `block px-3 py-2 rounded text-sm ${isActive ? 'bg-brand-600' : 'hover:bg-slate-800'}`
              }>
              {i.label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute bottom-4 left-4 right-4 text-xs text-slate-400">
          <div className="truncate">{user?.full_name}</div>
          <div className="truncate text-slate-500">{user?.email}</div>
          <div className="text-slate-500">Роль: {user?.role}</div>
          <button onClick={() => { logout(); nav('/login') }}
            className="mt-2 w-full text-center bg-slate-800 hover:bg-slate-700 rounded py-1.5">
            Выйти
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
