import { screen } from '@testing-library/react'
import { ArticleCard } from '../../components/ArticleCard'
import { makeArticle, renderWithProviders } from '../../test/utils'

describe('ArticleCard', () => {
  it('links the headline to the article page', () => {
    renderWithProviders(<ArticleCard article={makeArticle({ id: 7, title: 'Rates rise again' })} />)
    expect(screen.getByRole('link', { name: 'Rates rise again' })).toHaveAttribute('href', '/article/7')
  })

  it('shows topic and sentiment', () => {
    renderWithProviders(<ArticleCard article={makeArticle({ topic_primary: 'Science', sentiment: 'negative' })} />)
    expect(screen.getByText('Science')).toBeInTheDocument()
    expect(screen.getByText('Negative')).toBeInTheDocument()
  })

  it('shows the source count only when several outlets covered the story', () => {
    const { rerender } = renderWithProviders(<ArticleCard article={makeArticle({ coverage_count: 1 })} />)
    expect(screen.queryByText(/sources/)).not.toBeInTheDocument()
    rerender(<ArticleCard article={makeArticle({ coverage_count: 3 })} />)
    expect(screen.getByText(/3 sources/)).toBeInTheDocument()
  })

  it('uses the image when there is one, otherwise a source initial', () => {
    const { rerender } = renderWithProviders(
      <ArticleCard article={makeArticle({ title: 'With image', image_url: 'https://img.example/a.jpg' })} />,
    )
    expect(screen.getByRole('img', { name: 'With image' })).toHaveAttribute('src', 'https://img.example/a.jpg')
    rerender(<ArticleCard article={makeArticle({ image_url: null, source: 'Guardian' })} />)
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    expect(screen.getByText('G')).toBeInTheDocument()
  })
})
