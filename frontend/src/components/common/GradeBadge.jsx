import { TIER_META } from '../../constants/tiers'

/**
 * The signature element of the app: a circular "stamp" that mimics the
 * grade seal a teacher presses onto a report card. Size scales for use
 * both inline in table rows and large on the prediction result card.
 */
export default function GradeBadge({ label, size = 'md' }) {
  const meta = TIER_META[label] ?? { color: '#6B7A6E', letter: '?', description: '' }
  const sizes = {
    sm: { box: 28, font: 12, ring: 2 },
    md: { box: 40, font: 15, ring: 2.5 },
    lg: { box: 84, font: 30, ring: 3.5 },
  }
  const s = sizes[size] ?? sizes.md

  return (
    <span
      className="inline-flex items-center justify-center rounded-stamp font-display font-semibold select-none"
      style={{
        width: s.box,
        height: s.box,
        fontSize: s.font,
        color: meta.color,
        border: `${s.ring}px solid ${meta.color}`,
        boxShadow: `inset 0 0 0 2px ${meta.color}22`,
        transform: 'rotate(-6deg)',
      }}
      title={`${label} \u2014 ${meta.description}`}
    >
      {meta.letter}
    </span>
  )
}
