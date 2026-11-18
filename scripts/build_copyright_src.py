"""软著源代码文档生成器（中国版权保护中心格式）

规则：
- 每页 50 行；程序量不足 60 页全量提交，超过则提交前 30 页 + 后 30 页；
- 页眉含软件名称 + 版本号；
- 剔除空行与纯注释行，提高代码密度。

三件软件的代码范围**互斥**，避免被审查员认定为同一软件拆分申请：
- 件一（平台）：框架层 + 交易/管理/安全/档案等路由与服务；
              **排除**联邦学习与病历治理相关文件。
- 件二（病历治理）：治理引擎、结构化评估、OCR、知识库、LLM 封装 + 治理路由与页面。
- 件三（联邦引擎）：联邦引擎、隐私会计、协调器、节点路由与服务、医院侧 Node Agent
              + 联邦页面。

运行：python scripts/build_copyright_src.py
输出：docs/软著申请/<软件名>V1.0-源代码.txt（三份）
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND_SRC = ROOT / "frontend" / "src"
OUT_DIR = ROOT / "docs" / "软著申请"
LINES_PER_PAGE = 50
PAGES = 30  # 前 30 页 + 后 30 页

# 件二 / 件三的专属文件关键词（路径包含即归属）
GOVERNANCE_KEYS = [
    "governance", "structure_eval", "ocr_service", "knowledge_base", "llm_service",
]
FEDERATION_KEYS = [
    "federated", "federation", "privacy_accountant", "node_agent",
]

TITLE_REGISTER = [
    {
        "file": "1-医数可信医疗数据要素可信流通平台V1.0-源代码.txt",
        "name": "医数可信医疗数据要素可信流通平台",
        "version": "V1.0",
        "roots": [BACKEND / "app", FRONTEND_SRC / "app", FRONTEND_SRC / "lib"],
        "globs": ["*.py", "page.tsx", "api.ts"],
        # 件一为平台主干，排除子系统与测试代码
        "exclude_contains": GOVERNANCE_KEYS + FEDERATION_KEYS + [
            "/tests/", "test_", "/scripts/", "__pycache__",
        ],
    },
    {
        "file": "2-医数可信病历智能治理系统V1.0-源代码.txt",
        "name": "医数可信病历智能治理系统",
        "version": "V1.0",
        "roots": [BACKEND / "app", FRONTEND_SRC / "app" / "governance"],
        "globs": ["*.py", "page.tsx"],
        "include_contains": GOVERNANCE_KEYS,
    },
    {
        "file": "3-医数可信联邦学习医疗协作引擎V1.0-源代码.txt",
        "name": "医数可信联邦学习医疗协作引擎",
        "version": "V1.0",
        "roots": [BACKEND / "app", BACKEND / "node_agent", FRONTEND_SRC / "app" / "federation"],
        "globs": ["*.py", "page.tsx"],
        "skip_roots": [BACKEND / "node_agent" / "node_agent" / "__init__.py"],
        "include_contains": FEDERATION_KEYS,
    },
]

# node_agent 目录下源码需要单独纳入件三（路径不含 app/）
EXTRA_FILES = {
    3: [
        BACKEND / "node_agent" / "node_agent" / "tls.py",
        BACKEND / "node_agent" / "node_agent" / "trainer.py",
        BACKEND / "node_agent" / "node_agent" / "synthdata.py",
        BACKEND / "node_agent" / "node_agent" / "__init__.py",
    ],
}


def collect_files(item, index):
    files = []
    for root in item["roots"]:
        if root.is_file():
            files.append(root)
            continue
        if not root.exists():
            continue
        for g in item["globs"]:
            files.extend(root.rglob(g))

    files.extend(EXTRA_FILES.get(index, []))

    seen, out = set(), []
    for f in files:
        if not f.is_file():
            continue
        rp = str(f.resolve())
        if rp in seen or f.name.startswith("__init__"):
            continue
        if any(x in rp for x in item.get("exclude_contains", [])):
            continue
        inc = item.get("include_contains")
        if inc and not any(k in rp for k in inc):
            continue
        seen.add(rp)
        out.append(f)
    return sorted(out, key=lambda p: str(p))


def code_lines(files):
    lines = []
    for f in files:
        try:
            raw = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for ln in raw:
            t = ln.rstrip()
            if not t.strip():
                continue
            stripped = t.strip()
            # 剔除极短的占位注释，保留有信息量的注释
            if stripped.startswith("#") and len(stripped) < 6:
                continue
            lines.append(t)
        lines.append("")  # 文件间空行分隔
    return lines[:6000] if len(lines) > 6000 else lines


def paginate(lines, soft_name, version):
    need = LINES_PER_PAGE * PAGES * 2
    if len(lines) <= need:
        selected = lines
    else:
        # 超过 60 页：取前 30 页 + 后 30 页，正好 60 页（不插入额外说明行）
        selected = lines[: LINES_PER_PAGE * PAGES] + lines[-LINES_PER_PAGE * PAGES:]

    out = []
    page = 1
    for i in range(0, len(selected), LINES_PER_PAGE):
        chunk = selected[i : i + LINES_PER_PAGE]
        out.append(f"第{page}页")
        out.append(f"{soft_name} {version}")
        out.extend(chunk)
        out.append("")
        page += 1
    return "\n".join(out), page - 1


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(TITLE_REGISTER, start=1):
        files = collect_files(item, index)
        lines = code_lines(files)
        content, pages = paginate(lines, item["name"], item["version"])
        out = OUT_DIR / item["file"]
        out.write_text(f"{item['name']} {item['version']}\n\n{content}", encoding="utf-8")
        print(f"✓ {item['file']}")
        print(f"    {pages} 页 | {len(lines)} 行 | {len(files)} 个文件")


if __name__ == "__main__":
    main()
