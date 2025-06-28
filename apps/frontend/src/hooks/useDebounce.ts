import { useState, useEffect } from 'react';

/**
 * 値の変更を指定ミリ秒遅延させた後に反映するカスタムフック
 *
 * @param value 監視する値
 * @param delay デバウンスにかけるミリ秒（デフォルト 300ms）
 * @returns デバウンス後の値
 */
function useDebounce<T>(value: T, delay: number = 300): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
        // delay ミリ秒後に値を更新
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        // クリーンアップ：次の effect 実行前にタイマーをクリア
        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);

    return debouncedValue;
}

export default useDebounce;
