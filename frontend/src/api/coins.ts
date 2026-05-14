import type { CoinSummary, NewsItem, Period, PriceHistory, TopMover } from '../types'
import { api } from './client'

const periodToDays: Record<Period, number> = { '24h': 1, '7d': 7, '30d': 30 }

export const getCoins = () =>
  api.get<CoinSummary[]>('/coins').then((r) => r.data)

export const getCoinHistory = (coinId: string, period: Period) =>
  api
    .get<PriceHistory[]>(`/coins/${coinId}/history`, {
      params: { days: periodToDays[period] },
    })
    .then((r) => r.data)

export const getCoinNews = (coinId: string, period: Period) =>
  api
    .get<NewsItem[]>(`/coins/${coinId}/news`, {
      params: { days: periodToDays[period] },
    })
    .then((r) => r.data)

export const getTopGainers = (period: Period) =>
  api.get<TopMover[]>('/top-gainers', { params: { period } }).then((r) => r.data)

export const getTopLosers = (period: Period) =>
  api.get<TopMover[]>('/top-losers', { params: { period } }).then((r) => r.data)
