import React from 'react'
import { motion } from 'framer-motion'
import { useIncrementalVectorize } from '@hooks/useIncrementalVectorize'
import { useVectorizeProgress }   from '@hooks/useVectorizeProgress'
import Button      from './Button'
import ProgressBar from './ProgressBar'

type VectorizeSectionProps = {
    /** ボタンクラス名を受け取る */
    buttonClassName?: string
}

const glowVariant = {
    idle: {
        boxShadow: '0 0 0 rgba(0,0,0,0)',
        transition: { duration: 0.5 }
    },
    hover: {
        boxShadow: '0 0 8px rgba(66, 153, 225, 0.6)',
        transition: { duration: 0.5 }
    }
}

const VectorizeSection: React.FC<VectorizeSectionProps> = ({ buttonClassName }) => {
    const { mutate, status } = useIncrementalVectorize()
    const isLoading = status === 'pending'
    const isSuccess = status === 'success'

    const shouldPoll = isLoading || isSuccess
    const { data, isFetching } = useVectorizeProgress(shouldPoll)

    const processed = data?.processed ?? 0
    const total     = data?.total     ?? 0
    const isVectorizing = isLoading || processed < total

    return (
        <div className="relative p-4 border rounded-lg h-full flex flex-col">
            <motion.div
                variants={glowVariant}
                initial="idle"
                whileHover={!isVectorizing ? 'hover' : undefined}
                animate="idle"
            >
                <Button
                    className={buttonClassName}
                    onClick={() => mutate()}
                    disabled={isVectorizing}
                >
                    {isVectorizing ? 'ベクトル化中…' : 'ベクトル化'}
                </Button>
            </motion.div>

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
