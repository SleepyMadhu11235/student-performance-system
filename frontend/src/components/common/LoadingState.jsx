import { Loader2 } from 'lucide-react'

export default function LoadingState({ label = 'Loading\u2026' }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-20 text-ink-faint">
      <Loader2 size={22} className="animate-spin text-brass" />
      <p className="mt-3 text-sm font-mono">{label}</p>
    </div>
  )
}
