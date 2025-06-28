const BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || '').replace(/\/+$/, '')

async function request<T>(
    method: 'GET' | 'POST',
    path: string,
    body?: unknown
): Promise<T> {
    const url = `${BASE}/api/${path.replace(/^\/+/, '')}`
    const opts: RequestInit = {
        method,
        headers: { 'Content-Type': 'application/json' },
        ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    }

    const res = await fetch(url, opts)
    if (!res.ok) {
        const text = await res.text().catch(() => res.statusText)
        throw new Error(`HTTP ${res.status}: ${text}`)
    }
    return (await res.json()) as T
}

export const apiClient = {
    post: <T>(path: string, body: unknown): Promise<T> =>
        request<T>('POST', path, body),

    get: <T>(path: string): Promise<T> =>
        request<T>('GET', path),

    incrementalVectorize: () =>
        apiClient.post<{ status: string }>(
            'admin/incremental-vectorize',
            {}
        ),

    getVectorizeProgress: () =>
        apiClient.get<{ processed: number; total: number }>(
            'admin/progress'
        ),

    rebuildIndex: () =>
        apiClient.post<{ status: string }>(
            'admin/rebuild',
            {}
        ),
}
