import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'

function relTime(d) {
  try { return formatDistanceToNow(new Date(d), { addSuffix: true }) } catch { return '' }
}

function readTime(text) {
  if (!text) return null
  const mins = Math.max(1, Math.round(text.split(/\s+/).length / 200))
  return `${mins} min`
}

const SENTIMENT_DOT = {
  positive: 'dot-positive',
  neutral:  'dot-neutral',
  negative: 'dot-negative',
}

const SENTIMENT_LABEL = {
  positive: 'Positive',
  neutral:  'Neutral',
  negative: 'Negative',
}

/* ── Main grid card (image top, content below) ── */
export function ArticleCard({ article }) {
  const rt = readTime(article.content || article.summary)

  return (
    <article className="flex flex-col group">
      {/* Image */}
      <Link to={`/article/${article.id}`}
        className="block overflow-hidden bg-paper-tint w-full mb-3 flex-shrink-0"
        style={{ height: '200px' }}>
        {article.image_url ? (
          <img
            src={article.image_url}
            alt={article.title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
            onError={e => { e.currentTarget.style.display = 'none' }}
          />
        ) : (
          <div className="w-full h-full bg-gray-100 flex items-center justify-center">
            <span className="font-display italic text-gray-300 text-2xl">{article.source?.[0] || '?'}</span>
          </div>
        )}
      </Link>

      {/* Category + sentiment dot */}
      {(article.topic_primary || article.sentiment) && (
        <div className="flex items-center gap-2 mb-1.5">
          {article.topic_primary && (
            <span className="label-dark">{article.topic_primary}</span>
          )}
          {article.sentiment && (
            <span className="flex items-center gap-1">
              <span className={`w-1.5 h-1.5 rounded-full inline-block ${SENTIMENT_DOT[article.sentiment] || 'dot-neutral'}`} />
              <span className="font-ui text-[11px] text-ink-muted">{SENTIMENT_LABEL[article.sentiment]}</span>
            </span>
          )}
          {article.coverage_count > 1 && (
            <span className="font-ui text-[11px] text-ink-muted">
              · {article.coverage_count} sources
            </span>
          )}
        </div>
      )}

      {/* Headline */}
      <Link to={`/article/${article.id}`}>
        <h3 className="font-display font-bold text-ink leading-snug mb-2 text-lg sm:text-xl
                       hover:text-gray-600 transition-colors"
          style={{ lineHeight: '1.3' }}>
          {article.title}
        </h3>
      </Link>

      {/* Summary */}
      {article.summary && (
        <p className="font-ui text-sm text-ink-soft leading-relaxed line-clamp-3 mb-3">
          {article.summary}
        </p>
      )}

      {/* Footer meta */}
      <div className="mt-auto flex items-center gap-1.5 flex-wrap pt-1">
        <span className="font-ui text-[11px] text-ink-muted font-medium">{article.source}</span>
        {rt && (
          <>
            <span className="text-ink-light text-xs">|</span>
            <span className="font-ui text-[11px] text-ink-muted flex items-center gap-0.5">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <circle cx="12" cy="12" r="10" /><path strokeLinecap="round" d="M12 6v6l4 2" />
              </svg>
              {rt}
            </span>
          </>
        )}
        {article.published_at && (
          <>
            <span className="text-ink-light text-xs ml-auto">
              <time className="font-ui text-[11px] text-ink-muted">{relTime(article.published_at)}</time>
            </span>
          </>
        )}
      </div>
    </article>
  )
}

/* ── Compact list item (trending sidebar) ── */
export function ArticleCardCompact({ article, rank, showBar }) {
  const trendPct = article.trending_score ? Math.min(100, Math.round(article.trending_score * 100)) : 0

  const barColor = trendPct > 65
    ? '#16A34A'
    : trendPct > 35
    ? '#D97706'
    : '#DC2626'

  return (
    <article className="pt-3 first:pt-0 border-t first:border-t-0" style={{ borderColor: '#F3F4F6' }}>
      {article.topic_primary && (
        <span className="label-dark block mb-1">{article.topic_primary}</span>
      )}
      <Link to={`/article/${article.id}`}>
        <h4 className="font-display font-bold text-ink text-[0.9375rem] leading-snug mb-1
                       hover:text-gray-600 transition-colors line-clamp-2">
          {article.title}
        </h4>
      </Link>
      <div className="flex items-center justify-between">
        <span className="font-ui text-[11px] text-ink-faint">
          {article.published_at
            ? (() => { try { return formatDistanceToNow(new Date(article.published_at), { addSuffix: true }) } catch { return '' }})()
            : ''}
        </span>
      </div>
      {showBar && (
        <div className="mt-2 h-0.5 w-full bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full rounded-full" style={{ width: `${trendPct}%`, background: barColor }} />
        </div>
      )}
    </article>
  )
}

/* ── Editor's Picks horizontal card ── */
export function ArticleCardPickH({ article }) {
  return (
    <article className="flex gap-3 group">
      {article.image_url && (
        <Link to={`/article/${article.id}`}
          className="shrink-0 overflow-hidden bg-paper-tint" style={{ width: '80px', height: '60px' }}>
          <img
            src={article.image_url}
            alt={article.title}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            onError={e => { e.currentTarget.style.display = 'none' }}
          />
        </Link>
      )}
      <div className="flex-1 min-w-0">
        {article.topic_primary && (
          <span className="label-dark block mb-1">{article.topic_primary}</span>
        )}
        <Link to={`/article/${article.id}`}>
          <h4 className="font-display font-semibold text-ink text-sm leading-snug mb-1
                         hover:text-gray-600 transition-colors line-clamp-2">
            {article.title}
          </h4>
        </Link>
        {article.published_at && (
          <time className="font-ui text-[11px] text-ink-faint">
            {(() => { try { return formatDistanceToNow(new Date(article.published_at), { addSuffix: true }) } catch { return '' }})()}
          </time>
        )}
      </div>
    </article>
  )
}
