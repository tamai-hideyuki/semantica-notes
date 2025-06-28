import React, { ButtonHTMLAttributes, FC } from 'react';
import clsx from 'clsx';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    /**
     * ボタンのバリエーション
     * デフォルトは 'primary'
     */
    variant?: 'primary' | 'secondary';
    /**
     * Tailwind のクラスをさらに追加したいとき用
     */
    className?: string;
}

const VARIANT_CLASSES: Record<NonNullable<ButtonProps['variant']>, string> = {
    primary: 'bg-blue-500 hover:bg-blue-600 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
};

const Button: FC<ButtonProps> = ({
                                     variant = 'primary',
                                     className,
                                     disabled,
                                     children,
                                     ...rest
                                 }) => {
    const baseClasses =
        'px-4 py-2 rounded-2xl shadow-sm font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2';
    const variantClasses = VARIANT_CLASSES[variant];

    return (
        <button
            className={clsx(
                baseClasses,
                variantClasses,
                disabled && 'opacity-50 cursor-not-allowed',
                className
            )}
            disabled={disabled}
            {...rest}
        >
            {children}
        </button>
    );
};

export default Button;
