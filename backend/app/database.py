from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    """初始化数据库 schema：统一走 Alembic 迁移体系（baseline 全量建表 + 增量迁移）。

    P2.1 前为 `create_all` + 手工 `ALTER TABLE` 补列——create_all 只建新表不改旧表，
    补列脚本与 migrations/versions 脱钩，生产 PG 上必然漂移。现在启动执行
    `alembic upgrade head`，本地/CI/生产共用同一套迁移脚本，schema 变更只经
    `alembic revision --autogenerate` 产生（P2 运维闭环）。

    历史库平滑升级：P2.1 之前由 create_all 创建的库没有 alembic_version 表，
    先按现状 stamp 到 head（不重跑、不破坏数据），再执行增量迁移。
    """
    import asyncio
    import os

    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    # 与 env.py 同源：生产 PG / 本地 SQLite 均由 settings.DATABASE_URL 提供
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    # 1. 历史库检测：无 alembic_version 但已有业务表 → stamp head（幂等）
    async with engine.connect() as conn:
        table_names = await conn.run_sync(
            lambda sync_conn: set(inspect(sync_conn).get_table_names())
        )
    if "alembic_version" not in table_names and table_names:
        # create_all 时代的历史库：表结构已与 head 一致（test_migrations 校准）
        await asyncio.to_thread(command.stamp, cfg, "head")

    # 2. 执行迁移（空库 = baseline 全量建表；已有库 = 增量迁移至 head）
    #    env.py 的 run_migrations_online 内部 asyncio.run 需要无事件循环的线程
    await asyncio.to_thread(command.upgrade, cfg, "head")
