/**
 * メモエンティティ定義
 */
export interface Memo {
    uuid:       string
    title:      string
    tags:       string
    category:   string
    body:       string
    created_at: string
    score?:     number
}

/**
 * 本文からスニペット（先頭 max 文字＋…）を生成するユーティリティ
 */
export function makeSnippet(body: string, max = 100): string {
    return body.length > max
        ? body.slice(0, max) + '…'
        : body
}
