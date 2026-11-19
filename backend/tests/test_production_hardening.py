"""生产加固（P0 阶段一）回归测试 —— 锁定 fail-closed 默认与资源级授权行为：

1. 配置校验：演示模式恒通过；生产模式检出出厂默认密钥/口令/通配 CORS。
2. 超管 token：HMAC 签名 + 24h 过期；旧版静态 sha256 token 被拒绝。
3. NL2SQL 数据作用域：普通调用者涉及个人表 → 注入 user_id 过滤；
   涉及 users 表或子查询 → 拒绝；特权角色不限制。
"""

import base64
import hashlib
import hmac
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import production_config_problems, settings  # noqa: E402
from app.services.data_lake import engine as de  # noqa: E402


# ------------------------------------------------------------------
# 1. 生产配置校验（fail-closed）
# ------------------------------------------------------------------

def test_production_config_problems_detects_demo_defaults(monkeypatch):
    """生产模式：六项出厂默认/缺失配置全部被检出。"""
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    # conftest 已预置非默认 YIBAO_SESSION_SECRET，此处显式还原为出厂默认值以检出
    monkeypatch.setattr(settings, "YIBAO_SESSION_SECRET", "please-change-this")
    problems = production_config_problems()
    assert len(problems) == 6
    joined = " ".join(problems)
    assert "ADMIN_PASSWORD" in joined
    assert "YIBAO_ADMIN_SECRET" in joined
    assert "YIBAO_SESSION_SECRET" in joined
    assert "CORS_ORIGINS" in joined
    assert "YIBAO_DATA_KEY" in joined
    assert "FEDERATION_PARAM_KEY" in joined


def test_production_config_problems_detects_env_example_placeholders(monkeypatch):
    """从 .env.example 直接复制未替换的占位值同样被判为未配置。"""
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "please-change-this-admin-password")
    monkeypatch.setattr(settings, "YIBAO_ADMIN_SECRET", "please-change-this-admin-secret")
    monkeypatch.setattr(settings, "YIBAO_SESSION_SECRET", "please-change-this-to-a-random-secret")
    problems = production_config_problems()
    assert len(problems) == 6


def test_production_config_problems_pass_with_real_config(monkeypatch):
    """生产模式：配置独立密钥/口令与 CORS 白名单后通过。"""
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "ProdAdmin@2027")
    monkeypatch.setattr(settings, "YIBAO_ADMIN_SECRET", "prod-admin-secret-xyz")
    monkeypatch.setattr(settings, "YIBAO_SESSION_SECRET", "prod-session-secret-xyz")
    monkeypatch.setattr(settings, "CORS_ORIGINS", "https://meditrust.example.com")
    # 32 字节密钥的 base64 形态（YIBAO_DATA_KEY / FEDERATION_PARAM_KEY）
    monkeypatch.setattr(settings, "YIBAO_DATA_KEY", base64.b64encode(bytes(32)).decode())
    monkeypatch.setattr(settings, "FEDERATION_PARAM_KEY", base64.b64encode(bytes(32)).decode())
    assert production_config_problems() == []


def test_demo_mode_config_problems_always_empty():
    """演示模式：恒通过（零摩擦）。"""
    assert production_config_problems() == []


# ------------------------------------------------------------------
# 2. 超管 token：签名 + 过期
# ------------------------------------------------------------------

