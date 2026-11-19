#!/usr/bin/env bash
# PostgreSQL 备份脚本（P3 运维闭环）——pg_dump 在线备份 + gzip 压缩 + 轮转保留。
#
# SQLite 库请用 scripts/backup_db.py（原生在线备份 API）；本脚本面向
# docker-compose prod profile 的 PostgreSQL（等保三级"数据备份"控制项）。
#
# 用法：
#   bash scripts/backup_pg.sh                      # 备份 + 默认保留 7 天
#   bash scripts/backup_pg.sh --keep 30            # 保留 30 天
#   bash scripts/backup_pg.sh --no-compress        # 不压缩（调试用）
#
# 生产调度（crontab -e）：
#   # 每天 02:03 执行 PG 备份，保留 30 天，日志写 /var/log/meditrust
#   3 2 * * * cd /srv/meditrust && bash scripts/backup_pg.sh --keep 30 >> /var/log/meditrust/backup.log 2>&1
#
# 等保三级要点：备份目录应挂载独立存储卷/异地副本（本脚本仅产生本地副本，
# 异地同步由 rsync/OSS 同步任务承接，见 docs/部署回滚预案.md）。
#
# 恢复演练（每季度一次并留存记录）：
#   1. 停止后端（docker compose --profile prod stop backend-prod）
#   2. gunzip -c backups/pg_YYYYMMDD_HHMMSS.sql.gz | docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"
#   3. 重启后端并访问 /api/health/detailed 确认 database available

set -euo pipefail

KEEP_DAYS=7
COMPRESS=1
SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep) KEEP_DAYS="$2"; shift 2 ;;
    --no-compress) COMPRESS=0; shift ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

# compose 环境变量统一从 .env / 当前 shell（POSTGRES_* 由 compose 传入）
POSTGRES_USER="${POSTGRES_USER:-yibao}"
POSTGRES_DB="${POSTGRES_DB:-yibao}"
BACKUP_DIR="${BACKUP_DIR:-$SRC_DIR/backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/pg_${STAMP}.sql"

mkdir -p "$BACKUP_DIR"

echo "[备份] $(date '+%Y-%m-%d %H:%M:%S') pg_dump → ${OUT}.gz"

# docker compose exec 经 TTY 会有警告，-T 关闭；postgres 服务名固定
if ! docker compose -f "$SRC_DIR/docker-compose.yml" exec -T postgres \
    pg_dump -U "$POSTGRES_USER" --no-owner --no-acl "$POSTGRES_DB" > "$OUT"; then
  echo "[失败] pg_dump 执行失败：postgres 服务是否运行？compose 是否在 prod profile 下？"
  rm -f "$OUT"
  exit 1
fi

if [[ "$COMPRESS" == "1" ]]; then
  gzip -f "$OUT"
  OUT="${OUT}.gz"
fi

SIZE="$(du -h "$OUT" | cut -f1)"
echo "[完成] $OUT（$SIZE）"

# 轮转：删除超期备份（按文件修改时间）
if [[ "$KEEP_DAYS" -gt 0 ]]; then
  DELETED="$(find "$BACKUP_DIR" -name 'pg_*.sql*' -mtime "+$KEEP_DAYS" -print -delete | wc -l)"
  if [[ "$DELETED" -gt 0 ]]; then
    echo "[轮转] 清理 $DELETED 个超过 ${KEEP_DAYS} 天的备份"
  fi
fi
