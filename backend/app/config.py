from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./yibao.db"
    REDIS_URL: str = "redis://localhost:6379"

    # 主力 LLM：aiping 网关（Kimi-K3，OpenAI 兼容）
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://aiping.cn/api/v1"
    LLM_MODEL: str = "Kimi-K3"

    # 备选 LLM：奇绩算力（gpt-5.6-sol，主力 Kimi-K3 故障时自动切换；变量名沿用 DASHSCOPE_）
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://api.openai-next.com/v1"
    DASHSCOPE_MODEL: str = "gpt-5.6-sol"

    # 视觉模型：aiping 网关（GLM-4.6V，供影像/图文理解扩展使用）
    VISION_API_KEY: str = ""
    VISION_BASE_URL: str = "https://aiping.cn/api/v1"
    VISION_MODEL: str = "GLM-4.6V"

    # P2.5 LLM 生产化：全局并发限流（主力+备选+视觉共用一个信号量，
    # 超出路数的请求排队等待）。10 路压测实测主力网关 429 限频，
    # 8 路以内可主动避开限流阈值；1 = 关闭排队语义以外的并发。
    LLM_MAX_CONCURRENCY: int = 8

    # 泛癌卫士（Oncoformer）：留空 = 真模型不可用，降级预计算队列模式
    ONCOFORMER_CKPT_PATH: str = ""
    # COMPASS 队列目录（含 metadata.parquet + cxr_images），本地实时推理用
    ONCOFORMER_DATA_DIR: str = ""
    # 预计算队列 JSON 覆盖路径（默认 <仓库根>/data/cancer_cohort.json）
    ONCOFORMER_COHORT_JSON: str = ""

    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # 路演离线模式：跳过 LLM/知识库初始化，全程使用关键词+mock降级（无网络依赖）
    DEMO_OFFLINE: bool = False

    # 身份作用域开关（P0 鉴权强制）：
    # false（默认，生产模式）= 业务端点强制 X-User-Token 与 user_id 匹配（管理员可代查）；
    # true = 演示模式（路演/Demo 环境，user-switcher 零摩擦，业务端点信任 user_id 路径参数）。
    # 安全原则：fail-closed —— 未显式声明 DEMO_MODE=true 的部署一律按生产模式对待，
    # 并在启动时校验密钥/口令（见 production_config_problems），不安全配置拒绝启动。
    DEMO_MODE: bool = False

    # 存证链外部锚定：RFC 3161 可信时间戳机构地址（留空 = 仅离线留痕不请求 TSA）
    CHAIN_ANCHOR_TSA_URL: str = "https://freetsa.org/tsr"
    # 定时锚定周期（小时；0 = 关闭，仅管理端手动锚定）
    CHAIN_ANCHOR_INTERVAL_HOURS: int = 24

    # 等保三级·安全审计留存：库内保留天数（等保 2.0 三级要求 ≥6 个月，超期先归档库外再清理）
    AUDIT_RETENTION_DAYS: int = 183
    # 审计留存清理周期（小时；0 = 关闭，仅管理端/脚本手动归档）
    AUDIT_CLEANUP_INTERVAL_HOURS: int = 24
    # 审计归档目录（JSONL append-only，超期记录删除前的库外留存）
    AUDIT_ARCHIVE_DIR: str = "./audit_archive"

    # 等保三级·存储加密：敏感字段 AES-256-GCM 数据密钥（32 字节，base64/hex；留空 = 明文兼容模式）
    YIBAO_DATA_KEY: str = ""

    # P1.1 联邦节点：参数上行 AES-256-GCM 信封密钥（与医院侧节点 Agent 共享，32 字节
    # base64/hex/口令；留空 = 明文兼容联调模式，生产必须配置）
    FEDERATION_PARAM_KEY: str = ""

    # P1.2 联邦密钥轮换：多版本密钥环（enc2 信封按 key_id 寻钥）。
    # 格式 "key_id:key" 逗号分隔（key 为 32 字节 base64/hex），最后一个为活跃写入密钥，
    # 其余为过渡期保留的解密密钥；key_id = sha256(key)[:8] 十六进制，可由
    # scripts/rotate_federation_key.py 生成。留空时回退单密钥 FEDERATION_PARAM_KEY
    # （自动计算 key_id）。轮换完成后移除旧密钥条目 → 历史密文永久不可解密。
    FEDERATION_PARAM_KEYS: str = ""

    # P1.3 恶意参数方向检测：节点上行参数与当前全局模型的 cosine 相似度低于阈值 →
    # 422 拒绝（参数不落库）。0.0 = 仅拒绝方向反转/正交的明显篡改；设为负数关闭检测；
    # 合法 DP 更新方向与全局模型高度一致（接近 1），不会误伤。
    FEDERATION_COS_THRESHOLD: float = 0.0

    # P1.4 隐私预算核算：RDP 矩会计的 (ε, δ) 转换目标 δ（每任务 per-node 视角）。
    # 常规取 ≤1/数据集规模（如 10 万样本取 1e-5）；仅影响报告口径，不改噪声机制。
    DP_ACCOUNTANT_DELTA: float = 1e-5

    # 告警触达通道：钉钉/飞书群机器人 Webhook（留空 = 仅日志不推送）
    ALERT_WEBHOOK_URL: str = ""
    # 管理端登录失败多少次触发撞库告警（滑窗内计数）
    ALERT_LOGIN_FAILURE_THRESHOLD: int = 5

    # 支付宝在线支付：sandbox = 沙箱零配置；live = 真实收款（个人电脑网站支付）
    ALIPAY_MODE: str = "sandbox"
    ALIPAY_APP_ID: str = ""
    # PKCS1 PEM（换行用 \n 转义写入 .env）；私钥切勿提交仓库/粘贴聊天。留空兜底读 backend/keys/
    ALIPAY_APP_PRIVATE_KEY: str = ""
    ALIPAY_PUBLIC_KEY: str = ""
    # 支付成功异步回调地址（需公网 HTTPS，如 ms.show 域名）
    ALIPAY_NOTIFY_URL: str = ""
    # 支付完成同步跳转地址（电脑网站支付 return_url，留空 = 不跳转）
    ALIPAY_RETURN_URL: str = ""

    # OCR 服务：OCR.space
    OCR_API_KEY: str = ""
    OCR_API_URL: str = "https://api.ocr.space/parse/image"

    # 管理后台超级管理员（/admin 页面登录用）
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "医数可信@2026"
    # 管理员 token 签发密钥（改后所有已签发 token 失效）
    YIBAO_ADMIN_SECRET: str = "oumed-admin-secret"

    # 部署/鉴权相关：auth.py 、main.py 直接从环境变量读取，
    # 此处声明是为了让 pydantic-settings 解析 .env 时不报 extra_forbidden 错误
    YIBAO_API_KEY: str = ""
    YIBAO_SESSION_SECRET: str = "please-change-this"
    CORS_ORIGINS: str = "*"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()


