import { useRouter }       from 'next/router'
import { useEffect, useState } from 'react'
import type { MemoDTO }    from '@dtos/MemoDTO'
import { apiClient }       from '@lib/apiClient'
import { EditMemo }        from '@presenters/EditMemo'

const EditPage: React.FC = () => {
    const router = useRouter()
    const { uuid } = router.query as { uuid?: string }
    const [memo, setMemo] = useState<MemoDTO | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!uuid) return
        apiClient.get<MemoDTO>(`/memo/${uuid}`)
            .then(setMemo)
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [uuid])

    if (loading) return <p>読み込み中…</p>
    if (!memo)   return <p>メモが見つかりませんでした</p>

    return (
        <EditMemo
            initial={memo}
            onSaved={() => router.push(`/memos/${uuid}`)}
        />
    )
}

export default EditPage
