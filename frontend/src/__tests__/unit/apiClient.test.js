import { api } from '../../api/client'

const [interceptor] = api.interceptors.response.handlers

describe('API client', () => {
  it('points at the versioned API', () => {
    expect(api.defaults.baseURL).toMatch(/\/api\/v1$/)
  })

  it('unwraps the response body', () => {
    expect(interceptor.fulfilled({ data: { data: [1] } })).toEqual({ data: [1] })
  })

  it('surfaces the API error message', async () => {
    const err = { response: { data: { detail: 'Article not found' } }, message: 'Request failed with 404' }
    await expect(interceptor.rejected(err)).rejects.toThrow('Article not found')
  })

  it('falls back to the network error message', async () => {
    await expect(interceptor.rejected({ message: 'Network Error' })).rejects.toThrow('Network Error')
  })
})
