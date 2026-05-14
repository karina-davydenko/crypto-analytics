import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { NewsItem } from '../types'
import { formatDate } from '../utils/format'

interface Props {
  news: NewsItem[]
}

interface DaySentiment {
  date: string
  sentiment: number
  count: number
}

function groupByDate(news: NewsItem[]): DaySentiment[] {
  const byDate = new Map<string, { sum: number; count: number }>()

  for (const item of news) {
    if (!item.published_at || item.sentiment_score === null) continue
    const dateKey = item.published_at.slice(0, 10)
    const existing = byDate.get(dateKey) ?? { sum: 0, count: 0 }
    byDate.set(dateKey, {
      sum: existing.sum + Number(item.sentiment_score),
      count: existing.count + 1,
    })
  }

  return Array.from(byDate.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([dateKey, { sum, count }]) => ({
      date: formatDate(dateKey),
      sentiment: Number((sum / count).toFixed(3)),
      count,
    }))
}

export function SentimentChart({ news }: Props) {
  const data = useMemo(() => groupByDate(news), [news])

  if (data.length === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 280, color: 'var(--text-muted)' }}>
        Нет данных по новостям
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[-1, 1]}
          tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 6,
            fontSize: 12,
          }}
          formatter={(value) => [`${Number(value).toFixed(3)}`, 'Sentiment']}
        />
        <Bar dataKey="sentiment" radius={[3, 3, 0, 0]}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.sentiment >= 0 ? 'var(--green)' : 'var(--red)'}
              fillOpacity={0.7}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
