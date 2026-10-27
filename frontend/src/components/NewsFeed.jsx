import { useEffect, useState } from 'react'
import { useArticles } from '../hooks/useData'
import { getArticles } from '../api/client'
import { ArticleCard, ArticleCardPickH } from './ArticleCard'

/* Skeleton card for loading state */
function CardSkeleton() {
  return (
    <div className="flex flex-col">
      <div className="skeleton w-full mb-3" style={{ height: '200px' }} />
      <div className="skeleton h-3 w-20 mb-2 rounded" />
      <div className="skeleton h-5 w-full mb-1 rounded" />
      <div className="skeleton h-5 w-4/5 mb-3 rounded" />
      <div className="skeleton h-3 w-full mb-1 rounded" />
      <div className="skeleton h-3 w-3/4 rounded" />
    </div>
  )
}

/* Editor's Picks horizontal strip — bottom of feed */
function EditorsPicks({ category }) {
  const { data } = useArticles({ category, sort: 'trending', limit: 3, page: 3 })
  const picks = data?.data || []
  if (!picks.length) return null

  return (
    <section className="mt-12 pt-6 border-t-2" style={{ borderColor: '#111827' }}>
      <h2 className="label-dark mb-5">Editor's Picks</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pb-8 border-b" style={{ borderColor: '#E5E7EB' }}>
        {picks.map(a => (
          <ArticleCardPickH key={a.id} article={a} />
        ))}
      </div>
    </section>
  )
}

export function NewsFeed({ category, skipFirst = false }) {
  const [page, setPage]       = useState(1)
  const [allArticles, setAll] = useState(null)
  const [loadingMore, setLoadingMore] = useState(false)

  /* A new category is a new list: drop pages loaded for the previous one */
  useEffect(() => {
    setPage(1)
    setAll(null)
  }, [category])

  /* Primary fetch */
  const { data, isLoading, isError, error } = useArticles({
    category, sort: 'trending', limit: 10, page: 1,
  })

  /* On first successful load, seed allArticles */
  const baseArticles = data?.data || []
  const displayArticles = allArticles ?? (skipFirst ? baseArticles.slice(1) : baseArticles)
  const meta = data?.meta

  /* Load more */
  const handleLoadMore = async () => {
    setLoadingMore(true)
    try {
      const nextPage = page + 1
      const res = await getArticles({ category, sort: 'trending', limit: 10, page: nextPage })
      const next = res?.data || []
      setAll(prev => {
        const existing = prev ?? displayArticles
        // dedupe by id
        const ids = new Set(existing.map(a => a.id))
        return [...existing, ...next.filter(a => !ids.has(a.id))]
      })
      setPage(nextPage)
    } catch (e) {
      console.error(e)
    } finally {
      setLoadingMore(false)
    }
  }

  const currentArticles = allArticles ?? displayArticles
  const hasMore = meta ? page < meta.pages : false

  return (
    <section>
      {/* Section header */}
      <div className="flex items-center justify-between border-t-2 pt-3 mb-6"
        style={{ borderColor: '#111827' }}>
        <div className="flex items-center gap-2">
          <h2 className="label-dark">Latest Stories</h2>
          {meta?.total != null && (
            <span className="font-ui text-[11px] text-ink-faint ml-1">
              {meta.total} articles
            </span>
          )}
        </div>
      </div>

      {/* Error */}
      {isError && (
        <div className="py-8 text-center border border-red-100 bg-red-50">
          <p className="font-ui text-sm text-red-600">
            ⚠ Could not load articles — {error?.message}
          </p>
        </div>
      )}

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-10 stagger">
          {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : currentArticles.length === 0 ? (
        <div className="py-16 text-center">
          <p className="font-display italic text-ink-muted text-2xl">No stories found</p>
          <p className="font-ui text-sm text-ink-faint mt-2">Try a different topic or check back shortly</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-10 stagger">
          {currentArticles.map(a => (
            <ArticleCard key={a.id} article={a} />
          ))}
        </div>
      )}

      {/* Load more */}
      {!isLoading && hasMore && (
        <div className="flex justify-center mt-10">
          <button
            onClick={handleLoadMore}
            disabled={loadingMore}
            className="font-ui text-sm font-medium text-ink border border-ink px-8 py-2.5
                       hover:bg-ink hover:text-white transition-colors duration-150 disabled:opacity-50"
          >
            {loadingMore ? (
              <span className="flex items-center gap-2">
                <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                Loading…
              </span>
            ) : 'Load more stories'}
          </button>
        </div>
      )}

      {/* Editor's Picks */}
      <EditorsPicks category={category} />
    </section>
  )
}
