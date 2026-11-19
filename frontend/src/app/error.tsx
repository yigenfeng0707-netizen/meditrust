"use client";

/**
 * 全局错误边界（Next App Router 约定）。
 *
 * 此前全站无 error.tsx / ErrorBoundary：任意页面渲染抛错即整页白屏，
 * 且 apiFetch 的错误被静默吞掉（P0-前端-2）。现在未预期异常给用户
 * 明确的"出错了"界面 + 重试入口，而不是空白或假数据。
 */

import { useEffect } from "react";
import { AlertTriangle, RotateCw } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // 上报到后端日志通道（失败不影响用户）
    console.error("[页面异常]", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="mx-auto max-w-md rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <AlertTriangle className="mx-auto mb-3 h-10 w-10 text-red-500" />
        <h2 className="mb-2 text-lg font-semibold text-red-900">页面出现异常</h2>
        <p className="mb-1 text-sm text-red-700">
          页面渲染时发生未预期的错误。这通常与当前展示的数据有关，重试通常可以恢复。
        </p>
        {error.digest && (
          <p className="mb-4 text-xs text-red-400">错误编号：{error.digest}</p>
        )}
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-700"
        >
          <RotateCw className="h-4 w-4" />
          重试
        </button>
      </div>
    </div>
  );
}
