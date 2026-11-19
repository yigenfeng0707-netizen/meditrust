"use client";

/**
 * 数据源降级横幅：当任一数据域后端不可达/回退 mock 时，显式提示用户。
 *
 * 此前 apiFetch 吞掉所有错误并静默回退 mock —— 医疗平台显示假数据无提示
 * 是事故级风险（P0-前端-1）。现在用户会看到："以下模块后端暂不可达，
 * 当前展示为演示模拟数据：健康画像 / 联邦协作…"
 */

import { useSyncExternalStore } from "react";
import { subscribe, degradedDomains, type DomainStatus } from "@/lib/data-source";

const DOMAIN_LABELS: Record<string, string> = {
  health: "健康画像",
  coverage: "医保待遇",
  claims: "报销助手",
  policy: "政策参谋",
  security: "权益管家",
  agents: "智能对话",
  body: "档案管家",
  drugs: "药品卫士",
  eeg: "脑电卫士",
  imaging: "影像卫士",
  federation: "联邦协作",
  governance: "病历治理",
  marketplace: "数据要素市场",
  payments: "支付结算",
  cancer: "泛癌卫士",
  users: "用户",
  data: "数据管家",
  admin: "管理后台",
};

function labelOf(domain: string): string {
  return DOMAIN_LABELS[domain] ?? domain;
}

function errorLabel(st: DomainStatus): string {
  switch (st.error) {
    case "network":
      return "网络连接失败";
    case "timeout":
      return "请求超时";
    case "http:401":
      return "登录已过期";
    case "parse":
      return "响应格式异常";
    default:
      return st.error ? `服务异常（${st.error}）` : "服务不可达";
  }
}

export function DataSourceBanner() {
  const degraded = useSyncExternalStore(
    subscribe,
    degradedDomains,
    degradedDomains,
  );

  if (degraded.length === 0) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="w-full border-b border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-800"
    >
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-3 gap-y-1">
        <span className="font-semibold whitespace-nowrap">
          ⚠ 后端服务异常，以下模块当前展示为演示模拟数据：
        </span>
        <span className="flex flex-wrap gap-1.5">
          {degraded.map(({ domain, ...st }) => (
            <span
              key={domain}
              className="inline-flex items-center rounded border border-amber-300 bg-white px-2 py-0.5 text-xs"
              title={errorLabel(st)}
            >
              {labelOf(domain)}
              <span className="ml-1 text-amber-500">·{errorLabel(st)}</span>
            </span>
          ))}
        </span>
        <span className="ml-auto text-xs text-amber-600 whitespace-nowrap">
          恢复后将自动切换回实时数据
        </span>
      </div>
    </div>
  );
}
