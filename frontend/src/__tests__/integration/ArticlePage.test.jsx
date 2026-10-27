import { screen } from '@testing-library/react'
import { Article } from '../../pages/Article'
import { getArticle, getArticles } from '../../api/client'
import { makeArticle, page, renderWithProviders } from '../../test/utils'

vi.mock('../../api/client', () => ({ getArticle: vi.fn(), getArticles: vi.fn() }))

const story = makeArticle({
  id: 42,
  title: 'Nvidia unveils new AI chip',
  summary: 'Nvidia revealed a faster data-centre chip.',
  sentiment: 'positive',
  coverage_count: 3,
  also_covered_by: [
    { id: 43, title: 'Nvidia shows off new processor', source: 'The Verge', url: 'https://verge.example/n' },
    { id: 44, title: 'Chipmaker reveals AI hardware', source: 'BBC Technology', url: 'https://bbc.example/n' },
  ],
})

const renderArticle = (id = 42) => renderWithProviders(<Article />, { route: `/article/${id}`, path: '/article/:id' })

describe('Article page', () => {
  beforeEach(() => {
    getArticle.mockReset()
    getArticles.mockReset().mockResolvedValue(page([story, makeArticle({ id: 50, title: 'Related story' })]))
  })

  it('fetches the article from the URL id and shows the AI summary', async () => {
    getArticle.mockResolvedValue(story)
    renderArticle()
    expect(await screen.findByRole('heading', { name: 'Nvidia unveils new AI chip' })).toBeInTheDocument()
    expect(getArticle).toHaveBeenCalledWith('42')
    expect(screen.getByText('Nvidia revealed a faster data-centre chip.')).toBeInTheDocument()
    expect(screen.getByText('Positive')).toBeInTheDocument()
  })

  it('lists the other outlets that covered the same story', async () => {
    getArticle.mockResolvedValue(story)
    renderArticle()
    expect(await screen.findByText(/also covered by 2 other sources/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /The Verge/ })).toHaveAttribute('href', 'https://verge.example/n')
  })

  it('shows related stories but not the current one', async () => {
    getArticle.mockResolvedValue(story)
    renderArticle()
    expect(await screen.findByText('Related story')).toBeInTheDocument()
    expect(screen.getAllByText('Nvidia unveils new AI chip')).toHaveLength(1)
  })

  it('links to the original article', async () => {
    getArticle.mockResolvedValue(story)
    renderArticle()
    expect(await screen.findByRole('link', { name: /read full article/i }))
      .toHaveAttribute('href', story.url)
  })

  it('shows "not found" when the API returns an error', async () => {
    getArticle.mockRejectedValue(new Error('Article not found'))
    renderArticle(999)
    expect(await screen.findByText('Article not found')).toBeInTheDocument()
  })
})
