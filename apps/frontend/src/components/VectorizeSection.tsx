import React from 'react'
import { useIncrementalVectorize } from '@hooks/useIncrementalVectorize'
import { useVectorizeProgress }   from '@hooks/useVectorizeProgress'
import Button      from './Button'
import ProgressBar from './ProgressBar'

type VectorizeSectionProps = {
    /** ボタンクラス名を受け取る */
    buttonClassName?: string
}

const VectorizeSection: React.FC<VectorizeSectionProps> = ({ buttonClassName }) => {
    // Mutation の結果として、status を受け取る
    const { mutate, status } = useIncrementalVectorize()

    // status をもとにフラグを作る
    const isLoading = status === 'pending'
    const isSuccess = status === 'success'

    // mutate が呼ばれた or 成功したら polling 開始
    const shouldPoll = isLoading || isSuccess
    const { data, isFetching } = useVectorizeProgress(shouldPoll)

    const processed = data?.processed ?? 0
    const total     = data?.total     ?? 0
    const isVectorizing = isLoading || processed < total

    return (
        <div className="relative p-4 border rounded-lg h-full flex flex-col">
            <Button
                className={buttonClassName}
                onClick={() => mutate()}
                disabled={isVectorizing}
            >
                {isVectorizing ? 'ベクトル化中…' : 'ベクトル化を実行'}
            </Button>

            {isFetching && total > 0 && (
                <div className="mt-2">
                    <ProgressBar processed={processed} total={total} />
                </div>
            )}

            {!isVectorizing && isSuccess && total > 0 && (
                <p className="text-green-600 text-sm mt-2">ベクトル化 完了！</p>
            )}
        </div>
    )
}

export default VectorizeSection
