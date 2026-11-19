"""pytest 全局夹具：测试环境 = 演示模式 + 离线，并预置会话密钥。

- DEMO_MODE=true：测试套件默认按演示模式运行（与路演/Demo 环境一致）；
  需要生产模式的测试各自 monkeypatch.setattr(settings, "DEMO_MODE", False)。
- DEMO_OFFLINE=true：跳过 ChromaDB 嵌入模型下载与 LLM 外部依赖，
  避免无网络环境挂死（裸跑测试卡在 ONNX 模型下载的根因）。
- YIBAO_SESSION_SECRET：为生产模式（DEMO_MODE=false）的 token 签发/校验
  预置测试密钥，strict 模式测试无需逐个配置。
- CHAIN_ANCHOR_INTERVAL_HOURS=0：关闭定时锚定调度，避免 TestClient
  触发 lifespan 时向真实 TSA（freetsa.org）发起网络请求。
"""

import os

os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("DEMO_OFFLINE", "true")
os.environ.setdefault("YIBAO_SESSION_SECRET", "unit-test-session-secret")
os.environ.setdefault("CHAIN_ANCHOR_INTERVAL_HOURS", "0")
