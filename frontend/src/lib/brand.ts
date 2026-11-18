/**
 * 品牌常量层 —— 全站品牌信息的唯一事实源。
 *
 * 说明：本文件只服务对外展示。内部模块名、目录名与已登记软著名称保持
 * 原有技术标识不变，避免破坏知识产权证据链（软著/专利以登记文本为准）。
 */

export const BRAND = {
  /** 中文主品牌 */
  name: "医数可信",
  /** 英文主品牌 */
  nameEn: "MediTrust",
  /** 平台全称（用于 metadata / 页头） */
  fullName: "医数可信 MediTrust · 医疗数据要素可信流通平台",
  /** 平台定位（副标题） */
  tagline: "医疗数据要素可信流通平台",
  /** 品牌口号 */
  slogan: "医疗数据 · 可用不可见",
  /** 智能体统一称呼 */
  assistant: "医数可信助手",
  /** 组织名（用于证书、页脚） */
  org: "医数可信",
} as const;

export type Brand = typeof BRAND;
