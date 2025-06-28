import React, { FC } from 'react';

interface ProgressBarProps {
    processed: number;
    total: number;
}

const ProgressBar: FC<ProgressBarProps> = ({ processed, total }) => {
    const percent = total > 0 ? Math.round((processed / total) * 100) : 0;

    return (
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <div
                className="h-full bg-blue-500 transition-width duration-200"
                style={{ width: `${percent}%` }}
            ></div>
            <div className="absolute inset-0 flex items-center justify-center text-xs font-medium text-white">
                {percent}%
            </div>
        </div>
    );
};

export default ProgressBar;
