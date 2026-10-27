import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

/* Render with the same providers the real app uses (React Query + Router). */
export function renderWithProviders(ui, { route = '/', path = '*' } = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  const wrap = (node) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path={path} element={node} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
  const result = render(wrap(ui))
  return { ...result, rerender: (next) => result.rerender(wrap(next)) }
}

let nextId = 1
export function makeArticle(overrides = {}) {
  const id = overrides.id ?? nextId++
  return {
    id,
    url: `https://news.example/${id}`,
    title: `Headline number ${id}`,
    summary: `Summary for story ${id}.`,
    content: `Body text for story ${id}.`,
    image_url: null,
    source: 'Example News',
    author: null,
    published_at: '2026-10-24T10:00:00Z',
    sentiment: 'neutral',
    sentiment_score: 0.8,
    topic_primary: 'Technology',
    topic_secondary: 'Finance',
    coverage_count: 1,
    trending_score: 0.5,
    ...overrides,
  }
}

export function page(data, { page = 1, pages = 1, total = data.length, limit = 10 } = {}) {
  return { data, meta: { total, page, limit, pages } }
}
