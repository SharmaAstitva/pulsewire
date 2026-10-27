import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'

function fmt(d) {
  if (!d) return ''
  try {
    return new Intl.DateTimeFormat('en-US', { month: 'long', day: 'numeric', year: 'numeric' }).format(new Date(d))
  } catch { return '' }
}

function readTime(text) {
  if (!text) return null
  const words = text.split(/\s+/).length
  const mins = Math.max(1, Math.round(words / 200))
  return `${mins} min read`
}

function SentimentBadge({ sentiment }) {
  const cfg = {
    positive: { cls: 'badge badge-positive', label: 'Positive' },
    negative: { cls: 'badge badge-negative', label: 'Negative' },
    neutral:  { cls: 'badge badge-neutral',  label: 'Neutral' },
  }[sentiment] || { cls: 'badge badge-neutral', label: 'Neutral' }
  return <span className={cfg.cls}>{cfg.label}</span>
}

export function Hero({ article, isLoading }) {
  if (isLoading) {
    return (
      <div className="w-full h-[420px] skeleton mb-0" />
    )
  }
  if (!article) return null

  const rt = readTime(article.content || article.summary)

  return (
    <section className="fade-up">
      {/* Full-bleed image with overlay */}
      <Link to={`/article/${article.id}`} className="block relative w-full h-[420px] overflow-hidden group">
        {/* Image */}
        {article.image_url ? (
          <img
            src={article.image_url}
            alt={article.title}
            className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-[1.02]"
            onError={e => { e.currentTarget.style.display = 'none' }}
          />
        ) : (
          <div className="absolute inset-0 bg-gray-300" />
        )}

        {/* Gradient overlay — dark at bottom */}
        <div className="absolute inset-0" style={{
          background: 'linear-gradient(to bottom, rgba(0,0,0,0.08) 0%, rgba(0,0,0,0.18) 40%, rgba(0,0,0,0.72) 100%)'
        }} />

        {/* Content over image */}
        <div className="absolute inset-0 flex flex-col justify-end p-6 sm:p-8">
          {/* Category badge */}
          {article.topic_primary && (
            <div className="mb-3">
              <span className="inline-block px-2 py-0.5 text-[11px] font-ui font-700 tracking-widest uppercase text-white border border-white/60" style={{ fontWeight: 700 }}>
                {article.topic_primary}
              </span>
            </div>
          )}

          {/* Headline */}
          <h1 className="font-display font-bold text-white leading-tight mb-3 max-w-3xl"
            style={{ fontSize: 'clamp(1.6rem, 3vw, 2.4rem)', lineHeight: '1.2' }}>
            {article.title}
          </h1>

          {/* Summary */}
          {article.summary && (
            <p className="font-ui text-white/85 text-sm leading-relaxed mb-4 max-w-2xl line-clamp-2 hidden sm:block">
              {article.summary}
            </p>
          )}

          {/* Meta row */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-ui text-white/80 text-xs font-medium">{article.source}</span>
            {article.published_at && (
              <>
                <span className="text-white/40">|</span>
                <time className="font-ui text-white/70 text-xs">{fmt(article.published_at)}</time>
              </>
            )}
            {rt && (
              <>
                <span className="text-white/40">|</span>
                <span className="font-ui text-white/70 text-xs flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" strokeLinecap="round" />
                  </svg>
                  {rt}
                </span>
              </>
            )}
            {article.sentiment && <SentimentBadge sentiment={article.sentiment} />}
          </div>
        </div>
      </Link>

      {/* "Read full story" bar below hero */}
      <div className="flex justify-end items-center px-0 py-2.5 border-b" style={{ borderColor: '#E5E7EB' }}>
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-ui text-[12px] text-ink-muted hover:text-ink transition-colors flex items-center gap-1.5"
        >
          Read full story
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </section>
  )
}
