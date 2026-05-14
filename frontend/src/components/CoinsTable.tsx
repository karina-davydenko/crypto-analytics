import { useEffect, useMemo, useState } from 'react'
import { getCoins } from '../api/coins'
import type { CoinSummary } from '../types'
import { formatChange, formatCompact, formatPrice } from '../utils/format'

interface Props {
  selectedCoinId: string | null
  onSelect: (coin: CoinSummary) => void
}

type SortKey = keyof Pick<
  CoinSummary,
  'close_price' | 'daily_change_pct' | 'avg_volume' | 'avg_market_cap' | 'ma_7d' | 'ma_30d'
>

const COLUMNS: { label: string; key: SortKey | null; align: 'left' | 'right' }[] = [
  { label: '#', key: null, align: 'left' },
  { label: 'Монета', key: null, align: 'left' },
  { label: 'Цена', key: 'close_price', align: 'right' },
  { label: 'Изм. 24ч', key: 'daily_change_pct', align: 'right' },
  { label: 'Объём', key: 'avg_volume', align: 'right' },
  { label: 'Капитализация', key: 'avg_market_cap', align: 'right' },
  { label: 'MA 7д', key: 'ma_7d', align: 'right' },
  { label: 'MA 30д', key: 'ma_30d', align: 'right' },
]

const ICON_COLORS = ['#58a6ff', '#3fb950', '#d29922', '#f85149', '#bc8cff', '#f0883e']

function CoinIcon({ coinId, symbol }: { coinId: string; symbol: string }) {
  const [failed, setFailed] = useState(false)
  const src = `https://cdn.jsdelivr.net/npm/cryptocurrency-icons@0.18.1/svg/color/${symbol.toLowerCase()}.svg`
  const color = ICON_COLORS[coinId.charCodeAt(0) % ICON_COLORS.length]

  if (failed) {
    return (
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: '50%',
          background: color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 12,
          fontWeight: 700,
          color: '#fff',
          flexShrink: 0,
        }}
      >
        {symbol.charAt(0).toUpperCase()}
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={symbol}
      width={28}
      height={28}
      style={{ borderRadius: '50%', flexShrink: 0 }}
      onError={() => setFailed(true)}
    />
  )
}

export function CoinsTable({ selectedCoinId, onSelect }: Props) {
  const [coins, setCoins] = useState<CoinSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('avg_market_cap')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  useEffect(() => {
    getCoins()
      .then(setCoins)
      .catch(() => setError('Не удалось загрузить данные'))
      .finally(() => setLoading(false))
  }, [])

  function handleSort(key: SortKey | null) {
    if (!key) return
    if (key === sortKey) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return coins.filter(
      (c) => c.coin_name.toLowerCase().includes(q) || c.symbol.toLowerCase().includes(q),
    )
  }, [coins, search])

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      // null всегда в конец независимо от направления сортировки
      if (av === null && bv === null) return 0
      if (av === null) return 1
      if (bv === null) return -1
      return sortDir === 'desc' ? Number(bv) - Number(av) : Number(av) - Number(bv)
    })
  }, [filtered, sortKey, sortDir])

  if (loading) return <div style={{ padding: 24, color: 'var(--text-muted)' }}>Загрузка...</div>
  if (error) return <div style={{ padding: 24, color: 'var(--red)' }}>{error}</div>

  return (
    <div className="card" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <input
          className="search-input"
          type="text"
          placeholder="Поиск монеты..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div style={{ flex: 1, overflowY: 'auto', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr
              style={{
                borderBottom: '1px solid var(--border)',
                position: 'sticky',
                top: 0,
                background: 'var(--bg-card)',
                zIndex: 1,
              }}
            >
              {COLUMNS.map((col) => {
                const isActive = col.key === sortKey
                return (
                  <th
                    key={col.label}
                    onClick={() => handleSort(col.key)}
                    style={{
                      padding: '10px 16px',
                      textAlign: col.align,
                      color: isActive ? 'var(--accent)' : 'var(--text-muted)',
                      fontWeight: 500,
                      whiteSpace: 'nowrap',
                      cursor: col.key ? 'pointer' : 'default',
                      userSelect: 'none',
                      fontSize: 12,
                      letterSpacing: '0.04em',
                    }}
                  >
                    {col.label}
                    {isActive && (
                      <span style={{ marginLeft: 4 }}>{sortDir === 'desc' ? '↓' : '↑'}</span>
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {sorted.map((coin, i) => {
              const isSelected = coin.coin_id === selectedCoinId
              return (
                <tr
                  key={coin.coin_id}
                  onClick={() => onSelect(coin)}
                  className={`table-row${isSelected ? ' table-row--selected' : ''}`}
                  style={{ borderBottom: '1px solid var(--border)' }}
                >
                  <td style={{ padding: '10px 16px', color: 'var(--text-muted)', fontSize: 12 }}>
                    {i + 1}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <CoinIcon coinId={coin.coin_id} symbol={coin.symbol} />
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text)' }}>
                          {coin.coin_name}
                        </span>
                        <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>
                          {coin.symbol.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td
                    style={{
                      padding: '10px 16px',
                      textAlign: 'right',
                      fontWeight: 600,
                      color: 'var(--text)',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {formatPrice(coin.close_price)}
                  </td>
                  <td
                    style={{ padding: '10px 16px', textAlign: 'right', whiteSpace: 'nowrap' }}
                    className={
                      coin.daily_change_pct === null
                        ? ''
                        : coin.daily_change_pct >= 0
                          ? 'positive'
                          : 'negative'
                    }
                  >
                    {formatChange(coin.daily_change_pct)}
                  </td>
                  <td
                    style={{
                      padding: '10px 16px',
                      textAlign: 'right',
                      color: 'var(--text-muted)',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {formatCompact(coin.avg_volume)}
                  </td>
                  <td
                    style={{
                      padding: '10px 16px',
                      textAlign: 'right',
                      color: 'var(--text-muted)',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {formatCompact(coin.avg_market_cap)}
                  </td>
                  <td
                    style={{
                      padding: '10px 16px',
                      textAlign: 'right',
                      color: 'var(--text-muted)',
                      fontSize: 12,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {formatPrice(coin.ma_7d)}
                  </td>
                  <td
                    style={{
                      padding: '10px 16px',
                      textAlign: 'right',
                      color: 'var(--text-muted)',
                      fontSize: 12,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {formatPrice(coin.ma_30d)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
