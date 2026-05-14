export interface CoinSummary {
  coin_id: string
  coin_name: string
  symbol: string
  close_price: number
  daily_change_pct: number | null
  avg_volume: number | null
  avg_market_cap: number | null
  ma_7d: number | null
  ma_30d: number | null
}

export interface PriceHistory {
  price_date: string
  open_price: number
  close_price: number
  high_price: number
  low_price: number
  daily_change_pct: number | null
  volatility_score: number | null
  avg_volume: number | null
  ma_7d: number | null
  ma_30d: number | null
}

export interface NewsItem {
  title: string
  description: string | null
  url: string
  source: string | null
  published_at: string | null
  sentiment_score: number | null
  sentiment_label: string | null
}

export interface TopMover {
  coin_id: string
  coin_name: string
  symbol: string
  period: string
  close_price: number | null
  change_pct: number | null
  avg_volume: number | null
  mover_type: string
  rank: number
}

export type Period = '24h' | '7d' | '30d'
