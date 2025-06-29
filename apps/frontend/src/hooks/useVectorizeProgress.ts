import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@lib/apiClient'

export type ProgressData = { processed: number; total: number }

export const useVectorizeProgress = (enabled: boolean) =>
    useQuery<
        ProgressData,              // queryFn の戻り値
        Error,                     // エラー型
        ProgressData,              // data プロパティに格納される型
        ['vectorize-progress']     // queryKey のタプル型
    >({
        queryKey: ['vectorize-progress'],
        queryFn:  () => apiClient.getVectorizeProgress(),
        enabled,

        // 第一引数が Query オブジェクト型なので、state.data を参照
        refetchInterval: (query) => {
            const d = query.state.data
            if (!enabled || !d) return false
            // 完了前だけ１秒ごとに再フェッチ
            return d.processed < d.total ? 1000 : false
        },

        // フォーカス時・マウント時・再接続時の自動再フェッチをオフ
        refetchOnWindowFocus: false,
        refetchOnMount:       false,
        refetchOnReconnect:   false,
    })