def test_admin_token_has_expiry_and_signature():
    """新格式 exp|sig：含过期时间，签名可复算。"""
    from app.routers import admin

    token = admin._issue_admin_token("admin")
    assert "|" in token
    exp_s, sig = token.rsplit("|", 1)
    exp = int(exp_s)
    assert 86000 < exp - time.time() <= 86400  # 24h 窗口
    payload = f"admin|admin|{exp}"
    expected = hmac.new(
        settings.YIBAO_ADMIN_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    assert hmac.compare_digest(sig, expected)
    assert admin._verify_admin_token(token)


def test_admin_token_rejects_expired_and_legacy_static(monkeypatch):
    """过期 token 与旧版静态 sha256 token 均被拒绝。"""
    from app.routers import admin

    # 旧格式：sha256("admin|admin|secret")，无过期
    legacy = hashlib.sha256(
        f"admin|admin|{settings.YIBAO_ADMIN_SECRET}".encode("utf-8")
    ).hexdigest()
    assert not admin._verify_admin_token(legacy)
    assert not admin._verify_admin_token(None)
    assert not admin._verify_admin_token("garbage")


def test_admin_token_expires(monkeypatch):
    """token 过期后校验失败。"""
    from app.routers import admin

    # 构造一个已过期的 token：直接回算签名
    exp = int(time.time()) - 10
    payload = f"admin|admin|{exp}"
    sig = hmac.new(
        settings.YIBAO_ADMIN_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    assert not admin._verify_admin_token(f"{exp}|{sig}")


# ------------------------------------------------------------------
# 3. NL2SQL 数据作用域（资源级授权）
# ------------------------------------------------------------------

class TestPersonalScopeEnforcement:
    """_enforce_personal_scope：普通用户视角的 SQL 重写/拒绝。"""

    def test_aggregate_template_gets_user_filter(self):
        sql = ("SELECT visit_type, COUNT(*) AS visit_count FROM medical_records "
               "GROUP BY visit_type ORDER BY visit_count DESC")
        ok, scoped, reason = de._enforce_personal_scope(sql, 7)
        assert ok, reason
        assert "WHERE user_id = 7" in scoped
        assert "COUNT(*)" in scoped  # 列函数不受影响

    def test_non_personal_table_passes_through(self):
        sql = "SELECT COUNT(*) FROM policy_documents LIMIT 100"
        ok, scoped, _ = de._enforce_personal_scope(sql, 7)
        assert ok and scoped == sql

    def test_users_table_blocked_for_member(self):
        sql = "SELECT insurance_type, COUNT(*) FROM users GROUP BY insurance_type"
        ok, _, reason = de._enforce_personal_scope(sql, 7)
        assert not ok
        assert "users" in reason

    def test_where_sql_rejected(self):
        sql = "SELECT * FROM medical_records WHERE hospital = '市一医院'"
        ok, _, reason = de._enforce_personal_scope(sql, 7)
        assert not ok
        assert "WHERE" in reason

    def test_subquery_rejected_but_column_function_allowed(self):
        # COUNT(*) 这类列函数不算子查询
        ok, scoped, _ = de._enforce_personal_scope(
            "SELECT SUM(total_cost) FROM medical_records", 7)
        assert ok and "user_id = 7" in scoped
        # 真子查询被拒绝
        ok, _, reason = de._enforce_personal_scope(
            "SELECT * FROM (SELECT * FROM medical_records) t", 7)
        assert not ok
        assert "子查询" in reason

    def test_mixed_personal_and_public_tables_scoped(self):
        sql = ("SELECT COUNT(*) FROM medical_records m JOIN policy_documents p "
               "ON m.diagnosis = p.title")
        ok, scoped, _ = de._enforce_personal_scope(sql, 7)
        assert not ok  # JOIN 含个人表 → 按复杂 SQL 拒绝（fail-closed）


@pytest.mark.asyncio
async def test_smart_query_member_scope_applied():
    """smart_query：member 调用者 → 个人表查询自动限定本人；特权角色不限制。"""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from datetime import datetime

    from app.models import Base, MedicalRecord, User

    _engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(_engine, expire_on_commit=False)
    async with factory() as session:
        session.add(User(id=1, name="甲", age=60, gender="男", city="杭州",
                         insurance_type="职工医保", employee_status="退休"))
        session.add(User(id=2, name="乙", age=55, gender="女", city="上海",
                         insurance_type="居民医保", employee_status="在职"))
        for uid in (1, 2):
            session.add(MedicalRecord(user_id=uid, date=datetime(2025, 3, 1),
                                      hospital="市一医院", department="内科",
                                      diagnosis="感冒", visit_type="门诊",
                                      total_cost=100.0, reimbursed_amount=60.0))
        await session.commit()

        # member（uid=1）：费用汇总模板被限定为本人
        r = await de.smart_query(session, "帮我汇总就医费用", llm=None,
                                 caller_uid=1, caller_role="member")
        assert r["query"]["sql"] is not None
        assert "WHERE user_id = 1" in r["query"]["sql"]
        assert r["query"]["row_count"] == 1  # 只有本人那条聚合行
        assert "user_id=1" in r["query"]["filters"]

        # 特权角色（regulator）：不限制
        r2 = await de.smart_query(session, "帮我汇总就医费用", llm=None,
                                  caller_uid=1, caller_role="regulator")
        assert "WHERE user_id" not in (r2["query"]["sql"] or "")

        # member 查 users 表 → 被拦截
        r3 = await de.smart_query(session, "有多少参保人", llm=None,
                                  caller_uid=1, caller_role="member")
        assert r3["query"]["source"] == "blocked"

        # 匿名（演示）调用者：不强制
        r4 = await de.smart_query(session, "帮我汇总就医费用", llm=None)
        assert "WHERE user_id" not in (r4["query"]["sql"] or "")
