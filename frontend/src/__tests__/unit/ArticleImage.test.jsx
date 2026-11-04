import { fireEvent, render, screen } from '@testing-library/react'
import { ArticleImage } from '../../components/ArticleImage'
import { makeArticle } from '../../test/utils'

describe('ArticleImage', () => {
  it('shows the photo when the article has one', () => {
    render(<ArticleImage article={makeArticle({ title: 'Rates rise', image_url: 'https://img.example/a.jpg' })} />)
    const img = screen.getByRole('img', { name: 'Rates rise' })
    expect(img.tagName).toBe('IMG')
    expect(img).toHaveAttribute('src', 'https://img.example/a.jpg')
  })

  it('shows a topic-coloured placeholder naming the source when there is no image', () => {
    render(<ArticleImage article={makeArticle({
      title: 'Arsenal win derby', image_url: null, source: 'Guardian Sport', topic_primary: 'Sports',
    })} />)
    const placeholder = screen.getByRole('img', { name: 'Arsenal win derby' })
    expect(placeholder.tagName).toBe('DIV')
    expect(placeholder).toHaveTextContent('Guardian Sport')
  })

  it('swaps a broken image for the placeholder', () => {
    render(<ArticleImage article={makeArticle({ title: 'Broken', image_url: 'https://img.example/404.jpg', source: 'BBC News' })} />)
    fireEvent.error(screen.getByRole('img', { name: 'Broken' }))
    expect(screen.getByRole('img', { name: 'Broken' }).tagName).toBe('DIV')
    expect(screen.getByText('BBC News')).toBeInTheDocument()
  })

  it('can hide the label where text is already overlaid (hero)', () => {
    render(<ArticleImage showLabel={false} article={makeArticle({ title: 'Hero story', source: 'CNBC' })} />)
    expect(screen.getByRole('img', { name: 'Hero story' })).toBeInTheDocument()
    expect(screen.queryByText('CNBC')).not.toBeInTheDocument()
  })

  it('uses a different colour per topic', () => {
    const { rerender } = render(<ArticleImage article={makeArticle({ id: 1, title: 'A', topic_primary: 'Sports' })} />)
    const sports = screen.getByRole('img', { name: 'A' }).style.background
    rerender(<ArticleImage article={makeArticle({ id: 1, title: 'A', topic_primary: 'Health' })} />)
    expect(screen.getByRole('img', { name: 'A' }).style.background).not.toBe(sports)
  })
})
