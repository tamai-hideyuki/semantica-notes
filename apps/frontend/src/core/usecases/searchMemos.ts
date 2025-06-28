import { apiClient } from '../../infrastructure/api/apiClient'
import { SearchResultDTO } from '../../interfaces/dtos/SearchResultDTO'

/**
 * セマンティック検索ユースケース
 * @param query 検索クエリ文字列
 * @returns 検索結果 DTO の配列
 */
export async function searchMemos(
    query: string
): Promise<SearchResultDTO[]> {
    return apiClient.post('/api/search', { query })
}
