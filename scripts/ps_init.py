import json, sys
from pathlib import Path
import requests

ROOT = Path.home() / "Desktop" / "ps"

TIER_NAMES = {
    0: "Unrated",
    1: "Bronze V", 2: "Bronze IV", 3: "Bronze III", 4: "Bronze II", 5: "Bronze I",
    6: "Silver V", 7: "Silver IV", 8: "Silver III", 9: "Silver II", 10: "Silver I",
    11: "Gold V", 12: "Gold IV", 13: "Gold III", 14: "Gold II", 15: "Gold I",
    16: "Platinum V", 17: "Platinum IV", 18: "Platinum III", 19: "Platinum II", 20: "Platinum I",
    21: "Diamond V", 22: "Diamond IV", 23: "Diamond III", 24: "Diamond II", 25: "Diamond I",
    26: "Ruby V", 27: "Ruby IV", 28: "Ruby III", 29: "Ruby II", 30: "Ruby I",
}

def solvedac_problem(pid: int):
    url = "https://solved.ac/api/v3/problem/show"
    r = requests.get(url, params={"problemId": pid}, timeout=10)
    r.raise_for_status()
    data = r.json()

    title = data.get("titleKo") or data.get("title") or ""
    level = int(data.get("level") or 0)
    tier_name = TIER_NAMES.get(level, "Unrated")

    tags = []
    for t in data.get("tags", []) or []:
        disp = (t.get("displayNames") or [])
        ko = next((x.get("name") for x in disp if x.get("language") == "ko"), None)
        en = next((x.get("name") for x in disp if x.get("language") == "en"), None)
        tags.append(ko or en or t.get("key") or "")
    tags = [x for x in tags if x]

    return {
        "platform": "boj",
        "id": pid,
        "title": title,
        "tier": level,
        "tier_name": tier_name,
        "tags": tags,
        "url": f"https://www.acmicpc.net/problem/{pid}",
        "solvedac_url": f"https://solved.ac/problem/{pid}",
    }

def ensure_code_file(platform: str, pid: int):
    pdir = ROOT / platform / str(pid)
    pdir.mkdir(parents=True, exist_ok=True)
    f = pdir / ("Solution.java" if platform == "swea" else "Main.java")
    if not f.exists():
        f.write_text("", encoding="utf-8")
    return f

def write_problem_md(meta: dict):
    pdir = ROOT / meta["platform"] / str(meta["id"])
    lines = []
    lines.append(f"# BOJ {meta['id']} - {meta.get('title','')}")
    lines.append("")
    lines.append(f"- 난이도: **{meta.get('tier_name','')}**")
    if meta.get("tags"):
        lines.append(f"- 태그: {', '.join(meta['tags'])}")
    lines.append(f"- 링크: {meta.get('url','')}")
    lines.append(f"- solved.ac: {meta.get('solvedac_url','')}")
    lines.append("")
    lines.append("> 문제 본문은 저장하지 않습니다. (solved.ac 메타 기반 자동화)")
    (pdir / "Problem.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

def write_meta(meta: dict):
    pdir = ROOT / meta["platform"] / str(meta["id"])
    (pdir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def gather_all_meta():
    items = []
    for platform in ["boj", "swea", "codetree"]:
        base = ROOT / platform
        if not base.exists():
            continue
        for d in base.iterdir():
            if not d.is_dir():
                continue
            mj = d / "meta.json"
            if mj.exists():
                try:
                    items.append((platform, d.name, json.loads(mj.read_text(encoding="utf-8"))))
                except Exception:
                    pass
    def key(x):
        platform, sid, _ = x
        try:
            n = int(sid)
        except:
            n = 10**18
        return (platform, n)
    return sorted(items, key=key)

def update_root_readme():
    items = gather_all_meta()
    lines = []
    lines.append("# PS")
    lines.append("")
    lines.append("## Problems")
    lines.append("")
    lines.append("| Platform | ID | Title | Tier | Tags | Links |")
    lines.append("|---|---:|---|---|---|---|")
    for platform, sid, meta in items:
        pid = sid
        title = meta.get("title", "")
        tier = meta.get("tier_name", "")
        tags = ", ".join(meta.get("tags", [])[:6])
        rel_problem = f"{platform}/{pid}/Problem.md"
        rel_code = f"{platform}/{pid}/" + ("Solution.java" if platform == "swea" else "Main.java")
        title_cell = f"[{title or (platform.upper()+' '+pid)}]({rel_code})"
        links = []
        if (ROOT / rel_problem).exists():
            links.append(f"[Problem]({rel_problem})")
        if meta.get("url"):
            links.append(f"[BOJ]({meta['url']})")
        if meta.get("solvedac_url"):
            links.append(f"[solved.ac]({meta['solvedac_url']})")
        lines.append(f"| {platform.upper()} | {pid} | {title_cell} | {tier} | {tags} | {' · '.join(links)} |")
    (ROOT / "README.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

def init_boj(pid: int):
    meta = solvedac_problem(pid)
    ensure_code_file("boj", pid)
    write_problem_md(meta)
    write_meta(meta)
    update_root_readme()
    print(str(ROOT / "boj" / str(pid) / "Main.java"))

def init_other(platform: str, pid: int):
    ensure_code_file(platform, pid)
    meta = {"platform": platform, "id": pid, "title": "", "tier": 0, "tier_name": "", "tags": [], "url": "", "solvedac_url": ""}
    write_meta(meta)
    update_root_readme()
    f = ROOT / platform / str(pid) / ("Solution.java" if platform == "swea" else "Main.java")
    print(str(f))

def main():
    if len(sys.argv) < 3:
        raise SystemExit("usage: ps_init.py <platform:boj|swea|codetree> <id>")
    platform = sys.argv[1].strip().lower()
    pid = int(sys.argv[2])
    if platform == "boj":
        init_boj(pid)
    elif platform in ("swea", "codetree"):
        init_other(platform, pid)
    else:
        raise SystemExit("platform must be boj|swea|codetree")

if __name__ == "__main__":
    main()
