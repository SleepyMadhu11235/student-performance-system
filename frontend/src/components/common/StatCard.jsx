export default function StatCard({ label, value, unit, sublabel, accent = '#B8923F' }) {
  return (
    <div className="bg-paper-card rounded-md shadow-card px-6 py-5 border-t-2" style={{ borderColor: accent }}>
      <p className="label-eyebrow">{label}</p>
      <p className="mt-2 font-display text-4xl font-semibold text-ink leading-none">
        {value}
        {unit && <span className="text-lg font-body font-normal text-ink-faint ml-1">{unit}</span>}
      </p>
      {sublabel && <p className="mt-2 text-xs text-ink-faint font-mono">{sublabel}</p>}
    </div>
  )
}
