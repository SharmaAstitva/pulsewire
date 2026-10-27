import { renderHook, act } from '@testing-library/react'
import { useDebounce } from '../../hooks/useDebounce'

describe('useDebounce', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('only updates after the delay has passed', () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: 'a' },
    })
    rerender({ value: 'ab' })
    act(() => vi.advanceTimersByTime(299))
    expect(result.current).toBe('a')
    act(() => vi.advanceTimersByTime(1))
    expect(result.current).toBe('ab')
  })

  it('restarts the timer on every keystroke', () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: 'n' },
    })
    rerender({ value: 'ne' })
    act(() => vi.advanceTimersByTime(200))
    rerender({ value: 'new' })
    act(() => vi.advanceTimersByTime(200))
    expect(result.current).toBe('n')
    act(() => vi.advanceTimersByTime(100))
    expect(result.current).toBe('new')
  })
})
