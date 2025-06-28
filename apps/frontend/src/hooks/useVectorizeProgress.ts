import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@lib/apiClient'

export type ProgressData = { processed: number; total: number }

export const useVectorizeProgress = (enabled: boolean) =>
    useQuery<ProgressData, Error>({
        queryKey: ['vectorize-progress'],
        queryFn: () => apiClient.getVectorizeProgress(),
        enabled,
        // データ受信後、processed < total の間だけ 1秒ごとにポーリング
        refetchInterval: ({ state }) => {
            const d = state.data
            return enabled && d && d.processed < d.total ? 1000 : false
        },
    })
