import { ChevronLeft, ChevronRight } from 'lucide-react'

export default function Pagination({ page, totalPages, onChange }) {
  if (totalPages <= 1) return null

  const go = (p) => onChange(Math.min(Math.max(p, 1), totalPages))

  return (
    <div className="flex items-center justify-between pt-4">
      <p className="text-xs font-mono text-ink-faint">
        Page {page} of {totalPages}
      </p>
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => go(page - 1)}
          disabled={page === 1}
          className="p-1.5 rounded border border-line text-ink-soft disabled:opacity-30 disabled:cursor-not-allowed hover:border-brass hover:text-brass transition-colors"
          aria-label="Previous page"
        >
          <ChevronLeft size={16} />
        </button>
        <button
          type="button"
          onClick={() => go(page + 1)}
          disabled={page === totalPages}
          className="p-1.5 rounded border border-line text-ink-soft disabled:opacity-30 disabled:cursor-not-allowed hover:border-brass hover:text-brass transition-colors"
          aria-label="Next page"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}
