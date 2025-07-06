import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@lib/apiClient'
import type { SearchResultDTO } from '@dtos/SearchResultDTO'

/** ハイブリッド検索用の Hook */
export function useHybridSearch(query: string) {
    return useQuery<
        SearchResultDTO[],                           // TQueryFnData
        Error,                                       // TError
        SearchResultDTO[],                           // TData
        readonly ['search', 'hybrid', typeof query] // TQueryKey
    >({
        queryKey:   ['search', 'hybrid', query] as const,
        queryFn:    () => apiClient.searchHybridMemos(query),
        enabled:    query.length > 0,
        staleTime:  60_000,       // 1分
        refetchOnWindowFocus: false,
        refetchOnMount:       false,
        refetchOnReconnect:   false,
    })
}
