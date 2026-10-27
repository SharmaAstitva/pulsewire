import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NewsFeed } from '../../components/NewsFeed'
import { getArticles } from '../../api/client'
import { makeArticle, page, renderWithProviders } from '../../test/utils'

vi.mock('../../api/client', () => ({ getArticles: vi.fn() }))

const tech = [1, 2, 3].map(id => makeArticle({ id, title: `Tech story ${id}`, topic_primary: 'Technology' }))
const techPage2 = [4, 5].map(id => makeArticle({ id, title: `Tech story ${id}`, topic_primary: 'Technology' }))
const sports = [10, 11].map(id => makeArticle({ id, title: `Sports story ${id}`, topic_primary: 'Sports' }))

function fakeApi({ category, page: p = 1, limit }) {
  if (limit === 3) return Promise.resolve(page([]))          // Editor's Picks strip
  if (category === 'Sports') return Promise.resolve(page(sports))
  if (p === 2) return Promise.resolve(page(techPage2, { page: 2, pages: 2, total: 5 }))
  return Promise.resolve(page(tech, { pages: 2, total: 5 }))
}

describe('NewsFeed', () => {
  beforeEach(() => {
    getArticles.mockReset().mockImplementation(fakeApi)
  })

  it('loads stories from the API and shows the total', async () => {
    renderWithProviders(<NewsFeed category="Technology" />)
    expect(await screen.findByText('Tech story 1')).toBeInTheDocument()
    expect(screen.getByText('5 articles')).toBeInTheDocument()
    expect(getArticles).toHaveBeenCalledWith(expect.objectContaining({ category: 'Technology', page: 1 }))
  })

  it('appends the next page on "Load more" and then hides the button', async () => {
    renderWithProviders(<NewsFeed category="Technology" />)
    await userEvent.click(await screen.findByRole('button', { name: /load more/i }))
    expect(await screen.findByText('Tech story 5')).toBeInTheDocument()
    expect(screen.getByText('Tech story 1')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /load more/i })).not.toBeInTheDocument()
  })

  it('skips the first story when it is already shown in the hero', async () => {
    renderWithProviders(<NewsFeed skipFirst />)
    await screen.findByText('Tech story 2')
    expect(screen.queryByText('Tech story 1')).not.toBeInTheDocument()
  })

  // Written before the fix (TDD): this failed, old-category stories stayed on screen.
  it('resets the list when the category changes after loading more', async () => {
    const { rerender } = renderWithProviders(<NewsFeed category="Technology" />)
    await userEvent.click(await screen.findByRole('button', { name: /load more/i }))
    await screen.findByText('Tech story 5')

    rerender(<NewsFeed category="Sports" />)

    expect(await screen.findByText('Sports story 10')).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByText('Tech story 1')).not.toBeInTheDocument())
    expect(screen.queryByText('Tech story 5')).not.toBeInTheDocument()
  })

  it('shows an error message when the API fails', async () => {
    getArticles.mockRejectedValue(new Error('Network Error'))
    renderWithProviders(<NewsFeed />)
    expect(await screen.findByText(/could not load articles/i)).toHaveTextContent('Network Error')
  })

  it('shows an empty state when there are no stories', async () => {
    getArticles.mockResolvedValue(page([]))
    renderWithProviders(<NewsFeed category="Health" />)
    expect(await screen.findByText('No stories found')).toBeInTheDocument()
  })
})
