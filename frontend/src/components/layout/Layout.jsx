import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

const PAGE_META = {
  '/': { title: 'Dashboard', description: 'A running summary of every prediction on file.' },
  '/predict': { title: 'Predict', description: 'Score a single student or upload a class roster.' },
  '/history': { title: 'History', description: 'Every prediction the model has recorded.' },
  '/models': { title: 'Models', description: 'How each trained algorithm is performing.' },
}

export default function Layout() {
  const { pathname } = useLocation()
  const meta = PAGE_META[pathname] ?? { title: 'Gradebook', description: '' }

  return (
    <div className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <Topbar title={meta.title} description={meta.description} />
        <main className="px-8 py-8 max-w-[1400px]">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
