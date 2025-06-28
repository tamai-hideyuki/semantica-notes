import { useMutation, useQueryClient, UseMutationResult } from '@tanstack/react-query';
import { createMemo as runCreate } from '../../core/usecases/createMemo';
import type { MemoCreateDTO } from '../dtos/MemoCreateDTO';

export function useCreateMemo(): UseMutationResult<{ status: string; uuid: string }, Error, MemoCreateDTO> {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: MemoCreateDTO) => runCreate(data),
        onSuccess: () => {
            // 検索結果キャッシュを無効化
            queryClient.invalidateQueries({ queryKey: ['search'] });
        },
    });
}
