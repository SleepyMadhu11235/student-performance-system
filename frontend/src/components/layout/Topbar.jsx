import { NavLink } from 'react-router-dom'
import { Plus } from 'lucide-react'

export default function Topbar({ title, description }) {
  return (
    <header className="border-b border-line bg-paper/90 backdrop-blur sticky top-0 z-10 px-8 py-5 flex items-center justify-between">
      <div>
        <h2 className="font-display text-2xl text-ink">{title}</h2>
        {description && <p className="text-sm text-ink-faint mt-0.5">{description}</p>}
      </div>
      <NavLink
        to="/predict"
        className="inline-flex items-center gap-1.5 bg-ink text-paper text-sm px-4 py-2 rounded hover:bg-ink-soft transition-colors"
      >
        <Plus size={15} />
        New prediction
      </NavLink>
    </header>
  )
}
