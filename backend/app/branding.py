"""品牌常量层 —— 后端对外展示信息的唯一事实源。

说明：只服务对外展示（FastAPI 文档、健康检查、告警文案）。内部模块名、
数据库名与已登记软著名称保持原技术标识不变，以维持知识产权证据链。
"""

BRAND_NAME = "医数可信"
BRAND_NAME_EN = "MediTrust"
BRAND_FULL_NAME = f"{BRAND_NAME} {BRAND_NAME_EN} · 医疗数据要素可信流通平台"
BRAND_TAGLINE = "医疗数据要素可信流通平台"
BRAND_SLOGAN = "医疗数据 · 可用不可见"
BRAND_ORG = "医数可信"

BRAND_DESCRIPTION = (
    "医疗数据要素可信流通平台：联邦学习医疗协作 + AI 数据治理 Copilot + "
    "差分隐私与审计存证 + 数据要素流通交易闭环，让医疗数据「可用不可见、可控可计量」"
)
