import React, { useState, ChangeEvent, FormEvent, useEffect } from 'react'
import { useSearchMemos } from '@controllers/useSearchMemos'
import useDebounce from '../../hooks/useDebounce'
import type { SearchResultDTO } from '@dtos/SearchResultDTO'
import styles from '../../styles/SearchPage.module.css'
import Link from 'next/link'
import Modal from 'react-modal'
import { formatDate } from '@utils/formatDate';

Modal.setAppElement('#__next')

const ITEMS_PER_PAGE = 10

export function SearchPage() {
    const [query, setQuery] = useState('')
    const [selected, setSelected] = useState<SearchResultDTO | null>(null)
    const [page, setPage] = useState(1)
    const debouncedQuery = useDebounce(query, 500)
    const { data: results = [], isLoading, isError, error, refetch } = useSearchMemos(debouncedQuery)

    // 登録日時順ソートは検索クエリ未入力時のみ
    const sortedResults = React.useMemo(() => {
        if (!debouncedQuery) {
            return [...results].sort(
                (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
            )
        }
        return results
    }, [results, debouncedQuery])

    const handleSearch = (e: FormEvent) => {
        e.preventDefault()
        setPage(1)
        refetch()
    }

    // ページネーション用スライス
    const startIndex = (page - 1) * ITEMS_PER_PAGE
    const pagedResults = sortedResults.slice(startIndex, startIndex + ITEMS_PER_PAGE)
    const totalPages = Math.ceil(sortedResults.length / ITEMS_PER_PAGE)

    return (
        <div className={styles.container}>
            <h1>メモ検索</h1>
            <form onSubmit={handleSearch} className={styles.form}>
                <input
                    value={query}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
                    placeholder="検索クエリ"
                    className={styles.input}
                />
                <button type="submit" disabled={isLoading} className={styles.button}>
                    {isLoading ? '検索中…' : '検索'}
                </button>
            </form>

            {isError && <p className={styles.error}>エラー: {error?.message}</p>}

            {pagedResults.length > 0 ? (
                <>
                    <ul className={styles.results}>
                        {pagedResults.map((r: SearchResultDTO) => (
                            <li
                                key={r.uuid}
                                className={styles.item}
                                onClick={() => setSelected(r)}
                                style={{
                                    borderBottom: '1px solid #ddd',
                                    paddingBottom: '16px',
                                    marginBottom: '16px',
                                }}
                            >
                                <h2 className={styles.title}>{r.title}</h2>
                                <pre
                                    className={styles.preview}
                                    style={{
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word',
                                        maxWidth: '100%',
                                        overflowX: 'hidden'
                                    }}
                                >
                                    {r.body.slice(0, 200)}{r.body.length > 200 ? '…' : ''}
                                </pre>
                                <small className={styles.meta}>
                                    {formatDate(r.created_at)} ・ {r.category} / {r.tags.join(', ')}
                                </small>
                            </li>
                        ))}
                    </ul>

                    {/* ページネーション コントロール */}
                    <div className={styles.pagination}>
                        <button
                            disabled={page <= 1}
                            onClick={() => setPage(page - 1)}
                            className={styles.pageButton}
                        >
                            前へ
                        </button>
                        <span className={styles.pageInfo}>
                            {page} / {totalPages}
                        </span>
                        <button
                            disabled={page >= totalPages}
                            onClick={() => setPage(page + 1)}
                            className={styles.pageButton}
                        >
                            次へ
                        </button>
                    </div>
                </>
            ) : (
                !isLoading && <p className={styles.noResults}>該当するメモはありません。</p>
            )}

            <Modal
                isOpen={!!selected}
                onRequestClose={() => setSelected(null)}
                contentLabel="メモ詳細"
                className={styles.modal}
                overlayClassName={styles.overlay}
            >
                {selected && (
                    <>
                        <h2>{selected.title}</h2>
                        <pre
                            className={styles.fullBody}
                            style={{
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                                maxHeight: '80vh',
                                overflowY: 'auto',
                                overflowX: 'hidden'
                            }}
                        >
                            {selected.body}
                        </pre>
                        <button onClick={() => setSelected(null)} className={styles.closeButton}>
                            閉じる
                        </button>
                    </>
                )}
            </Modal>

            <p className={styles.backLink}>
                <Link href="/">⏎ 戻る</Link>
            </p>
        </div>
    )
}
