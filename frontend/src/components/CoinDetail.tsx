import { useEffect, useReducer } from 'react'
import { getCoinHistory, getCoinNews } from '../api/coins'
import type { NewsItem, Period, PriceHistory } from '../types'
import { formatChange, formatPrice } from '../utils/format'
import { NewsList } from './NewsList'
import { PriceChart } from './PriceChart'
import { SentimentChart } from './SentimentChart'

interface Props {
  coinId: string
  coinName: string
  currentPrice: number
  currentChange: number | null
  period: Period
}

type State =
  | { status: 'loading' }
  | { status: 'success'; history: PriceHistory[]; news: NewsItem[] }
  | { status: 'error'; message: string }

export function CoinDetail({ coinId, coinName, currentPrice, currentChange, period }: Props) {
  const [state, dispatch] = useReducer(
    (_prev: State, next: State): State => next,
    { status: 'loading' },
  )

  useEffect(() => {
    let cancelled = false
    dispatch({ status: 'loading' })
    Promise.all([getCoinHistory(coinId, period), getCoinNews(coinId, period)])
      .then(([history, news]) => {
        if (!cancelled) dispatch({ status: 'success', history, news })
      })
      .catch(() => {
        if (!cancelled) dispatch({ status: 'error', message: 'Не удалось загрузить данные' })
      })
    return () => {
      cancelled = true
    }
  }, [coinId, period])

  const isPositive = currentChange !== null && currentChange >= 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <h2>{coinName}</h2>
        <span style={{ fontSize: 20, fontWeight: 600 }}>{formatPrice(currentPrice)}</span>
        <span className={isPositive ? 'positive' : 'negative'} style={{ fontSize: 14 }}>
          {formatChange(currentChange)}
        </span>
      </div>

      {state.status === 'loading' ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
          Загрузка...
        </div>
      ) : state.status === 'error' ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--red)' }}>
          {state.message}
        </div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="card" style={{ padding: 16 }}>
              <h2 style={{ marginBottom: 12, fontSize: 13, color: 'var(--text-muted)', fontWeight: 500 }}>
                ИСТОРИЯ ЦЕН
              </h2>
              <PriceChart data={state.history} />
            </div>
            <div className="card" style={{ padding: 16 }}>
              <h2 style={{ marginBottom: 12, fontSize: 13, color: 'var(--text-muted)', fontWeight: 500 }}>
                SENTIMENT НОВОСТЕЙ
              </h2>
              <SentimentChart news={state.news} />
            </div>
          </div>

          <div className="card">
            <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)' }}>
              <h2 style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 500 }}>
                НОВОСТИ — {state.news.length} статей
              </h2>
            </div>
            <NewsList news={state.news} />
          </div>
        </>
      )}
    </div>
  )
}
