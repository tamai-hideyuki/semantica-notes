import React, {
    useState,
    useEffect,
    ChangeEvent,
    FormEvent,
} from 'react'
import { useCreateMemo } from '@controllers/useCreateMemo'
import type { MemoCreateDTO } from '@dtos/MemoCreateDTO'
import Link from 'next/link'
import VectorizeSection from '@components/VectorizeSection'
import styles from '../../styles/HomePage.module.css'

const initialForm = {
    category: '',
    title:    '',
    tags:     '',
    body:     '',
}

export function HomePage() {
    const [form, setForm] = useState(initialForm)
    const [showSuccess, setShowSuccess] = useState(false)

    const { mutate, status, data, error } = useCreateMemo()
    const isLoading = status === 'pending'
    const isError   = status === 'error'
    const isSuccess = status === 'success'

    // すべてトリム後に空かどうか
    const isFormEmpty =
        !form.category.trim() &&
        !form.title.trim()    &&
        !form.tags.trim()     &&
        !form.body.trim()

    // 保存成功時：フォームをリセット＋成功メッセージ表示 → 1.5秒後に非表示
    useEffect(() => {
        if (isSuccess) {
            setForm(initialForm)
            setShowSuccess(true)
            const timer = setTimeout(() => setShowSuccess(false), 1500)
            return () => clearTimeout(timer)
        }
    }, [isSuccess])

    const handleChange = (
        e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
    ) => {
        const { name, value } = e.target
        setForm(prev => ({ ...prev, [name]: value }))
    }

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault()
        const tagsArray = form.tags
            .split(',')
            .map(t => t.trim())
            .filter(Boolean)

        const payload: MemoCreateDTO = {
            category: form.category,
            title:    form.title,
            tags:     tagsArray,
            body:     form.body,
        }

        mutate(payload)
    }

    const buttonClasses = [
        styles.button,
        isLoading && styles.loading,
        isSuccess && styles.successState,
        isError   && styles.errorState,
    ].filter(Boolean).join(' ')

    return (
        <div className={styles.container}>
            <h1 className={styles.heading}>メモ作成</h1>

            <div className={styles.card}>
                <form onSubmit={handleSubmit} className={styles.form}>
                    <input
                        name="category"
                        value={form.category}
                        onChange={handleChange}
                        placeholder="カテゴリ"
                        className={styles.input}
                    />
                    <input
                        name="title"
                        value={form.title}
                        onChange={handleChange}
                        placeholder="タイトル"
                        className={styles.input}
                    />
                    <input
                        name="tags"
                        value={form.tags}
                        onChange={handleChange}
                        placeholder="タグ (カンマ区切り)"
                        className={styles.input}
                    />
                    <textarea
                        name="body"
                        rows={6}
                        value={form.body}
                        onChange={handleChange}
                        placeholder="本文"
                        className={styles.textarea}
                    />
                    <button
                        type="submit"
                        disabled={isLoading || isFormEmpty}
                        className={buttonClasses}
                    >
                        {isLoading ? '保存中…' : '保存'}
                    </button>
                </form>

                {/* エラー表示 */}
                {isError && (
                    <p className={styles.error}>エラー: {error?.message}</p>
                )}

                {/* フェードイン・アウトする成功メッセージ */}
                <p
                    className={[
                        styles.successMessage,
                        showSuccess ? styles.visible : '',
                    ].join(' ')}
                >
                    保存しました！
                </p>

                {/*
                {isSuccess && data && (
                    <p className={styles.success}>UUID: {data.uuid}</p>
                )} */}
            </div>

            <Link href="./search" className={styles.backLink}>
                → メモ検索ページへ
            </Link>

            <div className={styles.vectorizeSection}>
                <VectorizeSection buttonClassName={styles.vectorButton} />
            </div>
        </div>
    )
}
