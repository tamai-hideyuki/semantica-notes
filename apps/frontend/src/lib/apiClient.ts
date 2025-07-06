import axios from 'axios'
import type { SearchResultDTO } from '@dtos/SearchResultDTO'
import type { MemoCreateDTO } from '@dtos/MemoCreateDTO'
import type { MemoDTO } from '@dtos/MemoDTO'

// ──── BASE URL ────
const RAW_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? ''
const BASE = RAW_BASE.replace(/\/+$/g, '')
console.debug('[API BASE]', BASE)

// ──── Axios Instance ────
const client = axios.create({ baseURL: `${BASE}/api` })

// ──── 共通ログ関数 ────
function formatMethod(method?: string) {
    return (method ?? 'GET').toUpperCase()
}

// ──── Interceptors ────
client.interceptors.request.use(
    (config) => {
        const fullUrl = `${config.baseURL ?? ''}${config.url}`
        console.groupCollapsed('[API REQUEST]', formatMethod(config.method), fullUrl)
        console.debug('Config:', config)
        if (config.data) console.debug('Payload:', config.data)
        if (config.params) console.debug('Params:', config.params)
        console.groupEnd()
        return config
    },
    (error) => {
        console.groupCollapsed('[API REQUEST ERROR]')
        console.error(error)
        console.groupEnd()
        return Promise.reject(error)
    }
)

client.interceptors.response.use(
    (response) => {
        const { config } = response
        const fullUrl = `${config.baseURL ?? ''}${config.url}`
        console.groupCollapsed('[API RESPONSE]', formatMethod(config.method), fullUrl)
        console.debug('Status:', response.status)
        console.debug('Data:', response.data)
        console.groupEnd()
        return response
    },
    (error) => {
        const { config } = error
        console.groupCollapsed('[API ERROR]', formatMethod(config?.method), config?.url)
        console.error('Error Message:', error.message)
        if (error.response) console.error('Response Data:', error.response.data)
        console.groupEnd()
        return Promise.reject(error)
    }
)

// ──── API Client ────
export const apiClient = {
    // 汎用 POST／GET
    post: async <T>(path: string, body?: unknown): Promise<T> =>
        client.post<T>(path, body).then(res => res.data),

    get: async <T>(path: string): Promise<T> =>
        client.get<T>(path).then(res => res.data),

    // 検索エンドポイント
    searchMemos: (query: string) =>
        apiClient.post<SearchResultDTO[]>('/search', { query }),

    searchSemanticMemos: (query: string) =>
        apiClient.post<SearchResultDTO[]>('/search/semantic', { query }),

    searchHybridMemos: (query: string) =>
        apiClient.post<SearchResultDTO[]>('/search/hybrid', { query }),

    // メモ操作
    createMemo: (payload: MemoCreateDTO) =>
        apiClient.post<{ uuid: string; status: string }>('/memo', payload),

    updateMemo: (uuid: string, data: { title: string; body: string }) =>
        apiClient.post<MemoDTO>(`/memo/${uuid}`, data),

    deleteMemo: (uuid: string) =>
        apiClient.post<{ status: string }>(`/memo/${uuid}`, {}),

    // 管理操作
    incrementalVectorize: () =>
        apiClient.post<{ status: string }>('/admin/incremental-vectorize'),

    getVectorizeProgress: () =>
        apiClient.get<{ processed: number; total: number }>('/admin/progress'),

    rebuildIndex: () =>
        apiClient.post<{ status: string }>('/admin/rebuild'),
}

// ──── カテゴリ／タグ取得ヘルパー ────
export async function getCategories(): Promise<string[]> {
    return apiClient.get<string[]>('/categories')
}

export async function getTags(): Promise<string[]> {
    return apiClient.get<string[]>('/tags')
}
