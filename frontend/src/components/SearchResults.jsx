import { useSearch } from '../hooks/useData'
import { ArticleCard } from './ArticleCard'

function SearchSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-10">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="flex flex-col">
          <div className="skeleton w-full mb-3" style={{ height: '200px' }} />
          <div className="skeleton h-3 w-20 mb-2 rounded" />
          <div className="skeleton h-5 w-full mb-1 rounded" />
          <div className="skeleton h-5 w-4/5 rounded" />
        </div>
      ))}
    </div>
  )
}

export function SearchResults({ query }) {
  const { data, isLoading, isError } = useSearch(query)
  const articles = data?.data || []
  const total    = data?.meta?.total ?? 0

  return (
    <div className="fade-up">
      {/* Header */}
      <div className="border-t-2 pt-3 mb-6" style={{ borderColor: '#111827' }}>
        <div className="flex items-center gap-2">
          <h2 className="label-dark">
            Search results for "
            <span className="normal-case tracking-normal" style={{ fontFamily: 'Inter' }}>{query}</span>
            "
          </h2>
          {!isLoading && (
            <span className="font-ui text-[11px] text-ink-faint">
              {total} found
            </span>
          )}
        </div>
      </div>

      {isLoading && <SearchSkeleton />}

      {isError && (
        <p className="font-ui text-sm text-red-600 py-4">Search failed. Please try again.</p>
      )}

      {!isLoading && !isError && articles.length === 0 && (
        <div className="py-16 text-center">
          <p className="font-display italic text-ink-muted text-2xl">No results found</p>
          <p className="font-ui text-sm text-ink-faint mt-2">
            Try different keywords or browse by topic
          </p>
        </div>
      )}

      {!isLoading && articles.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-10 stagger">
          {articles.map(a => <ArticleCard key={a.id} article={a} />)}
        </div>
      )}
    </div>
  )
}
