import type { NewsItem } from '../types'

interface Props {
  news: NewsItem[]
}

function sentimentClass(label: string | null): string {
  if (label === 'positive') return 'badge badge-positive'
  if (label === 'negative') return 'badge badge-negative'
  return 'badge badge-neutral'
}

function sentimentText(label: string | null): string {
  if (label === 'positive') return 'Позитив'
  if (label === 'negative') return 'Негатив'
  return 'Нейтрально'
}

function formatTime(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function NewsList({ news }: Props) {
  if (news.length === 0) {
    return <p style={{ color: 'var(--text-muted)', padding: '16px' }}>Новостей не найдено</p>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {news.map((item) => (
        <a
          key={item.url}
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="news-item"
          style={{
            padding: '12px 16px',
            borderBottom: '1px solid var(--border)',
            textDecoration: 'none',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
            <span style={{ color: 'var(--text)', fontSize: 13, lineHeight: 1.5, flex: 1 }}>
              {item.title}
            </span>
            <span className={sentimentClass(item.sentiment_label)} style={{ flexShrink: 0 }}>
              {sentimentText(item.sentiment_label)}
            </span>
          </div>
          <div style={{ marginTop: 4, display: 'flex', gap: 12, color: 'var(--text-muted)', fontSize: 12 }}>
            {item.source && <span>{item.source}</span>}
            <span>{formatTime(item.published_at)}</span>
          </div>
        </a>
      ))}
    </div>
  )
}
