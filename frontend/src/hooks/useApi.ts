import { useEffect, useState } from 'react';

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Run an async loader whenever `deps` change, ignoring stale responses.
 * A short debounce keeps slider drags from flooding the API.
 */
export function useApi<T>(
  loader: () => Promise<T>,
  deps: readonly unknown[],
  debounceMs = 150,
): ApiState<T> {
  const [state, setState] = useState<ApiState<T>>({ data: null, loading: true, error: null });

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    const timer = setTimeout(() => {
      loader()
        .then((data) => !cancelled && setState({ data, loading: false, error: null }))
        .catch(
          (err: unknown) =>
            !cancelled &&
            setState({
              data: null,
              loading: false,
              error: err instanceof Error ? err.message : String(err),
            }),
        );
    }, debounceMs);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
    // The loader is recreated each render; `deps` captures its real inputs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
