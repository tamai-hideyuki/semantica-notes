import React, { useState } from 'react'
import type { MemoDTO } from '@dtos/MemoDTO'
import { apiClient }      from '@lib/apiClient'

type Props = {
    initial: MemoDTO
    onSaved?: (updated: MemoDTO) => void
}

export const EditMemo: React.FC<Props> = ({ initial, onSaved }) => {
    const [title, setTitle] = useState(initial.title)
    const [body, setBody]   = useState(initial.body)
    const [loading, setLoading] = useState(false)
    const [error, setError]     = useState<string | null>(null)

    const handleSave = async () => {
        setLoading(true)
        setError(null)
        try {
            const updated = await apiClient.updateMemo(initial.uuid, { title, body })
            onSaved?.(updated)
        } catch (e: any) {
            setError(e.message || '更新に失敗しました')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="edit-memo">
            <label>
                タイトル
                <input
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    disabled={loading}
                />
            </label>
            <label>
                本文
                <textarea
                    value={body}
                    onChange={e => setBody(e.target.value)}
                    disabled={loading}
                />
            </label>
            {error && <p className="error">{error}</p>}
            <button onClick={handleSave} disabled={loading}>
                {loading ? '保存中…' : '保存'}
            </button>
        </div>
    )
}
