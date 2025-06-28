/**
 * 日付を指定のフォーマット文字列に整形します。
 *
 * サポートするパターン:
 *   yyyy - 4桁の年
 *   MM   - 2桁の月 (01-12)
 *   dd   - 2桁の日 (01-31)
 *   HH   - 2桁の時 (00-23)
 *   mm   - 2桁の分 (00-59)
 *   ss   - 2桁の秒 (00-59)
 *
 * @param input    Date オブジェクトか日付文字列
 * @param format   出力フォーマット (デフォルト 'yyyy/MM/dd HH:mm:ss')
 * @returns        フォーマット済み日付文字列
 */
export function formatDate(
    input: Date | string,
    format: string = 'yyyy/MM/dd HH:mm:ss'
): string {
    const date = typeof input === 'string' ? new Date(input) : input;

    const pad = (n: number): string => n.toString().padStart(2, '0');

    const replacements: Record<string, string> = {
        yyyy: date.getFullYear().toString(),
        MM:   pad(date.getMonth() + 1),
        dd:   pad(date.getDate()),
        HH:   pad(date.getHours()),
        mm:   pad(date.getMinutes()),
        ss:   pad(date.getSeconds()),
    };

    return format.replace(/yyyy|MM|dd|HH|mm|ss/g, (m) => replacements[m]);
}
