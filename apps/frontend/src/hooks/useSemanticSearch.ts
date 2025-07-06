import { useQuery, UseQueryResult } from '@tanstack/react-query'
import { apiClient } from '@lib/apiClient'
import type { SearchResultDTO } from '@dtos/SearchResultDTO'

/**
 * セマンティック検索用の hook
 */
export function useSemanticSearch(
    query: string,
): UseQueryResult<SearchResultDTO[], Error> {
    return useQuery<SearchResultDTO[], Error>({
        queryKey: ['search', 'semantic', query],
        queryFn: () => apiClient.searchSemanticMemos(query),
        enabled: query.length > 0,
        staleTime: 1000 * 60,
    })
}