# ============================================================
# 生产模式配置校验（fail-closed）
# ============================================================

# 出厂默认值清单：生产模式（DEMO_MODE=false）下出现这些值 = 未安全配置
_DEMO_DEFAULT_ADMIN_PASSWORD = "医数可信@2026"
_DEMO_DEFAULT_ADMIN_SECRET = "oumed-admin-secret"
_DEMO_DEFAULT_SESSION_SECRET = "please-change-this"

# 占位符模式：从 .env.example 直接复制未替换的值同样视为未配置
_PLACEHOLDER_TOKENS = ("please-change", "change-this", "your-", "-here", "replace-me")


def _looks_unconfigured(value: str) -> bool:
    """值是否为空、出厂默认或明显的占位符（如 .env.example 未替换的值）。"""
    if not value:
        return True
    lowered = value.strip().lower()
    return any(tok in lowered for tok in _PLACEHOLDER_TOKENS)


def production_config_problems() -> list[str]:
    """生产模式配置校验：返回待修复项清单（空列表 = 通过）。

    演示模式（DEMO_MODE=true）恒通过：Demo 环境依赖出厂默认值零摩擦启动；
    生产模式（DEMO_MODE=false，默认）必须逐项通过，否则 app.main 在 lifespan
    拒绝启动（详见 main.py），避免"漏配一个 env 即完全敞开"。
    """
    if settings.DEMO_MODE:
        return []
    problems: list[str] = []
    if _looks_unconfigured(settings.ADMIN_PASSWORD) or settings.ADMIN_PASSWORD == _DEMO_DEFAULT_ADMIN_PASSWORD:
        problems.append(
            "ADMIN_PASSWORD 未配置或仍为出厂默认值/占位符（生产环境必须通过环境变量/.env 设置独立口令）"
        )
    if _looks_unconfigured(settings.YIBAO_ADMIN_SECRET) or settings.YIBAO_ADMIN_SECRET == _DEMO_DEFAULT_ADMIN_SECRET:
        problems.append(
            "YIBAO_ADMIN_SECRET 未配置或仍为出厂默认值/占位符（超管 token 签发密钥，设置后所有旧 token 失效）"
        )
    if _looks_unconfigured(settings.YIBAO_SESSION_SECRET):
        problems.append(
            "YIBAO_SESSION_SECRET 未配置或仍为出厂默认值/占位符（用户会话 token 的 HMAC 签名密钥）"
        )
    if settings.CORS_ORIGINS.strip() == "*":
        problems.append(
            "CORS_ORIGINS 为 *（全域放行），生产环境必须收敛为前端域名白名单（逗号分隔）"
        )
    # 数据加密与联邦传输加密：留空即静默降级为明文模式，医疗数据场景不可接受，
    # 因此与口令/CORS 同级强制（32 字节 base64/hex 密钥可由 scripts 生成）
    if _looks_unconfigured(settings.YIBAO_DATA_KEY):
        problems.append(
            "YIBAO_DATA_KEY 未配置或为占位符（敏感字段 AES-256-GCM 数据密钥；留空 = 明文兼容模式，生产必须配置 32 字节 base64/hex 密钥）"
        )
    if _looks_unconfigured(settings.FEDERATION_PARAM_KEY):
        problems.append(
            "FEDERATION_PARAM_KEY 未配置或为占位符（联邦节点参数上行 AES-256-GCM 信封密钥；留空 = 明文兼容联调模式，生产必须配置）"
        )
    return problems

