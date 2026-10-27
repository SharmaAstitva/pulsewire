import { useQuery } from '@tanstack/react-query'
import { getArticles, getArticle, getTrending, getCategories, searchArticles } from '../api/client'

export const useArticles = (params = {}) =>
  useQuery({
    queryKey: ['articles', params],
    queryFn: () => getArticles({ limit: 10, sort: 'trending', ...params }),
    staleTime: 3 * 60_000,
    refetchInterval: 5 * 60_000,
  })

export const useArticle = (id) =>
  useQuery({
    queryKey: ['article', id],
    queryFn: () => getArticle(id),
    enabled: !!id,
    staleTime: 30 * 60_000,
  })

export const useTrending = (params = {}) =>
  useQuery({
    queryKey: ['trending', params],
    queryFn: () => getTrending({ limit: 5, ...params }),
    staleTime: 2 * 60_000,
    refetchInterval: 3 * 60_000,
  })

export const useCategories = () =>
  useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
    staleTime: 10 * 60_000,
  })

export const useSearch = (q) =>
  useQuery({
    queryKey: ['search', q],
    queryFn: () => searchArticles({ q, limit: 20 }),
    enabled: q?.length >= 2,
    staleTime: 60_000,
  })
