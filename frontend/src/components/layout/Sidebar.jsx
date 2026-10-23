import { NavLink } from 'react-router-dom'
import { LayoutGrid, PenLine, ScrollText, SlidersHorizontal } from 'lucide-react'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutGrid, end: true },
  { to: '/predict', label: 'Predict', icon: PenLine },
  { to: '/history', label: 'History', icon: ScrollText },
  { to: '/models', label: 'Models', icon: SlidersHorizontal },
]

export default function Sidebar() {
  return (
    <aside className="w-64 shrink-0 bg-ink text-paper flex flex-col h-screen sticky top-0">
      <div className="px-6 pt-8 pb-6 border-b border-white/10">
        <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-brass-soft/80">
          Registrar&rsquo;s Office
        </p>
        <h1 className="font-display italic text-2xl mt-1 leading-tight">
          The Gradebook
        </h1>
        <p className="text-[11px] text-paper/50 mt-1">Performance Prediction Ledger</p>
      </div>

      <nav className="flex-1 py-4">
        <ul>
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) =>
                  [
                    'group flex items-center gap-3 px-6 py-3 text-sm border-l-2 transition-colors',
                    isActive
                      ? 'border-brass bg-white/[0.06] text-paper'
                      : 'border-transparent text-paper/55 hover:text-paper hover:bg-white/[0.03]',
                  ].join(' ')
                }
              >
                <Icon size={17} strokeWidth={1.8} />
                <span className="font-body">{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="px-6 py-5 border-t border-white/10">
        <p className="text-[11px] text-paper/40 font-mono leading-relaxed">
          v0.1 &middot; Phase 1 UI
          <br />
          mock data active
        </p>
      </div>
    </aside>
  )
}
