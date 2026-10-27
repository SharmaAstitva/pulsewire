import { useParams, Link } from 'react-router-dom'
import { format } from 'date-fns'
import { useArticle, useArticles } from '../hooks/useData'
import { ArticleCardCompact } from '../components/ArticleCard'

function fmt(d) {
  try { return format(new Date(d), 'MMMM d, yyyy') } catch { return '' }
}

function readTime(text) {
  if (!text) return null
  const mins = Math.max(1, Math.round(text.split(/\s+/).length / 200))
  return `${mins} min read`
}

const SENTIMENT_COLOR = {
  positive: { dot: '#16A34A', bg: '#F0FDF4', text: '#166534' },
  negative: { dot: '#DC2626', bg: '#FEF2F2', text: '#991B1B' },
  neutral:  { dot: '#D97706', bg: '#FFFBEB', text: '#92400E' },
}

export function Article() {
  const { id } = useParams()
  const { data: article, isLoading, isError } = useArticle(id)

  const { data: relData } = useArticles({
    category: article?.topic_primary, limit: 5, sort: 'trending',
  })
  const related = (relData?.data || []).filter(a => a.id !== parseInt(id)).slice(0, 4)

  const rt = readTime(article?.content || article?.summary)
  const sentCfg = SENTIMENT_COLOR[article?.sentiment] || SENTIMENT_COLOR.neutral

  if (isLoading) {
    return (
      <div className="max-w-site mx-auto px-4 sm:px-6 py-10 space-y-4 fade-in">
        <div className="skeleton h-4 w-28 rounded" />
        <div className="skeleton h-10 w-3/4 rounded" />
        <div className="skeleton h-10 w-1/2 rounded" />
        <div className="skeleton w-full rounded mt-4" style={{ height: '360px' }} />
        <div className="space-y-2 mt-6">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="skeleton h-4 rounded" style={{ width: i % 3 === 2 ? '75%' : '100%' }} />
          ))}
        </div>
      </div>
    )
  }

  if (isError || !article) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <p className="font-display italic text-ink-muted text-3xl mb-4">Article not found</p>
        <Link to="/" className="font-ui text-sm underline text-ink-muted hover:text-ink transition-colors">
          ← Back to frontpage
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-site mx-auto px-4 sm:px-6 py-8 fade-up">

      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 font-ui text-[11px] text-ink-faint mb-6 pb-4 border-b"
        style={{ borderColor: '#E5E7EB' }}>
        <Link to="/" className="hover:text-ink transition-colors">PulseWire</Link>
        <span>›</span>
        {article.topic_primary && (
          <>
            <span className="text-ink-muted">{article.topic_primary}</span>
            <span>›</span>
          </>
        )}
        <span className="text-ink truncate max-w-xs">{article.source}</span>
      </nav>

      <div className="flex gap-12">
        {/* ── Article body ── */}
        <article className="flex-1 min-w-0 max-w-2xl">

          {/* Category label */}
          {article.topic_primary && (
            <span className="label-dark block mb-2">{article.topic_primary}</span>
          )}

          {/* Headline */}
          <h1 className="font-display font-bold text-ink mb-4"
            style={{ fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)', lineHeight: '1.18' }}>
            {article.title}
          </h1>

          {/* Byline row */}
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 font-ui text-[12px] text-ink-muted
                          pb-5 mb-6 border-b" style={{ borderColor: '#E5E7EB' }}>
            <span className="font-semibold text-ink-soft uppercase tracking-wider text-[11px]">
              {article.source}
            </span>
            {article.author && (
              <>
                <span className="text-ink-light">|</span>
                <span>By {article.author}</span>
              </>
            )}
            {article.published_at && (
              <>
                <span className="text-ink-light">|</span>
                <time>{fmt(article.published_at)}</time>
              </>
            )}
            {rt && (
              <>
                <span className="text-ink-light">|</span>
                <span className="flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <circle cx="12" cy="12" r="10"/><path strokeLinecap="round" d="M12 6v6l4 2"/>
                  </svg>
                  {rt}
                </span>
              </>
            )}
            {article.sentiment && (
              <span className="ml-auto flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-medium"
                style={{ background: sentCfg.bg, color: sentCfg.text }}>
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: sentCfg.dot }} />
                {article.sentiment.charAt(0).toUpperCase() + article.sentiment.slice(1)}
              </span>
            )}
          </div>

          {/* Hero image */}
          {article.image_url && (
            <div className="mb-8 overflow-hidden bg-paper-tint w-full" style={{ height: '380px' }}>
              <img src={article.image_url} alt={article.title}
                className="w-full h-full object-cover" />
            </div>
          )}

          {/* AI Summary callout */}
          {article.summary && (
            <div className="border-l-4 pl-5 mb-8" style={{ borderColor: '#111827' }}>
              <div className="flex items-center gap-2 mb-2">
                <span className="font-ui text-[10px] font-black uppercase tracking-widest
                                 bg-ink text-white px-1.5 py-0.5">AI</span>
                <span className="label">Summary</span>
              </div>
              <p className="font-body text-ink text-lg leading-relaxed" style={{ fontStyle: 'italic' }}>
                {article.summary}
              </p>
            </div>
          )}

          {/* Same story from other outlets (story clustering) */}
          {article.also_covered_by?.length > 0 && (
            <div className="mb-8 p-4 border" style={{ borderColor: '#E5E7EB' }}>
              <p className="label mb-2">
                Also covered by {article.also_covered_by.length} other{' '}
                {article.also_covered_by.length === 1 ? 'source' : 'sources'}
              </p>
              <ul className="space-y-1.5">
                {article.also_covered_by.map(c => (
                  <li key={c.id} className="font-ui text-sm">
                    <a href={c.url} target="_blank" rel="noopener noreferrer"
                      className="text-ink hover:underline">
                      <span className="font-semibold">{c.source}</span>
                      <span className="text-ink-muted"> · {c.title}</span>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Body text */}
          {article.content && (
            <div className="font-body text-ink-soft leading-[1.8] mb-10 space-y-4"
              style={{ fontSize: '1.0625rem' }}>
              <p>{article.content}</p>
            </div>
          )}

          {/* Read original CTA */}
          <div className="pt-6 border-t" style={{ borderColor: '#E5E7EB' }}>
            <a href={article.url} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 font-ui text-[12px] font-bold
                         uppercase tracking-widest text-white transition-colors"
              style={{ background: '#111827' }}
              onMouseEnter={e => e.currentTarget.style.background = '#B91C1C'}
              onMouseLeave={e => e.currentTarget.style.background = '#111827'}
            >
              Read Full Article
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
              </svg>
            </a>
          </div>
        </article>

        {/* ── Related sidebar ── */}
        {related.length > 0 && (
          <aside className="hidden lg:block w-64 shrink-0">
            <div className="border-t-2 pt-3" style={{ borderColor: '#111827' }}>
              <h2 className="label-dark mb-4">More Stories</h2>
              <div className="space-y-3">
                {related.map(a => (
                  <ArticleCardCompact key={a.id} article={a} showBar={false} />
                ))}
              </div>
              <div className="mt-6 pt-4 border-t" style={{ borderColor: '#E5E7EB' }}>
                <Link to="/"
                  className="font-ui text-[11px] font-semibold uppercase tracking-wider
                             text-ink-muted hover:text-ink transition-colors">
                  ← Return to frontpage
                </Link>
              </div>
            </div>
          </aside>
        )}
      </div>
    </div>
  )
}
