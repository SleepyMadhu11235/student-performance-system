import { CircleAlert, RotateCcw } from 'lucide-react'

export default function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-20 px-6">
      <div className="w-11 h-11 rounded-full bg-tier-fail/10 flex items-center justify-center text-tier-fail">
        <CircleAlert size={20} />
      </div>
      <p className="font-display text-lg text-ink mt-4">Couldn&rsquo;t load this</p>
      <p className="text-sm text-ink-faint mt-1 max-w-sm">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 mt-5 text-sm border border-line rounded-md px-3.5 py-2 text-ink-soft hover:border-brass hover:text-brass transition-colors"
        >
          <RotateCcw size={14} /> Try again
        </button>
      )}
    </div>
  )
}
