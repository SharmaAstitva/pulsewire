import { useState } from 'react'
import { useTrending, useCategories } from '../hooks/useData'
import { ArticleCardCompact } from './ArticleCard'

/* ── Trending Now ── */
function TrendingNow({ category }) {
  const { data: articles, isLoading } = useTrending({ limit: 5, category })

  return (
    <section>
      <div className="flex items-center gap-2 border-t-2 border-ink pt-3 mb-4">
        <svg className="w-3.5 h-3.5 text-ink" fill="currentColor" viewBox="0 0 24 24">
          <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6h-6z"/>
        </svg>
        <h2 className="label-dark">Trending Now</h2>
      </div>
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="space-y-1.5">
              <div className="skeleton h-3 w-16 rounded" />
              <div className="skeleton h-4 w-full rounded" />
              <div className="skeleton h-4 w-4/5 rounded" />
              <div className="skeleton h-1.5 w-full rounded mt-1" />
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {(articles || []).map((a, i) => (
            <ArticleCardCompact key={a.id} article={a} rank={i} showBar={true} />
          ))}
        </div>
      )}
    </section>
  )
}

/* ── Sentiment Pulse ── */
function SentimentPulse({ category }) {
  const { data: articles } = useTrending({ limit: 8, category })

  if (!articles?.length) return null

  const counts = { positive: 0, neutral: 0, negative: 0 }
  articles.forEach(a => a.sentiment && counts[a.sentiment]++)
  const total = articles.length
  const pct = k => Math.round((counts[k] / total) * 100)
  const posPct = pct('positive')
  const neuPct = pct('neutral')
  const negPct = pct('negative')

  return (
    <section className="border-t-2 border-ink pt-3">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-3.5 h-3.5 text-ink" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <h2 className="label-dark">Sentiment Pulse</h2>
      </div>

      {/* Segmented bar */}
      <div className="flex h-2 w-full rounded-sm overflow-hidden gap-px mb-3">
        {posPct > 0 && (
          <div style={{ width: `${posPct}%`, background: '#16A34A' }} />
        )}
        {neuPct > 0 && (
          <div style={{ width: `${neuPct}%`, background: '#D97706' }} />
        )}
        {negPct > 0 && (
          <div style={{ width: `${negPct}%`, background: '#DC2626' }} />
        )}
      </div>

      {/* Legend rows */}
      <div className="space-y-1.5">
        {[
          { key: 'positive', label: 'Positive', pct: posPct, color: '#16A34A', bg: '#F0FDF4' },
          { key: 'neutral',  label: 'Neutral',  pct: neuPct, color: '#D97706', bg: '#FFFBEB' },
          { key: 'negative', label: 'Negative', pct: negPct, color: '#DC2626', bg: '#FFF1F2' },
        ].map(({ key, label, pct: p, color, bg }) => (
          <div key={key} className="flex items-center justify-between text-xs font-ui">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color }} />
              <span className="text-ink-muted">{label}</span>
            </div>
            <div className="flex items-center gap-2 text-ink-muted">
              <span>{counts[key]} {counts[key] === 1 ? 'story' : 'stories'}</span>
              <span className="font-semibold" style={{ color }}>{p}%</span>
            </div>
          </div>
        ))}
      </div>

      <p className="font-ui text-[10px] text-ink-faint mt-3">
        Based on {total} articles analyzed by AI
      </p>
    </section>
  )
}

/* ── Browse by Topic ── */
function BrowseTopics({ activeCategory, onCategory }) {
  const { data: cats, isLoading } = useCategories()

  return (
    <section className="border-t-2 border-ink pt-3">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-3.5 h-3.5 text-ink" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
        </svg>
        <h2 className="label-dark">Browse by Topic</h2>
      </div>

      {isLoading ? (
        <div className="space-y-1">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="skeleton h-9 rounded" />
          ))}
        </div>
      ) : (
        <div className="space-y-0.5">
          <button
            onClick={() => onCategory(null)}
            className={`w-full flex items-center justify-between px-3 py-2 text-sm font-ui transition-colors
              ${!activeCategory ? 'bg-ink text-white font-semibold' : 'text-ink hover:bg-paper-tint'}`}
          >
            <span>All</span>
            {!activeCategory && <span className="font-mono text-xs text-white/60">{cats?.reduce((s, c) => s + c.count, 0) || ''}</span>}
          </button>
          {(cats || []).map(cat => (
            <button
              key={cat.name}
              onClick={() => onCategory(activeCategory === cat.name ? null : cat.name)}
              className={`w-full flex items-center justify-between px-3 py-2 text-sm font-ui transition-colors
                ${activeCategory === cat.name ? 'bg-ink text-white font-semibold' : 'text-ink hover:bg-paper-tint'}`}
            >
              <span>{cat.name}</span>
              <span className={`font-mono text-xs ${activeCategory === cat.name ? 'text-white/60' : 'text-ink-faint'}`}>
                {cat.count}
              </span>
            </button>
          ))}
        </div>
      )}
    </section>
  )
}

/* ── Newsletter card ── */
function NewsletterCard() {
  const [email, setEmail] = useState('')
  const [done, setDone] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (email) setDone(true)
  }

  return (
    <section className="border border-rule-DEFAULT p-4" style={{ borderColor: '#E5E7EB' }}>
      <h3 className="font-display font-bold text-ink text-base mb-1">The Daily Briefing</h3>
      <p className="font-ui text-sm text-ink-muted mb-3 leading-relaxed">
        Top stories curated by AI, delivered each morning before 7am.
      </p>
      {done ? (
        <p className="font-ui text-sm text-green-700 font-medium">✓ You're subscribed!</p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-2">
          <input
            type="email"
            placeholder="your@email.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="input-field"
            required
          />
          <button type="submit"
            className="w-full py-2 text-[12px] font-ui font-bold uppercase tracking-widest text-white transition-colors"
            style={{ background: '#111827' }}
            onMouseEnter={e => e.currentTarget.style.background = '#B91C1C'}
            onMouseLeave={e => e.currentTarget.style.background = '#111827'}
          >
            Subscribe Free
          </button>
        </form>
      )}
    </section>
  )
}

/* ── Full Sidebar ── */
export function Sidebar({ activeCategory, onCategory }) {
  return (
    <aside className="space-y-6 w-full">
      <TrendingNow category={activeCategory} />
      <SentimentPulse category={activeCategory} />
      <BrowseTopics activeCategory={activeCategory} onCategory={onCategory} />
      <NewsletterCard />
    </aside>
  )
}
