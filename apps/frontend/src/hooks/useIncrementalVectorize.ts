import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@lib/apiClient'

type Response = { status: string }

export const useIncrementalVectorize = () => {
    const qc = useQueryClient()
    return useMutation<Response, Error, void>({
        mutationFn: () => apiClient.incrementalVectorize(),
        onSuccess: () => {
            // ベクトル化進捗キャッシュを無効化して最新を取得
            qc.invalidateQueries({ queryKey: ['vectorize-progress'] })
        },
    })
}
