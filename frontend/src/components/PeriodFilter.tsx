import type { Period } from '../types'

interface Props {
  value: Period
  onChange: (period: Period) => void
}

const periods: { key: Period; label: string }[] = [
  { key: '24h', label: '24ч' },
  { key: '7d', label: '7д' },
  { key: '30d', label: '30д' },
]

export function PeriodFilter({ value, onChange }: Props) {
  return (
    <div
      style={{
        display: 'flex',
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        padding: 3,
        gap: 2,
      }}
    >
      {periods.map(({ key, label }) => {
        const isActive = value === key
        return (
          <button
            key={key}
            onClick={() => onChange(key)}
            style={{
              padding: '5px 16px',
              borderRadius: 6,
              border: 'none',
              background: isActive ? 'var(--accent)' : 'transparent',
              color: isActive ? '#fff' : 'var(--text-muted)',
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: isActive ? 600 : 400,
              transition: 'all 0.15s',
            }}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
