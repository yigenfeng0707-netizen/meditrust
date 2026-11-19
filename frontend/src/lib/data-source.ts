/**
 * 数据源状态注册表（全局 pub/sub，框架无关）。
 *
 * 解决的问题：此前 apiFetch 把网络错误/401/500/超时全部静默吞掉，
 * 各业务函数回退 mock 演示数据且无任何 UI 提示——医疗平台显示假数据
 * 不知情是事故级风险。现在每次 API 调用的成败都记入注册表，
 * DataSourceBanner 据此向用户显式标注"哪些数据是演示模拟数据"。
 *
 * - recordApiOutcome(path, live, errorKind)：由 api.ts 在每次请求后调用
 * - markMockFallback(domain)：业务函数显式回退 mock 时调用
 * - useDataSourceStatus()：React 订阅 hook（组件内使用）
 * - 401 事件：apiFetch 在 401 时 dispatch window 事件
 *   `meditrust:unauthorized`，user-context 监听后清理会话回到演示用户
 */

export interface DomainStatus {
  /** 域内最近一次请求是否成功（true=后端实时数据） */
  live: boolean;
  /** 是否正处于 mock 降级（业务函数显式回退） */
  fallback: boolean;
  /** 最近错误类型（network / http:401 / http:500 / timeout / parse） */
  error: string | null;
  updatedAt: number;
}

const _registry = new Map<string, DomainStatus>();
const _listeners = new Set<() => void>();

/** 从 API 路径提取数据域名：/api/health/x → health，/api/federation/jobs → federation */
export function domainOfPath(path: string): string {
  const m = path.match(/^\/api\/([a-z0-9_-]+)/i);
  return m ? m[1].toLowerCase() : "other";
}

function _set(domain: string, patch: Partial<DomainStatus>) {
  const prev = _registry.get(domain);
  const next: DomainStatus = {
    live: prev?.live ?? false,
    fallback: prev?.fallback ?? false,
    error: prev?.error ?? null,
    updatedAt: Date.now(),
    ...patch,
  };
  _registry.set(domain, next);
  _listeners.forEach((cb) => cb());
}

/** 记录一次 API 请求结果（api.ts 内部调用） */
export function recordApiOutcome(
  path: string,
  live: boolean,
  errorKind: string | null = null,
) {
  _set(domainOfPath(path), { live, error: live ? null : errorKind });
}

/** 业务函数显式回退 mock 演示数据时调用 */
export function markMockFallback(pathOrDomain: string) {
  const domain = pathOrDomain.startsWith("/")
    ? domainOfPath(pathOrDomain)
    : pathOrDomain;
  _set(domain, { fallback: true });
}

/** 域被恢复为实时数据时清除降级标记 */
export function clearMockFallback(pathOrDomain: string) {
  const domain = pathOrDomain.startsWith("/")
    ? domainOfPath(pathOrDomain)
    : pathOrDomain;
  _set(domain, { fallback: false });
}

/** 快照：哪些域当前不可达或处于降级（给 banner 用） */
export function degradedDomains(): Array<DomainStatus & { domain: string }> {
  const out: Array<DomainStatus & { domain: string }> = [];
  _registry.forEach((st, domain) => {
    if (!st.live || st.fallback) out.push({ domain, ...st });
  });
  return out;
}

export function subscribe(cb: () => void): () => void {
  _listeners.add(cb);
  return () => _listeners.delete(cb);
}

// ---- 测试辅助 ----
export function _resetDataSourceRegistry() {
  _registry.clear();
  _listeners.forEach((cb) => cb());
}
