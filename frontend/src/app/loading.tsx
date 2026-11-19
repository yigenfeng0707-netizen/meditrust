/**
 * 全局路由加载态（Next App Router 约定）：路由切换期间显示骨架，
 * 替代此前"数据为 null 时整页空白"的体验（P0-前端-2）。
 */
export default function Loading() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center p-6">
      <div className="flex flex-col items-center gap-3 text-gray-400">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-500" />
        <span className="text-sm">正在加载数据…</span>
      </div>
    </div>
  );
}
