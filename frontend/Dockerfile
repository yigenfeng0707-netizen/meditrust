# 医数可信 - 前端生产镜像
# 多阶段构建：deps → builder → runner，最终镜像不含 node_modules / 源码

# ============== 1. 安装依赖 ==============
FROM node:18-alpine AS deps
WORKDIR /app

# 仅装包管理器，避免反复重建时重装
RUN npm install -g pnpm@9

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# ============== 2. 构建 ==============
FROM node:18-alpine AS builder
WORKDIR /app

RUN npm install -g pnpm@9

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 构建时注入后端地址（默认本地，生产由 docker-compose / 运行时覆盖）
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
RUN pnpm build

# ============== 3. 运行（精简镜像） ==============
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
# 运行时由 docker-compose 注入真实后端地址
ENV NEXT_PUBLIC_API_URL=http://localhost:8000

# tini 处理 PID 1 信号转发，docker stop 时 Next server 优雅退出（P2 容器化加固）
RUN apk add --no-cache tini \
    && addgroup -g 1001 -S nodejs \
    && adduser -S nextjs -u 1001 -G nodejs

# Next standalone 产物已内嵌所需 node_modules
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 非 root 用户运行
USER nextjs

EXPOSE 3000

# 容器健康检查（K8s/compose 就绪探针用）
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s \
    CMD wget -qO- http://localhost:3000/ || exit 1

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "server.js"]
