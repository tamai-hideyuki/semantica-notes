import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@lib/apiClient'
import type { SearchResultDTO } from '@dtos/SearchResultDTO'

export const useSearchMemos = (query: string) =>
    useQuery<SearchResultDTO[], Error>({
        queryKey: ['search', query],
        queryFn: () => apiClient.searchMemos(query),
        enabled: query.length > 0,
        staleTime: 1000 * 60 * 5,
    })
