import React, { useState } from 'react'
import type { MemoDTO } from '@dtos/MemoDTO'
import { apiClient }      from '@lib/apiClient'
import { useRouter }      from 'next/router'

type Props = {
    initial: MemoDTO
    onSaved?: (updated: MemoDTO) => void
}

export const EditMemo: React.FC<Props> = ({ initial, onSaved }) => {
    const router = useRouter()

    const [title, setTitle]       = useState(initial.title)
    const [body, setBody]         = useState(initial.body)
    const [loading, setLoading]   = useState(false)
    const [error, setError]       = useState<string | null>(null)

    const handleSave = async () => {
        if (loading) return

        setLoading(true)
        setError(null)

        try {
            const updated = await apiClient.updateMemo(initial.uuid, { title, body })

            // コールバック呼び出し
            onSaved?.(updated)

            // 保存後に前のページに戻る
            router.back()
        } catch (e: unknown) {
            const message = e instanceof Error ? e.message : '更新に失敗しました'
            setError(message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="edit-memo p-4 max-w-lg mx-auto bg-white rounded-lg shadow">
            <h1 className="text-xl font-semibold mb-4">メモを編集</h1>

            <label className="block mb-3">
                <span className="text-gray-700">タイトル</span>
                <input
                    type="text"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    disabled={loading}
                />
            </label>

            <label className="block mb-4">
                <span className="text-gray-700">本文</span>
                <textarea
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 h-32"
                    value={body}
                    onChange={e => setBody(e.target.value)}
                    disabled={loading}
                />
            </label>

            {error && (
                <p className="text-red-600 mb-4">{error}</p>
            )}

            <div className="flex space-x-2">
                <button
                    onClick={handleSave}
                    disabled={loading}
                    className={`
            px-4 py-2 rounded-md text-white 
            ${loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
          `}
                >
                    {loading ? '保存中…' : '保存'}
                </button>
                <button
                    onClick={() => router.back()}
                    disabled={loading}
                    className="px-4 py-2 rounded-md bg-gray-200 hover:bg-gray-300"
                >
                    キャンセル
                </button>
            </div>
        </div>
    )
}
