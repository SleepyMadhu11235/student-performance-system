// Category tier metadata — used across GradeBadge, charts, and filters.
// Not mock data: this is real, permanent UI configuration.

export const TIER_ORDER = ['Excellent', 'Good', 'Pass', 'Fail']

export const TIER_META = {
  Excellent: { color: '#2F6F62', letter: 'E', description: 'Score 85\u2013100' },
  Good: { color: '#6B8E4E', letter: 'G', description: 'Score 70\u201384' },
  Pass: { color: '#4C6B8A', letter: 'P', description: 'Score 50\u201369' },
  Fail: { color: '#B4453A', letter: 'F', description: 'Score below 50' },
}
