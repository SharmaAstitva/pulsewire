import { useArticles } from '../hooks/useData'
import { Hero } from '../components/Hero'
import { NewsFeed } from '../components/NewsFeed'
import { Sidebar } from '../components/Sidebar'
import { SearchResults } from '../components/SearchResults'

export function Home({ category, searchQuery, onCategory }) {
  /* Featured = top trending article */
  const { data: heroData, isLoading: heroLoading } = useArticles({
    sort: 'trending', limit: 1, category,
  })
  const featured = heroData?.data?.[0] ?? null

  const isSearching = searchQuery && searchQuery.length >= 2

  return (
    <div>
      {isSearching ? (
        /* ── Search view ──────────────────────────── */
        <div className="max-w-site mx-auto px-4 sm:px-6 py-8">
          <div className="flex gap-10">
            <div className="flex-1 min-w-0">
              <SearchResults query={searchQuery} />
            </div>
            <div className="hidden xl:block w-72 shrink-0">
              <Sidebar activeCategory={category} onCategory={onCategory} />
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* ── Hero — full width within site max ──── */}
          <div className="max-w-site mx-auto px-4 sm:px-6 pt-4">
            <Hero article={featured} isLoading={heroLoading} />
          </div>

          {/* ── Two-column body ──────────────────────── */}
          <div className="max-w-site mx-auto px-4 sm:px-6 py-8">
            <div className="flex gap-10">

              {/* Left 70% — news grid */}
              <div className="flex-1 min-w-0">
                <NewsFeed
                  category={category}
                  skipFirst={!!featured && !category}
                />
              </div>

              {/* Vertical separator */}
              <div className="hidden xl:block w-px bg-gray-200 shrink-0" />

              {/* Right 30% — sidebar */}
              <div className="hidden xl:block w-72 shrink-0">
                <Sidebar activeCategory={category} onCategory={onCategory} />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
