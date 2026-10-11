import { useCallback, useEffect, useState } from "react";

export function useAsyncData(loader, dependencies = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await loader();
      setData(result);
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to load data.");
    } finally {
      setLoading(false);
    }
  }, Array.isArray(dependencies) ? dependencies : []);

  useEffect(() => {
    reload();
  }, [reload]);

  return { data, loading, error, reload, setData };
}
