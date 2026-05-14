import { useMemo } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { PriceHistory } from '../types'
import { formatDate, formatPrice } from '../utils/format'

interface Props {
  data: PriceHistory[]
}

export function PriceChart({ data }: Props) {
  const chartData = useMemo(() => data.map((d) => ({
    date: formatDate(d.price_date),
    Цена: Number(d.close_price),
    'MA 7д': d.ma_7d !== null ? Number(d.ma_7d) : null,
    'MA 30д': d.ma_30d !== null ? Number(d.ma_30d) : null,
  })), [data])

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 0, left: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="date"
          tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={(v: number) => formatPrice(v)}
          tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={90}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 6,
            fontSize: 12,
          }}
          formatter={(value) => formatPrice(Number(value))}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-muted)' }} />
        <Line
          type="monotone"
          dataKey="Цена"
          stroke="var(--accent)"
          strokeWidth={2}
          dot={false}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="MA 7д"
          stroke="var(--yellow)"
          strokeWidth={1.5}
          strokeDasharray="4 2"
          dot={false}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="MA 30д"
          stroke="var(--green)"
          strokeWidth={1.5}
          strokeDasharray="4 2"
          dot={false}
          connectNulls
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
