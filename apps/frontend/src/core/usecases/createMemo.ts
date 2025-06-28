import { MemoCreateDTO } from '../../interfaces/dtos/MemoCreateDTO'
import { apiClient } from '../../infrastructure/api/apiClient'

/**
 * メモ作成ユースケース
 * @param data フォーム入力データ
 * @returns { status, uuid }
 */
export async function createMemo(
    data: MemoCreateDTO
): Promise<{ status: string; uuid: string }> {
    return apiClient.post('/memo', data)
}
