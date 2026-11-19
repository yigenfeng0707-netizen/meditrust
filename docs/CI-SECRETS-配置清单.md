# CI Secrets 配置清单

> 仓库：`yigenfeng0707-netizen/meditrust`
> 核对时间：2026-11-18
> 核对方式：`gh secret list` / `gh variable list` + 本机令牌可用性探测 + 魔搭 OpenAPI 读键名

## 一、当前状态

| 类型 | 名称 | 状态 | 本机来源 |
|---|---|---|---|
| Secret | `MODELSCOPE_DEMO_URL` | ✅ 已配置 | 创空间公开地址 |
| Secret | `MODELSCOPE_USERNAME` | ✅ 已配置 | 本机令牌文件标注的账号 `gsym236998` |
| Secret | `MODELSCOPE_TOKEN` | ✅ 已配置 | `~/Desktop/根/api/魔搭访问token.txt`（两个令牌均能访问创空间 OpenAPI，取其一） |
| Secret | `LLM_API_KEY` | ✅ 已配置 | `~/Desktop/根/api/aipingtoken.txt`，已实测 `GET /v1/models` 返回 200 |
| Secret | `VISION_API_KEY` | ✅ 已配置 | 同上（主力与视觉共用 aiping 网关） |
| Secret | `DASHSCOPE_API_KEY` | ✅ 已配置 | `~/Desktop/根/api/51APIkey.txt`，在 `51kik.com/v1` 实测 200 |
| Secret | `YIBAO_SESSION_SECRET` | ✅ 已配置 | `deploy/modelscope/ms_deploy.json` 中线上正在使用的值，原样回填 |
| Secret | `ADMIN_PASSWORD` | ⚠️ 未配置 | 本机无本项目专用值；线上 secrets 已存在该键，不覆盖 |
| Secret | `YIBAO_ADMIN_SECRET` | ⚠️ 未配置 | 同上；覆盖会导致已签发管理员 token 全部失效 |
| Secret | `ALIPAY_APP_PRIVATE_KEY` | ⚠️ 未配置 | 本机仅有其他应用密钥（APPID `2021006171661005`），与线上 `2021006195651204` 不一致 |
| Secret | `ALIPAY_PUBLIC_KEY` | ⚠️ 未配置 | 同上，不能混用 |
| Variable | `MODELSCOPE_SPACE_NAME` | ✅ 配置为 `oumed-chain-demo` | 经魔搭 OpenAPI 验证；注意不是 `gsym236998-oumed-chain-demo` |

## 二、影响范围

| Workflow | 当前表现 |
|---|---|
| `keepalive.yml` | 正常，保活地址已配置 |
| `deploy-modelscope.yml` | Push、Sync secrets、Trigger build 阶段的必需项已齐备；4 项缺失密钥会被 workflow 条件跳过，线上原值保持不变，不会导致部署失败 |
| `modelscope-logs.yml` | 正常 |

## 三、配置方式

后续如需补齐剩余项，在仓库根目录执行（从标准输入读取，避免写入 shell 历史）：

```bash
cd "/Users/chenlinlian/Desktop/根/Hicool创业赛/oumed-chain"
gh secret set ADMIN_PASSWORD
gh secret set YIBAO_ADMIN_SECRET
gh secret set ALIPAY_APP_PRIVATE_KEY
gh secret set ALIPAY_PUBLIC_KEY
```

## 四、取值来源与注意事项

1. **魔搭空间名**：正确值是 `oumed-chain-demo`。此前按公开地址前缀推测的 `gsym236998-oumed-chain-demo` 会返回 404，已纠正。
2. **LLM / VISION**：线上 variables 中 `LLM_BASE_URL` 与 `VISION_BASE_URL` 均为 `https://aiping.cn/api/v1`，因此两个 secret 都回填 aiping 网关 key；该 key 已实测可用。
3. **DASHSCOPE**：本机 key 在 `51kik.com` 可用，但线上 variables 中 `DASHSCOPE_BASE_URL` 仍为 `https://api.openai-next.com/v1`（探测返回 Cloudflare 1010）。它只是三级降级链路的备用项，主力 aiping 可用时不影响主流程；若要让备用链路真正可用，需同步修改线上 `DASHSCOPE_BASE_URL`，本次未改动。
4. **YIBAO_SESSION_SECRET**：直接取自仓库中 `ms_deploy.json` 的线上值，保证与已部署容器一致。
5. **ADMIN_PASSWORD / YIBAO_ADMIN_SECRET**：魔搭 OpenAPI 只返回键名、不返回值（`value` 为空），本机也没有本项目专用值。workflow 对这两项做了非空判断，缺失即跳过同步，因此保持线上现状是最安全的选择；不要随意生成新值覆盖。
6. **支付宝密钥**：本机 `~/Desktop/根/zhifubaobisai/.prod-keys/` 下的密钥属于 APPID `2021006171661005`（研报侠项目），与本项目线上 `2021006195651204` 不是同一应用，混用会导致验签失败。若确需启用本项目 live 支付，请从对应支付宝应用控制台导出私钥与支付宝公钥后再配置。

## 五、安全说明

- 密钥只写入 GitHub Actions Secrets，不进入 git 历史；`ms_deploy.json` 仅保留占位符或线上既有值。
- 配置完成后只核对名称，不打印值。
- 本次尚未手动触发部署工作流，因此未做端到端部署验证；如需验证，可在 GitHub Actions 中手动运行 `deploy-modelscope.yml`。
