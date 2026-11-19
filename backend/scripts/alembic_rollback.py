"""数据库迁移降级脚本（P3 运维闭环）。

配合 init_db 的 alembic upgrade head，提供安全的回退通道：

    # 查看当前版本与可回退目标
    python scripts/alembic_rollback.py --status

    # 降级到上一版本（交互确认）
    python scripts/alembic_rollback.py --down one

    # 降级到指定 revision
    python scripts/alembic_rollback.py --to e74955a4c306

    # 跳过确认（CI/编排场景，慎用）
    python scripts/alembic_rollback.py --down one --yes

安全原则：
- 降级前自动做一次数据库快照备份（SQLite 在线备份 / PG pg_dump 提示），
  失败则中止；
- 降级会丢列（ADD COLUMN 的反向操作是 DROP COLUMN），脚本显式警告；
- 生产场景建议：先停写入 → 备份 → 降级 → 回滚应用镜像 → 验证。
  完整部署回滚流程见 docs/部署回滚预案.md。
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from alembic.runtime.migration import MigrationContext  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402

from app.config import settings  # noqa: E402


def _cfg() -> Config:
    cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return cfg


def _current_revision() -> str:
    """当前库的 head revision（同步引擎只读查询）。"""
    sync_url = (
        settings.DATABASE_URL
        .replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        .replace("sqlite+aiosqlite://", "sqlite:///")
    )
    engine = create_engine(sync_url)
    try:
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            return ctx.get_current_revision() or "(空库)"
    finally:
        engine.dispose()


def _snapshot() -> Path | None:
    """降级前快照备份：SQLite 原生在线备份；PG 环境提示用 backup_pg.sh。"""
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        backups = _BACKEND_DIR / "backups"
        backups.mkdir(parents=True, exist_ok=True)
        dst = backups / f"pre_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        import sqlite3

        src = url.split("///")[-1]
        if not os.path.exists(src):
            return None
        src_conn = sqlite3.connect(src)
        try:
            dst_conn = sqlite3.connect(str(dst))
            try:
                src_conn.backup(dst_conn)
            finally:
                dst_conn.close()
        finally:
            src_conn.close()
        print(f"[快照] SQLite 备份完成：{dst}")
        return dst
    # PG：pg_dump 依赖客户端工具，提示走专用脚本
    print("[快照] PostgreSQL 环境，请先执行：bash scripts/backup_pg.sh")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="数据库迁移降级（alembic downgrade 包装）")
    parser.add_argument("--status", action="store_true", help="查看当前迁移版本")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--down", choices=["one"], help="降级到上一版本")
    group.add_argument("--to", metavar="REVISION", help="降级到指定 revision")
    parser.add_argument("--yes", action="store_true", help="跳过交互确认（慎用）")
    args = parser.parse_args()

    if args.status or not (args.down or args.to):
        head = _current_revision()
        print(f"当前数据库迁移版本: {head}")
        versions = _BACKEND_DIR / "migrations" / "versions"
        print("可用 revision（按链顺序）:")
        for f in sorted(versions.glob("*.py")):
            print(f"  {f.name}")
        return 0

    target = "-1" if args.down == "one" else args.to
    current = _current_revision()
    print(f"当前版本: {current}")
    print(f"目标: {target}")

    snapshot = _snapshot()
    if snapshot is None and not settings.DATABASE_URL.startswith("sqlite"):
        if not args.yes:
            print("未自动备份（PG），继续前请确认已完成 backup_pg.sh 备份")
            if input("继续降级？输入 yes 确认: ").strip().lower() != "yes":
                print("已中止")
                return 1
    if not args.yes:
        print("⚠️  降级会执行 DROP COLUMN 等不可逆操作，列数据将丢失！")
        if input("确认降级？输入 yes 确认: ").strip().lower() != "yes":
            print("已中止")
            return 1

    cfg = _cfg()
    command.downgrade(cfg, target)
    print(f"[完成] 已降级至 {_current_revision()}")
    if snapshot:
        print(f"[回滚备份] 如需还原：cp {snapshot} <源库路径>（先停服务）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
