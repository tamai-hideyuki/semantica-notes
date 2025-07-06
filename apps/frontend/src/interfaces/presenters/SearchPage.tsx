import React, { useState, ChangeEvent, FormEvent, JSX } from 'react'
import { useSemanticSearch } from '@hooks/useSemanticSearch'
import { useHybridSearch } from '@hooks/useHybridSearch'
import useDebounce from '@hooks/useDebounce'
import type { SearchResultDTO } from '@dtos/SearchResultDTO'
import styles from '../../styles/SearchPage.module.css'
import Link from 'next/link'
import Modal from 'react-modal'
import { formatDate } from '@utils/formatDate'

Modal.setAppElement('#__next')
const ITEMS_PER_PAGE = 10

type SearchMode = 'semantic' | 'hybrid'

export function SearchPage(): JSX.Element {
    const [query, setQuery] = useState<string>('')
    const [mode, setMode] = useState<SearchMode>('semantic')
    const [selected, setSelected] = useState<SearchResultDTO | null>(null)
    const [page, setPage] = useState<number>(1)

    const debouncedQuery = useDebounce<string>(query, 500)

    const { data: results = [], isLoading, isError, error, refetch } =
        mode === 'semantic'
            ? useSemanticSearch(debouncedQuery)
            : useHybridSearch(debouncedQuery)

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

    const startIndex = (page - 1) * ITEMS_PER_PAGE
    const pagedResults = sortedResults.slice(startIndex, startIndex + ITEMS_PER_PAGE)
    const totalPages = Math.ceil(sortedResults.length / ITEMS_PER_PAGE)

    return (
        <div className={styles.container}>
            <h1 className={styles.heading}>メモ検索</h1>

            <div className={styles.searchCard}>
                <div className={styles.modeToggle}>
                    <label>
                        <input
                            type="radio"
                            name="mode"
                            value="semantic"
                            checked={mode === 'semantic'}
                            onChange={() => setMode('semantic')}
                        />
                        セマンティック
                    </label>
                    <label>
                        <input
                            type="radio"
                            name="mode"
                            value="hybrid"
                            checked={mode === 'hybrid'}
                            onChange={() => setMode('hybrid')}
                        />
                        ハイブリッド
                    </label>
                </div>

                <form onSubmit={handleSearch} className={styles.form}>
                    <input
                        type="text"
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
            </div>

            {pagedResults.length > 0 ? (
                <ul className={styles.results}>
                    {pagedResults.map((r) => (
                        <li key={r.uuid} className={styles.item} onClick={() => setSelected(r)}>
                            <h2 className={styles.title}>{r.title}</h2>
                            <pre className={styles.preview}>
                {r.body.slice(0, 200)}{r.body.length > 200 ? '…' : ''}
              </pre>
                            <small className={styles.meta}>
                                {formatDate(r.created_at)} ・ {r.category} / {r.tags.join(', ')}
                            </small>
                        </li>
                    ))}
                </ul>
            ) : (
                !isLoading && <p className={styles.noResults}>該当するメモはありません。</p>
            )}

            <div className={styles.pagination}>
                <button disabled={page <= 1} onClick={() => setPage(page - 1)} className={styles.pageButton}>
                    前へ
                </button>
                <span className={styles.pageInfo}>{page} / {totalPages}</span>
                <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className={styles.pageButton}>
                    次へ
                </button>
            </div>

            <Modal
                isOpen={!!selected}
                onRequestClose={() => setSelected(null)}
                contentLabel="メモ詳細"
                className={styles.modal}
                overlayClassName={styles.overlay}
            >
                {selected && (
                    <div className={styles.detailCard}>
                        <h2 className={styles.detailTitle}>{selected.title}</h2>
                        <pre className={styles.fullBody}>{selected.body}</pre>
                        <div className={styles.actions}>
                            <Link href={`/memos/${selected.uuid}/edit`}>
                                <button className={styles.editButton}>編集</button>
                            </Link>
                            <button onClick={() => setSelected(null)} className={styles.closeButton}>
                                閉じる
                            </button>
                        </div>
                    </div>
                )}
            </Modal>

            <Link href="/" className={styles.backLink}>⏎ 戻る</Link>
        </div>
    )
}
