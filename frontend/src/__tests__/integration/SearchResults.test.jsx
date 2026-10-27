import { screen } from '@testing-library/react'
import { SearchResults } from '../../components/SearchResults'
import { searchArticles } from '../../api/client'
import { makeArticle, page, renderWithProviders } from '../../test/utils'

vi.mock('../../api/client', () => ({ searchArticles: vi.fn() }))

describe('SearchResults', () => {
  beforeEach(() => {
    searchArticles.mockReset()
  })

  it('shows matching stories and the total', async () => {
    searchArticles.mockResolvedValue(page([makeArticle({ title: 'Cricket final tonight' })], { total: 1 }))
    renderWithProviders(<SearchResults query="cricket" />)
    expect(await screen.findByText('Cricket final tonight')).toBeInTheDocument()
    expect(screen.getByText('1 found')).toBeInTheDocument()
    expect(searchArticles).toHaveBeenCalledWith({ q: 'cricket', limit: 20 })
  })

  it('shows an empty state', async () => {
    searchArticles.mockResolvedValue(page([]))
    renderWithProviders(<SearchResults query="zzzz" />)
    expect(await screen.findByText('No results found')).toBeInTheDocument()
  })

  it('shows an error state', async () => {
    searchArticles.mockRejectedValue(new Error('boom'))
    renderWithProviders(<SearchResults query="cricket" />)
    expect(await screen.findByText(/search failed/i)).toBeInTheDocument()
  })

  it('does not call the API for one-letter queries', () => {
    renderWithProviders(<SearchResults query="c" />)
    expect(searchArticles).not.toHaveBeenCalled()
  })
})
