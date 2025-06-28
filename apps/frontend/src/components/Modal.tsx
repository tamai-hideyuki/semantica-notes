import React, { FC, ReactNode, useEffect } from 'react';

export interface ModalProps {
    /**
     * モーダルの可視状態
     */
    isOpen: boolean;
    /**
     * モーダルを閉じる時に呼ばれるコールバック
     */
    onClose: () => void;
    /**
     * モーダルのタイトル
     */
    title?: string;
    /**
     * モーダル内にレンダリングするコンテンツ
     */
    children: ReactNode;
}

const Modal: FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
    // ESC キーで閉じる
    useEffect(() => {
        const handleKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose();
            }
        };
        if (isOpen) {
            window.addEventListener('keydown', handleKey);
        }
        return () => {
            window.removeEventListener('keydown', handleKey);
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-2xl shadow-lg max-w-lg w-full p-6 relative"
                onClick={(e) => e.stopPropagation()}
            >
                {/* ヘッダー */}
                <div className="flex items-center justify-between mb-4">
                    {title && <h2 className="text-xl font-semibold">{title}</h2>}
                    <button
                        onClick={onClose}
                        aria-label="Close modal"
                        className="text-gray-500 hover:text-gray-700 focus:outline-none"
                    >
                        ✕
                    </button>
                </div>

                {/* コンテンツ */}
                <div className="space-y-4">{children}</div>
            </div>
        </div>
    );
};

export default Modal;
