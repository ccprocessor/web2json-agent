#!/usr/bin/env python3
"""
汇总「某目录下全部 jsonl」各自对应流水线目录中的统计：
- LLM token（来自各 pipeline_summary.json 的 total_token_usage）
- 时间（各次 pipeline_elapsed_seconds 之和；为脚本侧计时的簇耗时之和）
- 可选：llm_retry_stats 累计

work_id 规则与 run_jsonl_web2json_pipeline.slugify(jsonl 文件名不含后缀) 一致。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return value or "run"


def pipeline_extract_complete(pipeline_root: Path) -> tuple[bool, str]:
    """各 cluster 下 HTML 数是否与 extract_data/result 中 JSON 数一致。"""
    clusters_dir = pipeline_root / "classify" / "clusters"
    if not clusters_dir.is_dir():
        return False, f"缺少目录: {clusters_dir}"
    for cluster_dir in sorted(clusters_dir.iterdir()):
        if not cluster_dir.is_dir() or not cluster_dir.name.startswith("cluster_"):
            continue
        cname = cluster_dir.name
        n_html = len(list(cluster_dir.glob("*.html"))) + len(list(cluster_dir.glob("*.htm")))
        rd = pipeline_root / f"{cname}_extract_data" / "result"
        n_json = len(list(rd.glob("*.json"))) if rd.is_dir() else 0
        if n_html != n_json:
            return False, f"{cname}: html={n_html} json={n_json}"
    return True, ""


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="汇总某目录下所有 jsonl 对应 pipeline 的 token / 时间 / retry。"
    )
    parser.add_argument(
        "site_dir",
        nargs="?",
        default="Prod/ms-web-jwn",
        help="包含 *.jsonl 的目录（相对项目根或绝对路径），默认 Prod/ms-web-jwn",
    )
    parser.add_argument(
        "--output-root",
        default="output",
        help="流水线输出根目录，默认 output",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="除存在 pipeline_summary 外，还校验各簇 HTML 数与 result JSON 数一致",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="有缺失或未通过 strict 时仍打印汇总且退出码为 0（默认识别到问题则退出 1）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_out",
        help="输出完整 JSON（便于脚本解析）",
    )
    args = parser.parse_args()

    site_dir = Path(args.site_dir).expanduser()
    if not site_dir.is_absolute():
        site_dir = (PROJECT_ROOT / site_dir).resolve()
    if not site_dir.is_dir():
        raise SystemExit(f"目录不存在: {site_dir}")

    output_root = Path(args.output_root).expanduser()
    if not output_root.is_absolute():
        output_root = (PROJECT_ROOT / output_root).resolve()

    jsonl_files = sorted(site_dir.glob("*.jsonl"))
    if not jsonl_files:
        raise SystemExit(f"目录下无 *.jsonl: {site_dir}")

    rows: list[dict[str, Any]] = []
    tot_in = tot_out = tot_tok = 0
    tot_req = 0
    tot_elapsed = 0.0
    tot_retry = 0
    errors: list[str] = []

    for jp in jsonl_files:
        work_id = slugify(jp.stem)
        pr = output_root / f"{work_id}_pipeline"
        sp = pr / "pipeline_summary.json"
        row: dict[str, Any] = {
            "jsonl": jp.name,
            "work_id": work_id,
            "pipeline_root": str(pr),
        }
        if not sp.is_file():
            row["error"] = "missing pipeline_summary.json"
            errors.append(f"{jp.name}: 无 {sp}")
            rows.append(row)
            continue

        try:
            summary = load_summary(sp)
        except json.JSONDecodeError as e:
            row["error"] = f"invalid json: {e}"
            errors.append(f"{jp.name}: {e}")
            rows.append(row)
            continue

        if args.strict:
            ok, msg = pipeline_extract_complete(pr)
            if not ok:
                row["error"] = f"incomplete extract: {msg}"
                errors.append(f"{jp.name}: {msg}")
                rows.append(row)
                continue

        usage = summary.get("total_token_usage") or {}
        if isinstance(usage, dict):
            tot_in += int(usage.get("total_input_tokens", 0) or 0)
            tot_out += int(usage.get("total_completion_tokens", 0) or 0)
            tot_tok += int(usage.get("total_tokens", 0) or 0)
            tot_req += int(usage.get("request_count", 0) or 0)

        elapsed = summary.get("pipeline_elapsed_seconds")
        if elapsed is not None:
            tot_elapsed += float(elapsed)

        retry_stats = summary.get("llm_retry_stats") or {}
        if isinstance(retry_stats, dict):
            tot_retry += int(retry_stats.get("llm_retry_events", 0) or 0)

        row["total_input_tokens"] = usage.get("total_input_tokens", 0) if isinstance(usage, dict) else 0
        row["total_completion_tokens"] = (
            usage.get("total_completion_tokens", 0) if isinstance(usage, dict) else 0
        )
        row["total_tokens"] = usage.get("total_tokens", 0) if isinstance(usage, dict) else 0
        row["request_count"] = usage.get("request_count", 0) if isinstance(usage, dict) else 0
        row["pipeline_elapsed_seconds"] = float(elapsed) if elapsed is not None else None
        row["llm_retry_events"] = retry_stats.get("llm_retry_events", 0) if isinstance(retry_stats, dict) else 0
        rows.append(row)

    aggregate = {
        "site_dir": str(site_dir),
        "output_root": str(output_root),
        "jsonl_count": len(jsonl_files),
        "ok_count": sum(1 for r in rows if "error" not in r),
        "error_count": sum(1 for r in rows if "error" in r),
        "total_token_usage": {
            "request_count": tot_req,
            "total_input_tokens": tot_in,
            "total_completion_tokens": tot_out,
            "total_tokens": tot_tok,
        },
        "pipeline_elapsed_seconds_sum": round(tot_elapsed, 3),
        "llm_retry_events_sum": tot_retry,
        "rows": rows,
    }

    if args.json_out:
        print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    else:
        print(f"目录: {site_dir}")
        print(f"输出根: {output_root}")
        print(f"jsonl 数: {len(jsonl_files)}  成功汇总: {aggregate['ok_count']}  失败/跳过: {aggregate['error_count']}")
        print()
        hdr = f"{'jsonl':<56} {'input':>10} {'output':>10} {'total':>10} {'秒':>10} {'retry':>6}"
        print(hdr)
        print("-" * len(hdr))
        for r in rows:
            if "error" in r:
                print(f"{r['jsonl']:<56}  ERROR: {r['error']}")
            else:
                print(
                    f"{r['jsonl']:<56} "
                    f"{r['total_input_tokens']:>10} "
                    f"{r['total_completion_tokens']:>10} "
                    f"{r['total_tokens']:>10} "
                    f"{r['pipeline_elapsed_seconds'] or 0:>10.3f} "
                    f"{r.get('llm_retry_events', 0):>6}"
                )
        print("-" * len(hdr))
        print(
            f"{'合计':<56} "
            f"{tot_in:>10} "
            f"{tot_out:>10} "
            f"{tot_tok:>10} "
            f"{tot_elapsed:>10.3f} "
            f"{tot_retry:>6}"
        )
        print()
        print(
            "说明: 「秒」为各次 pipeline 的 pipeline_elapsed_seconds 之和（簇耗时相加）；"
            "若某次 summary 无该字段则按 0。"
        )
        if errors:
            print("\n问题:")
            for e in errors:
                print(f"  - {e}")

    if aggregate["error_count"] and not args.allow_partial:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
