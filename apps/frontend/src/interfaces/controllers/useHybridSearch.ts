import { useQuery, UseQueryResult } from '@tanstack/react-query'
import { apiClient } from '@lib/apiClient'
import type { SearchResultDTO } from '@dtos/SearchResultDTO'

     /** ハイブリッド検索用の Hook */
     export function useHybridSearch(query: string) {
         return useQuery<SearchResultDTO[], Error, SearchResultDTO[], readonly ['search','hybrid',string]>({
             queryKey: ['search', 'hybrid', query] as const,
             queryFn:  () => apiClient.searchHybridMemos(query),
             enabled:  query.length > 0,
             staleTime:          60_000,
             refetchOnWindowFocus: false,
             refetchOnMount:      false,
             refetchOnReconnect:  false,
         })
     }
