import React, { useState } from 'react'
import type { MemoDTO } from '@dtos/MemoDTO'
import { apiClient }    from '@lib/apiClient'
import { useRouter }    from 'next/router'
import Link             from 'next/link'
import styles           from '@styles/EditMemo.module.css'

type Props = {
    initial: MemoDTO
    onSaved?: (updated: MemoDTO) => void
}

export const EditMemo: React.FC<Props> = ({ initial, onSaved }) => {
    const router = useRouter()
    const [title, setTitle]     = useState(initial.title)
    const [body, setBody]       = useState(initial.body)
    const [loading, setLoading] = useState(false)
    const [error, setError]     = useState<string | null>(null)

    const handleSave = async () => {
        if (loading) return
        setLoading(true)
        setError(null)
        try {
            const updated = await apiClient.updateMemo(initial.uuid, { title, body })
            await router.replace('/search')
            onSaved?.(updated)
        } catch (e: any) {
            setError(e.message || '更新に失敗しました')
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async () => {
        if (!confirm('このメモを本当に削除しますか？')) return
        setLoading(true)
        try {
            await apiClient.deleteMemo(initial.uuid)
            // 削除完了後は検索ページへ
            await router.replace('/search')
        } catch (e: any) {
            setError(e.message || '削除に失敗しました')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className={styles.container}>
            <h1 className={styles.heading}>メモを編集</h1>

            <div className={styles.card}>
                <div className={styles.form}>
                    <input
                        className={styles.input}
                        type="text"
                        placeholder="タイトルを入力"
                        value={title}
                        onChange={e => setTitle(e.target.value)}
                        disabled={loading}
                    />
                    <textarea
                        className={styles.textarea}
                        placeholder="本文を入力"
                        value={body}
                        onChange={e => setBody(e.target.value)}
                        disabled={loading}
                    />
                </div>

                {error && <p className={styles.error}>{error}</p>}

                <div className={styles.vectorizeSection}>
                    <button
                        type="button"
                        onClick={handleSave}
                        disabled={loading}
                        className={`${styles.vectorButton} ${loading ? styles.loading : ''}`}
                    >
                        {loading ? '保存中…' : '保存'}
                    </button>
                </div>
            </div>

            {/* ↓ 追加ボタン群 */}
            <div className={styles.linkGroup}>
                <button
                    type="button"
                    onClick={handleDelete}
                    disabled={loading}
                    className={styles.deleteButton}
                >
                    削除
                </button>

                <Link href="/search">
                    <button className={styles.backLink}>→ メモ検索ページへ戻る</button>
                </Link>
            </div>
        </div>
    )
}
