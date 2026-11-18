# 医数可信 MediTrust

> 医疗数据要素可信流通平台
> 让医疗数据「**可用不可见、可控可计量**」

HICOOL 2027 全球创业者峰会暨创业大赛 · **本土组 / 创客期 / 个人参赛** · 赛道：软件和信息服务/科技服务

---

## 一句话价值

医院之间数据不能出院、不敢共享，导致专病模型只能在小样本上训练；保险公司和健康服务方又拿不到合规的医学证据。
本平台用**联邦学习 + 差分隐私 + 可验证审计链**把"数据协作"变成可度量、可审计、可计量的工程能力，并在其上承载 9 个医疗 AI 应用，形成"1 个可信数据底座 + N 个应用生态"。

## 项目定位

- **底座（真实实现）**：多家医院联邦学习协作（数据不出院）→ 差分隐私（形式化 ε/δ 隐私预算）→ 审计存证链（RFC 3161 外部锚定）→ 数据产品流通 → 监管合规
- **应用生态**：泛癌卫士（基于公开发表的 Oncoformer 泛癌模型，Cell 2026）、影像卫士（医师在环）、脑电卫士、档案管家、政策参谋、权益管家等 9 个医疗智能体，作为数据产品的消费方与民生价值出口

## 核心模块

```
backend/
├── app/services/federated/    # ⭐ 联邦学习引擎（自研，纯 CPU）
│   ├── data_generator.py      #   3 家异构模拟医院合成 EHR（阳性率 ~22%，贴近流行病学）
│   └── engine.py              #   FedAvg + 差分隐私（DP-FedAvg）+ 联邦统计
├── app/services/privacy_accountant.py  # RDP 矩会计，输出形式化 (ε, δ) 隐私预算报告
├── app/routers/federation.py  #   联邦任务 API + 审计存证链（sha256 串联）
├── app/services/chain_anchor.py        # 双链链尖合并 + RFC 3161 可信时间戳外部锚定
├── backend/node_agent/        #   医院侧节点 Agent（Docker 单容器 + mTLS + 参数加密上行）
├── app/services/orchestrator.py        # 多智能体编排（9 个医疗 Agent）
└── ...                        #   影像/脑电/档案/政策/报销等业务域
frontend/src/app/federation/   # ⭐ 联邦协作网络看板（核心演示页）
```

## 技术亮点（均可现场验证）

| 能力 | 验证方式 |
|---|---|
| 联邦学习追平集中训练 | `GET /api/federation/benchmark`，固定种子可复现 |
| 差分隐私预算可核算 | 任务 `result.privacy` 输出现形式化 (ε, δ) 报告 |
| 存证链不可篡改 | 管理端查询链尖与 RFC 3161 时间戳令牌 |
| 医院侧零原始数据出域 | Node Agent 演练记录（`docs/联邦节点演练记录.md`） |
| 恶意参数可拦截 | 余弦相似度检测，422 拒绝且不落库 |
| 多租户隔离 | 医院级租户，跨租户访问 403 / 非本院任务 404 |

## 实验基准（种子固定可复现）

| 方案 | 全局测试 AUC |
|------|-------------|
| 三甲医院本地模型 | 0.7013 |
| 区级医院本地模型 | 0.6994 |
| 社区卫生中心本地模型 | 0.6896 |
| **联邦学习 FedAvg** | **0.7018** |
| 联邦 + 轻噪声差分隐私（σ=0.01） | 0.6922 |
| 集中训练上界（现实不可行） | 0.7012 |

- 联邦模型**追平集中训练上界**：数据不出院即获得大池化效果
- 逐院公平性：三家医院全部获益（A +0.003 / B +0.000 / C +0.012）
- 数据阳性率 21.8%~25.1%，贴近真实心衰 30 天再入院流行病学
- DP 提供"隐私—效用"分档权衡：轻噪声档仅损失约 0.01 AUC
- UCI Cleveland 真实患者非 IID 复验：FedAvg AUC 0.9091，高于集中训练上界 0.9019

> 以上数据由 `backend/app/services/federated/` 内的合成/公开数据集生成，全部为技术验证口径，不含任何真实患者数据。

## 快速启动（本地轻量模式，无 Docker 依赖）

```bash
# 后端（默认 8000；若端口被占用可改 8100）
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
DEMO_OFFLINE=true uvicorn app.main:app --port 8000

# 前端
cd frontend
pnpm install
# 新建 .env.local，写入：NEXT_PUBLIC_API_URL=http://localhost:8000
pnpm dev
```

## Docker 一键部署（生产形态）

```bash
docker compose --profile prod up -d --build
# postgres + redis + chromadb + 后端(8000) + 前端(3000)
# 监控：docker compose --profile monitoring up -d（Prometheus 9090 / Grafana 3001）
```

## 合规与知识产权

- **软件著作权 3 件**：平台、病历智能治理系统、联邦学习协作引擎（个人名义申请，登记文本见 `docs/软著申请/`）
- **发明专利 1 件**：申请中
- **数据分类分级**：GB/T 39725-2020 × GB/T 43697-2024 双框架，字段级台账覆盖 25 张表，CI 强制校验
- **个人信息保护影响评估（PIA）**：已出具报告，待外部律师双审
- **等保三级（代码侧）**：审计留存 180 天归档、敏感字段 AES-256-GCM 加密、登录失败指数退避锁定、TLS 1.3 反代模板
- **测试**：625 项自动化测试全绿

## 参赛与文档

完整索引见 [`docs/hicool/README.md`](docs/hicool/README.md)。

| 文档 | 内容 |
|---|---|
| `docs/hicool/00-参赛策略.md` | 赛道选择、评委逻辑、竞争分析 |
| `docs/hicool/01-资格自查表.md` | 参赛资格逐条自查与股权方案 |
| `docs/hicool/02-BP-HICOOL版.md` | 商业计划书（含市场规模测算与融资计划） |
| `docs/hicool/03-北京落地规划书.md` | 北京经开区落地路径 |
| `docs/hicool/04-知识产权与尽调材料包.md` | 知识产权清单、职务发明处置、尽调材料 |
| `docs/hicool/05-路演脚本7分钟.md` | 赛区赛路演稿与时间控制卡 |
| `docs/hicool/06-路演脚本10分钟.md` | 复赛决赛路演稿与现场演示环节 |
| `docs/hicool/07-答辩QA预案.md` | 12 个必答题 + 6 个陷阱题 |
| `docs/hicool/08-一页纸.md` | 评委速览单页 |
| `docs/hicool/09-报名表填写草稿.md` | 报名字段记录 |

> 项目演进：本平台早期版本曾参加其他区域性创新创业赛事并完成第三方评审验证；HICOOL 为本项目当前主攻赛事。相关历史材料保留在 `docs/` 内以备尽调追溯。

## 目录说明

- `docs/`：商业计划、合规制度、软著材料、演练记录（历史材料原样保留）
- `scripts/`：数据生成、软著材料构建、演示视频与图表生成工具
- `deploy/`：魔搭创空间、TLS/mTLS、Prometheus/Grafana 部署配置
