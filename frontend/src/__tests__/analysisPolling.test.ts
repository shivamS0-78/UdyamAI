import { waitForAnalysisCompletion } from '@/lib/api';
import { apiFetch } from '@/lib/http';

jest.mock('@/lib/http', () => ({ apiFetch: jest.fn() }));

const mockedApiFetch = apiFetch as jest.MockedFunction<typeof apiFetch>;

function statusResponse(status: string) {
  return {
    ok: true,
    json: async () => ({ id: 'run-1', status, progress_percentage: 50 }),
  } as unknown as Response;
}

describe('waitForAnalysisCompletion', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset();
  });

  it('resolves without waiting when the run already finished', async () => {
    mockedApiFetch.mockResolvedValueOnce(statusResponse('completed'));

    const result = await waitForAnalysisCompletion('run-1', { intervalMs: 1, timeoutMs: 100 });

    expect(result.status).toBe('completed');
    expect(mockedApiFetch).toHaveBeenCalledTimes(1);
  });

  it('polls until the run reaches a terminal status', async () => {
    mockedApiFetch
      .mockResolvedValueOnce(statusResponse('pending'))
      .mockResolvedValueOnce(statusResponse('running'))
      .mockResolvedValueOnce(statusResponse('completed'));

    const result = await waitForAnalysisCompletion('run-1', { intervalMs: 1, timeoutMs: 500 });

    expect(result.status).toBe('completed');
    expect(mockedApiFetch).toHaveBeenCalledTimes(3);
  });

  it('stops polling a failed run', async () => {
    mockedApiFetch.mockResolvedValueOnce(statusResponse('failed'));

    const result = await waitForAnalysisCompletion('run-1', { intervalMs: 1, timeoutMs: 500 });

    expect(result.status).toBe('failed');
    expect(mockedApiFetch).toHaveBeenCalledTimes(1);
  });

  it('gives up instead of polling forever', async () => {
    mockedApiFetch.mockResolvedValue(statusResponse('running'));

    await expect(
      waitForAnalysisCompletion('run-1', { intervalMs: 1, timeoutMs: 20 })
    ).rejects.toThrow(/longer than expected/);
  });
});
