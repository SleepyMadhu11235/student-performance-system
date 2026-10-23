export default function EmptyState({ icon: Icon, title, description }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6">
      {Icon && (
        <div className="w-12 h-12 rounded-full border border-line flex items-center justify-center mb-4 text-ink-faint">
          <Icon size={20} />
        </div>
      )}
      <p className="font-display text-lg text-ink">{title}</p>
      {description && <p className="mt-1 text-sm text-ink-faint max-w-sm">{description}</p>}
    </div>
  )
}
