import path from "path";
import { Global } from "../global";

export const ModelBatcher = (() => {
  const cache = new Map<string, { v: unknown; t: number; s?: boolean }>();
  const inflight = new Map<string, Promise<unknown>>();
  const queue: Array<() => Promise<void>> = [];
  let running = 0;
  const CONCURRENCY = 4;
  const CACHE_FILE = path.join(Global.Path.state, "model_cache.json");
  const METRICS_FILE = path.join(Global.Path.state, "model_metrics.json");
  const METRICS = { hits: 0, misses: 0, requests: 0, persisted: 0 };
  let defaultTTL = 5 * 60 * 1000;

  // load persisted cache (only JSON-serializable entries)
  Bun.file(CACHE_FILE)
    .text()
    .then((t) => {
      const obj = t ? JSON.parse(t) : {};
      for (const k of Object.keys(obj)) {
        const item = obj[k];
        if (item && typeof item.t === "number" && "v" in item) {
          cache.set(k, { v: item.v, t: item.t, s: true });
        }
      }
    })
    .catch(() => {});

  // load metrics if present
  Bun.file(METRICS_FILE)
    .text()
    .then((t) => {
      const obj = t ? JSON.parse(t) : {};
      for (const k of Object.keys(METRICS)) {
        if (typeof obj[k] === "number") METRICS[k as keyof typeof METRICS] = obj[k];
      }
    })
    .catch(() => {});

  function persistCache() {
    const out: Record<string, { v: unknown; t: number }> = {};
    for (const [k, v] of cache.entries()) {
      if (!v.s) continue;
      out[k] = { v: v.v, t: v.t };
    }
    Bun.file(CACHE_FILE).write(JSON.stringify(out)).then(() => {}).catch(() => {});
  }

  function persistMetrics() {
    METRICS.persisted++;
    Bun.file(METRICS_FILE).write(JSON.stringify(METRICS)).then(() => {}).catch(() => {});
  }

  // periodic metrics persist
  ;(() => {
    const id = setInterval(() => {
      persistMetrics();
    }, 30 * 1000);
    if (typeof id === "number") {
      // noop: keep interval running
    }
  })();

  function next() {
    if (running >= CONCURRENCY) return;
    const task = queue.shift();
    if (!task) return;
    running++;
    void task().then(() => {
      running--;
      next();
    });
  }

  function enqueue<T>(fn: () => Promise<T>) {
    return new Promise<T>((res, rej) => {
      const task = async () => {
        try {
          const out = await fn();
          res(out);
        } catch (error) {
          rej(error);
        }
      };
      queue.push(task);
      next();
    });
  }

  function isSerializable(x: unknown) {
    try {
      JSON.stringify(x);
      return true;
    } catch {
      return false;
    }
  }

  async function call<T>(key: string, fn: () => Promise<T>, ttl?: number): Promise<T> {
    METRICS.requests++;
    const usedTTL = ttl ?? defaultTTL;
    const c = cache.get(key);
    if (c && Date.now() - c.t < usedTTL) {
      METRICS.hits++;
      return c.v as T;
    }
    METRICS.misses++;
    const p = inflight.get(key);
    if (p) return p as Promise<T>;
    const promise = enqueue(async () => {
      const r = await fn();
      const serial = isSerializable(r);
      cache.set(key, { v: r, t: Date.now(), s: serial });
      if (serial) persistCache();
      inflight.delete(key);
      return r;
    });
    inflight.set(key, promise);
    return promise as Promise<T>;
  }

  function invalidate(key: string) {
    cache.delete(key);
    persistCache();
  }

  function setDefaultTTL(ms: number) {
    if (ms > 0) defaultTTL = ms;
  }

  function clear() {
    cache.clear();
    inflight.clear();
    queue.length = 0;
    persistCache();
  }

  function metrics() {
    return {
      ...METRICS,
      inflight: inflight.size,
      queued: queue.length,
      cacheSize: cache.size,
    };
  }

  return {
    call,
    invalidate,
    setDefaultTTL,
    clear,
    metrics,
  };
})();
