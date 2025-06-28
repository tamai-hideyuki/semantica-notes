import React, { useState, ChangeEvent, FormEvent } from 'react'
import { useCreateMemo } from '../controllers/useCreateMemo'
import type { MemoCreateDTO } from '../dtos/MemoCreateDTO'
import Link from 'next/link'
import VectorizeSection from '@components/VectorizeSection'
import styles from '../../styles/HomePage.module.css'

export function HomePage() {
    const [form, setForm] = useState<{ category: string; title: string; tags: string; body: string;}>({
        category: '',
        title: '',
        tags: '',
        body: '',
    })

    const { mutate, status, data, error } = useCreateMemo()
    const isLoading = status === 'pending'
    const isError = status === 'error'
    const isSuccess = status === 'success'

    const handleChange = (
        e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
    ) => {
        const { name, value } = e.target
        setForm(prev => ({ ...prev, [name]: value }))
    }

     const handleSubmit = (e: FormEvent) => {
             e.preventDefault()
             // タグ文字列を配列化
             const tagsArray = form.tags
                     .split(',')
                 .map(tag => tag.trim())
                 .filter(tag => tag)

             // API DTOを構築
                 const payload: MemoCreateDTO = {
                     category: form.category,
                     title: form.title,
                     tags: tagsArray,
                     body: form.body,
                 }

                 // 直接 mutate に渡す
                     mutate(payload)
         }

    return (
        <div className={styles.container}>
            <h1>メモ作成</h1>
            <form onSubmit={handleSubmit} className={styles.form}>
                <input
                    name="category"
                    value={form.category}
                    onChange={handleChange}
                    placeholder="カテゴリ"
                />
                <input
                    name="title"
                    value={form.title}
                    onChange={handleChange}
                    placeholder="タイトル"
                />
                <input
                    name="tags"
                    value={form.tags}
                    onChange={handleChange}
                    placeholder="タグ (カンマ区切り)"
                />
                <textarea
                    name="body"
                    rows={6}
                    value={form.body}
                    onChange={handleChange}
                    placeholder="本文"
                />
                <button type="submit" disabled={isLoading}>
                    {isLoading ? '保存中…' : '保存'}
                </button>
            </form>

            {isError && <p className={styles.error}>エラー: {error?.message}</p>}
            {isSuccess && data && (
                <p className={styles.success}>
                    保存完了 ☞ UUID: {data.uuid}
                </p>
            )}

            {/* ベクトル化ボタン＆進捗表示セクション */}
            <div className={styles.vectorizeSection}>
                <VectorizeSection />
            </div>

            <p style={{ marginTop: '2rem' }}>
                <Link href="./search">→ メモ検索ページへ</Link>
            </p>
        </div>
    )
}
