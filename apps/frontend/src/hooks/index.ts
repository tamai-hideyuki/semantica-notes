import { useState, useEffect } from 'react'
import {
    useMutation,
    useQuery,
    useQueryClient,
    UseMutationResult,
} from '@tanstack/react-query'
import { apiClient } from '@lib/apiClient'

/**
 * 値の変更を指定ミリ秒遅延させた後に反映するカスタムフック
 */
export function useDebounce<T>(value: T, delay = 300): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value)
    useEffect(() => {
        const handler = setTimeout(() => setDebouncedValue(value), delay)
        return () => clearTimeout(handler)
    }, [value, delay])
    return debouncedValue
}

/**
 * インクリメンタルベクトル化の mutation
 */
export function useIncrementalVectorize(): UseMutationResult<
    { status: string },
    Error,
    void
> {
    const queryClient = useQueryClient()
    return useMutation<{ status: string }, Error, void, unknown>({
        mutationFn: () => apiClient.incrementalVectorize(),
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ['vectorize-progress'] }),
    })
}

interface VectorizeProgress {
    processed: number
    total: number
}

/**
 * ベクトル化進捗取得の query
 */
export function useVectorizeProgress(enabled: boolean) {
    return useQuery<
        VectorizeProgress,                // TQueryFnData
        Error,                            // TError
        VectorizeProgress,                // TData
        ['vectorize-progress']            // TQueryKey
    >({
        queryKey: ['vectorize-progress'],
        queryFn: () => apiClient.getVectorizeProgress(),
        enabled,
        refetchInterval: (query) => {
            const data = query.state.data
            if (!enabled || !data) return false
            return data.processed < data.total ? 1_000 : false
        },
        refetchOnWindowFocus: false,
        refetchOnMount: false,
        refetchOnReconnect: false,
    })
}
