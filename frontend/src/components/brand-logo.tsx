import { cn } from "@/lib/utils";
import { BRAND } from "@/lib/brand";

type BrandLogoProps = {
  className?: string;
  compact?: boolean;
  light?: boolean;
};

/** 品牌标志：数据要素可信流通。品牌文案统一从 `@/lib/brand` 读取。 */
export function BrandLogo({ className, compact = false, light = false }: BrandLogoProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span
        className="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-white shadow-lg shadow-cyan-500/25"
        aria-hidden="true"
      >
        <img src="/logo.jpg" alt="" className="h-full w-full object-cover" />
      </span>
      {!compact && (
        <div className="min-w-0">
          <div className={cn("text-xl font-bold leading-none tracking-[.04em]", light ? "text-slate-800" : "text-slate-900")}>
            {BRAND.name}
          </div>
          <div className={cn("mt-1 text-[10px] tracking-[.08em]", light ? "text-slate-500" : "text-slate-500")}>
            {BRAND.slogan}
          </div>
        </div>
      )}
    </div>
  );
}
