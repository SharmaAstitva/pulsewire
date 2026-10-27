/* Whole-app integration: real routing, layout, hooks and components.
   Only the HTTP layer (api/client) is replaced with an in-memory fake. */
import { screen, waitFor, within } from '@testing-library/react'
import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../../App'
import * as api from '../../api/client'
import { makeArticle, page } from '../../test/utils'

vi.mock('../../api/client', () => ({
  getArticles: vi.fn(), getArticle: vi.fn(), getTrending: vi.fn(),
  getCategories: vi.fn(), searchArticles: vi.fn(),
}))

const stories = [
  makeArticle({ id: 1, title: 'Lead story about the economy', topic_primary: 'Finance', sentiment: 'negative' }),
  makeArticle({ id: 2, title: 'Second story about chips', topic_primary: 'Technology', sentiment: 'positive' }),
  makeArticle({ id: 3, title: 'Third story about football', topic_primary: 'Sports' }),
]

beforeEach(() => {
  window.history.pushState({}, '', '/')
  api.getArticles.mockReset().mockImplementation(({ category } = {}) =>
    Promise.resolve(page(category ? stories.filter(s => s.topic_primary === category) : stories)))
  api.getTrending.mockReset().mockResolvedValue(stories)
  api.getCategories.mockReset().mockResolvedValue([
    { name: 'Finance', count: 1, avg_sentiment: -1 },
    { name: 'Technology', count: 1, avg_sentiment: 1 },
    { name: 'Sports', count: 1, avg_sentiment: 0 },
  ])
  api.searchArticles.mockReset().mockImplementation(({ q }) =>
    Promise.resolve(page(stories.filter(s => s.title.toLowerCase().includes(q.toLowerCase())))))
})

describe('PulseWire app', () => {
  it('renders the front page from the API', async () => {
    render(<App />)
    expect((await screen.findAllByText('Lead story about the economy')).length).toBeGreaterThan(0)
    expect(screen.getAllByText('Second story about chips').length).toBeGreaterThan(0)
    expect(api.getCategories).toHaveBeenCalled()
    expect(api.getTrending).toHaveBeenCalled()
  })

  it('searches after the user stops typing', async () => {
    const user = userEvent.setup()
    render(<App />)
    await user.click(await screen.findByRole('button', { name: 'Search' }))
    await user.type(screen.getByPlaceholderText('Search articles…'), 'football')

    expect(await screen.findByText(/search results for/i)).toBeInTheDocument()
    expect(await screen.findByText('1 found')).toBeInTheDocument()
    await waitFor(() => expect(api.searchArticles).toHaveBeenCalledWith(expect.objectContaining({ q: 'football' })))
    // Debounced: one request for the final query, not one per keystroke
    expect(api.searchArticles.mock.calls.every(([p]) => p.q === 'football')).toBe(true)
  })

  it('navigates to the article page when a headline is clicked', async () => {
    const user = userEvent.setup()
    api.getArticle.mockResolvedValue({ ...stories[1], also_covered_by: [] })
    render(<App />)
    const [link] = await screen.findAllByRole('link', { name: 'Second story about chips' })
    await user.click(link)
    expect(await screen.findByRole('heading', { name: 'Second story about chips' })).toBeInTheDocument()
    expect(window.location.pathname).toBe('/article/2')
  })

  it('filters the feed by topic from the sidebar', async () => {
    const user = userEvent.setup()
    render(<App />)
    const topics = (await screen.findAllByText('Sports')).map(el => el.closest('button')).filter(Boolean)
    await user.click(topics[topics.length - 1])
    await waitFor(() =>
      expect(api.getArticles).toHaveBeenCalledWith(expect.objectContaining({ category: 'Sports' })))
    const feed = screen.getByText('Latest Stories').closest('section')
    await waitFor(() => expect(within(feed).queryByText('Second story about chips')).not.toBeInTheDocument())
  })
})
