#!/usr/bin/env python3
"""
对 jsonl 执行完整 web2json 流水线：
1. 拆分 html + manifest
2. classify_html_dir
3. 对每个 cluster 执行 extract_schema
4. infer_code
5. extract_data_with_code
6. 汇总 token 使用
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from web2json import (
    Web2JsonConfig,
    classify_html_dir,
    extract_schema,
    infer_code,
    extract_data_with_code,
)
from web2json.utils.llm_client import LLMClient
from web2json.utils.llm_retry import get_retry_stats, reset_retry_stats


@dataclass
class PipelineRunResult:
    source_jsonl: str
    manifest: str
    html_dir: str
    pipeline_root: str
    cluster_count: int
    clusters: list[dict[str, Any]]
    total_token_usage: dict[str, int]
    summary_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run web2json pipeline on a crawl jsonl.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--source-jsonl", help="单个源 jsonl 文件路径。")
    src.add_argument(
        "--source-dir",
        help="目录下所有 *.jsonl 依次全量跑流水线（与 --source-jsonl 二选一）。",
    )
    parser.add_argument(
        "--work-id",
        default="",
        help="输出目录标识。默认根据 jsonl 文件名自动生成。",
    )
    parser.add_argument(
        "--input-root",
        default="input_html",
        help="HTML 输出根目录，默认 input_html。",
    )
    parser.add_argument(
        "--output-root",
        default="output",
        help="结果输出根目录，默认 output。",
    )
    parser.add_argument(
        "--html-key",
        default="html",
        help="jsonl 中 HTML 字段名，默认 html。",
    )
    parser.add_argument(
        "--iteration-rounds",
        type=int,
        default=3,
        help="schema 学习轮数上限，默认 3。",
    )
    parser.add_argument(
        "--cluster-limit",
        type=int,
        default=0,
        help="最多处理多少个 cluster，0 表示全部处理。",
    )
    parser.add_argument(
        "--fields",
        default="",
        help='预定义要抽取的字段，逗号分隔，类型均为 string，如 "title,content"。为空则走 auto schema。',
    )
    parser.add_argument(
        "--max-jsonl-files",
        type=int,
        default=0,
        help="与 --source-dir 联用：最多处理前 N 个 jsonl（按文件名排序），0 表示不限制。",
    )
    parser.add_argument(
        "--schema-json",
        default="",
        help="Predefined schema JSON 文件路径（与 README Predefined Mode 一致），优先级高于 --fields。",
    )
    parser.add_argument(
        "--skip-manifest",
        action="store_true",
        help="不重新从 jsonl 拆 HTML/manifest（需已存在 input_root/work_id/）。",
    )
    parser.add_argument(
        "--skip-classify",
        action="store_true",
        help="不重新聚类，直接复用 pipeline_root/classify/clusters/（补跑失败簇时用）。",
    )
    parser.add_argument(
        "--only-clusters",
        default="",
        help='只处理指定簇，逗号分隔，如 "cluster_4,cluster_5"。为空表示全部簇。',
    )
    parser.add_argument(
        "--merge-summary",
        action="store_true",
        help="写回 pipeline_summary.json 时与已有 summary 按 cluster_name 合并（补跑时用）。",
    )
    parser.add_argument(
        "--only-failed",
        action="store_true",
        help="仅补跑「HTML 数量 > result 下 JSON 数量」的簇（需已有 classify/extract 目录；可与 --only-clusters 叠加）。",
    )
    return parser.parse_args()


def load_schema_json(path: str) -> Optional[dict[str, Any]]:
    if not path or not path.strip():
        return None
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    if not p.is_file():
        raise SystemExit(f"--schema-json not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("--schema-json root must be a JSON object")
    return data


def fields_to_schema(fields_csv: str) -> Optional[dict[str, str]]:
    if not fields_csv or not fields_csv.strip():
        return None
    out: dict[str, str] = {}
    for part in fields_csv.split(","):
        name = part.strip()
        if name:
            out[name] = "string"
    return out or None


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return value or "run"


def build_html_manifest(source_jsonl: Path, output_dir: Path, html_key: str) -> Path:
    """逐行流式读取 jsonl，避免大文件一次性载入内存。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.jsonl"
    idx = 0

    with source_jsonl.open("r", encoding="utf-8") as src_fp, manifest_path.open(
        "w", encoding="utf-8"
    ) as manifest_fp:
        for line_no, line in enumerate(src_fp, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"skip invalid json line {line_no}: {exc}")
                continue
            html = row.get(html_key)
            if not isinstance(html, str) or not html.strip():
                continue
            idx += 1
            filename = f"{idx:04d}.html"
            (output_dir / filename).write_text(html, encoding="utf-8")

            manifest_row = {
                "sample_no": idx,
                "source_line": line_no,
                "filename": filename,
                "track_id": row.get("track_id"),
                "url": row.get("url"),
                "status": row.get("status"),
                "html_len": len(html),
            }
            manifest_fp.write(json.dumps(manifest_row, ensure_ascii=False) + "\n")

    return manifest_path


def usage_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    return {
        "total_input_tokens": after["total_input_tokens"] - before["total_input_tokens"],
        "total_completion_tokens": after["total_completion_tokens"] - before["total_completion_tokens"],
        "total_tokens": after["total_tokens"] - before["total_tokens"],
    }


def _synthetic_clusters_from_completed_extract(
    pipeline_root: Path, current_names: set[str]
) -> list[dict[str, Any]]:
    """无 pipeline_summary.json 时，从已有 cluster_*_extract_data/result 推断已完成的簇。"""
    out: list[dict[str, Any]] = []
    for ed in sorted(pipeline_root.glob("cluster_*_extract_data")):
        cname = ed.name[: -len("_extract_data")]
        if cname in current_names:
            continue
        rd = ed / "result"
        if not rd.is_dir():
            continue
        njson = len(list(rd.glob("*.json")))
        if njson == 0:
            continue
        out.append(
            {
                "cluster_name": cname,
                "cluster_size": njson,
                "data_output": str(ed),
                "note": "from_disk_merge (补跑合并时从结果目录推断)",
            }
        )
    return out


def _discover_clusters_from_disk(clusters_dir: Path) -> list[str]:
    if not clusters_dir.is_dir():
        return []
    names = sorted(
        p.name
        for p in clusters_dir.iterdir()
        if p.is_dir() and p.name.startswith("cluster_")
    )
    return names


def _underextracted_cluster_names(pipeline_root: Path, clusters_dir: Path) -> list[str]:
    """classify 中 HTML 数量大于对应 extract_data/result 中 JSON 数量的簇。"""
    failed: list[str] = []
    if not clusters_dir.is_dir():
        return failed
    for cluster_dir in sorted(clusters_dir.iterdir()):
        if not cluster_dir.is_dir() or not cluster_dir.name.startswith("cluster_"):
            continue
        cname = cluster_dir.name
        n_html = len(list(cluster_dir.glob("*.html"))) + len(list(cluster_dir.glob("*.htm")))
        rd = pipeline_root / f"{cname}_extract_data" / "result"
        n_json = len(list(rd.glob("*.json"))) if rd.is_dir() else 0
        if n_html > n_json:
            failed.append(cname)
    return failed


def run_jsonl_pipeline(
    source_jsonl: str,
    work_id: str = "",
    input_root: str = "input_html",
    output_root: str = "output",
    html_key: str = "html",
    iteration_rounds: int = 3,
    cluster_limit: int = 0,
    schema: Optional[dict[str, Any]] = None,
    skip_manifest: bool = False,
    skip_classify: bool = False,
    only_clusters: Optional[list[str]] = None,
    merge_summary: bool = False,
    only_failed: bool = False,
) -> PipelineRunResult:
    source_jsonl_path = Path(source_jsonl).expanduser()
    if not source_jsonl_path.is_absolute():
        source_jsonl_path = (PROJECT_ROOT / source_jsonl_path).resolve()

    work_id = work_id or slugify(source_jsonl_path.stem)

    input_root_path = Path(input_root).expanduser()
    if not input_root_path.is_absolute():
        input_root_path = (PROJECT_ROOT / input_root_path).resolve()

    output_root_path = Path(output_root).expanduser()
    if not output_root_path.is_absolute():
        output_root_path = (PROJECT_ROOT / output_root_path).resolve()

    html_dir = input_root_path / work_id
    pipeline_root = output_root_path / f"{work_id}_pipeline"
    pipeline_root.mkdir(parents=True, exist_ok=True)

    print(f"source_jsonl: {source_jsonl_path}")
    print(f"work_id: {work_id}")
    print(f"html_dir: {html_dir}")
    print(f"pipeline_root: {pipeline_root}")
    if schema:
        print(f"predefined schema fields: {list(schema.keys())}")

    manifest_path = html_dir / "manifest.jsonl"
    if skip_manifest:
        if not manifest_path.is_file():
            raise SystemExit(f"--skip-manifest requires existing {manifest_path}")
        print(f"manifest (reuse): {manifest_path}")
    else:
        manifest_path = build_html_manifest(source_jsonl_path, html_dir, html_key)
        print(f"manifest: {manifest_path}")

    clusters_dir = pipeline_root / "classify" / "clusters"
    classify_result = None

    if skip_classify:
        cluster_names = _discover_clusters_from_disk(clusters_dir)
        if not cluster_names:
            raise SystemExit(f"--skip-classify requires non-empty {clusters_dir}")
        print(f"classify (reuse): {len(cluster_names)} clusters under {clusters_dir}")
    else:
        classify_config = Web2JsonConfig(
            name="classify",
            html_path=str(html_dir),
            output_path=str(pipeline_root),
            save=["report", "files"],
        )
        classify_result = classify_html_dir(classify_config)
        cluster_names = sorted(classify_result.clusters.keys())

    if only_clusters:
        want = {x.strip() for x in only_clusters if x.strip()}
        cluster_names = [c for c in cluster_names if c in want]
        missing = want - set(cluster_names)
        if missing:
            raise SystemExit(f"--only-clusters not found on disk: {sorted(missing)}")
        if not cluster_names:
            raise SystemExit("--only-clusters filtered out all clusters")

    if only_failed:
        under = _underextracted_cluster_names(pipeline_root, clusters_dir)
        under_set = set(under)
        cluster_names = [c for c in cluster_names if c in under_set]
        print(f"only-failed: 未跑满簇 {under} → 本次处理 {cluster_names}")
        if not cluster_names:
            print("当前没有需要补跑的 cluster（各簇 JSON 数量已不少于 HTML）。")
            raise SystemExit(0)

    if cluster_limit:
        cluster_names = cluster_names[:cluster_limit]

    LLMClient.reset_usage()
    reset_retry_stats()
    cluster_summaries: list[dict[str, Any]] = []

    for cluster_name in cluster_names:
        cluster_html_dir = clusters_dir / cluster_name
        if classify_result is not None:
            cluster_files = classify_result.clusters[cluster_name]
            cluster_size = len(cluster_files)
        else:
            cluster_files = sorted(cluster_html_dir.glob("*.html")) + sorted(
                cluster_html_dir.glob("*.htm")
            )
            cluster_size = len(cluster_files)
        rounds = min(iteration_rounds, cluster_size)

        print(f"\n=== {cluster_name} ({cluster_size} files) ===")
        cluster_t0 = time.perf_counter()

        before_schema = LLMClient.get_total_usage()
        schema_result = extract_schema(
            Web2JsonConfig(
                name=f"{cluster_name}_schema",
                html_path=str(cluster_html_dir),
                output_path=str(pipeline_root),
                iteration_rounds=rounds,
                save=["schema"],
                schema=schema,
            )
        )
        after_schema = LLMClient.get_total_usage()

        before_code = LLMClient.get_total_usage()
        code_result = infer_code(
            Web2JsonConfig(
                name=f"{cluster_name}_code",
                html_path=str(cluster_html_dir),
                output_path=str(pipeline_root),
                schema=schema_result.final_schema,
                save=["schema", "code"],
                iteration_rounds=rounds,
            )
        )
        after_code = LLMClient.get_total_usage()

        parser_path = pipeline_root / f"{cluster_name}_code" / "final_parser.py"
        parse_result = extract_data_with_code(
            Web2JsonConfig(
                name=f"{cluster_name}_extract_data",
                html_path=str(cluster_html_dir),
                output_path=str(pipeline_root),
                parser_code=str(parser_path),
                save=["data"],
            )
        )

        cluster_summary = {
            "cluster_name": cluster_name,
            "cluster_size": cluster_size,
            "elapsed_seconds": round(time.perf_counter() - cluster_t0, 3),
            "html_dir": str(cluster_html_dir),
            "schema_output": str(pipeline_root / f"{cluster_name}_schema"),
            "code_output": str(pipeline_root / f"{cluster_name}_code"),
            "data_output": str(pipeline_root / f"{cluster_name}_extract_data"),
            "parser_path": str(parser_path),
            "schema_fields": list(schema_result.final_schema.keys()),
            "schema_token_usage": usage_delta(before_schema, after_schema),
            "code_token_usage": usage_delta(before_code, after_code),
            "parse_success_count": parse_result.success_count,
            "parse_failed_count": parse_result.failed_count,
        }
        cluster_summaries.append(cluster_summary)

    total_usage = LLMClient.get_total_usage()
    summary_path = pipeline_root / "pipeline_summary.json"
    run_elapsed = sum(c.get("elapsed_seconds", 0) for c in cluster_summaries if isinstance(c, dict))
    cluster_count_total = len(_discover_clusters_from_disk(clusters_dir)) if clusters_dir.is_dir() else len(cluster_names)

    summary: dict[str, Any] = {
        "source_jsonl": str(source_jsonl_path),
        "manifest": str(manifest_path),
        "html_dir": str(html_dir),
        "pipeline_root": str(pipeline_root),
        "cluster_count": cluster_count_total,
        "clusters": cluster_summaries,
        "total_token_usage": total_usage,
        "pipeline_elapsed_seconds": round(run_elapsed, 3),
        "llm_retry_stats": get_retry_stats(),
    }

    if merge_summary:
        current_names = {c["cluster_name"] for c in cluster_summaries}
        by_name: dict[str, Any] = {}
        if summary_path.is_file():
            try:
                prev = json.loads(summary_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                prev = {}
            prev_clusters = prev.get("clusters") or []
            if isinstance(prev_clusters, list):
                by_name = {
                    c.get("cluster_name"): c
                    for c in prev_clusters
                    if isinstance(c, dict) and c.get("cluster_name")
                }
        else:
            for c in _synthetic_clusters_from_completed_extract(pipeline_root, current_names):
                by_name[c["cluster_name"]] = c
        for c in cluster_summaries:
            by_name[c["cluster_name"]] = c
        if by_name:
            summary["clusters"] = [by_name[k] for k in sorted(by_name.keys())]
            summary["cluster_count"] = len(
                _discover_clusters_from_disk(clusters_dir)
            ) or len(summary["clusters"])
        # total_token_usage 仅为本次运行累计（补跑时不会与历史相加，避免重复计算）

    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsummary: {summary_path}")
    print(json.dumps(total_usage, ensure_ascii=False, indent=2))
    print(json.dumps(get_retry_stats(), ensure_ascii=False, indent=2))

    return PipelineRunResult(
        source_jsonl=summary["source_jsonl"],
        manifest=summary["manifest"],
        html_dir=summary["html_dir"],
        pipeline_root=summary["pipeline_root"],
        cluster_count=summary["cluster_count"],
        clusters=summary["clusters"],
        total_token_usage=summary["total_token_usage"],
        summary_path=str(summary_path),
    )


def main() -> None:
    args = parse_args()
    schema: Optional[dict[str, Any]] = None
    if args.schema_json:
        schema = load_schema_json(args.schema_json)
    else:
        schema = fields_to_schema(args.fields)

    only = None
    if args.only_clusters.strip():
        only = [x.strip() for x in args.only_clusters.split(",") if x.strip()]

    if args.skip_classify and not args.skip_manifest:
        print("提示: --skip-classify 通常与 --skip-manifest 一起用，避免重复从大 jsonl 拆 HTML。")

    extra_kw = dict(
        skip_manifest=args.skip_manifest,
        skip_classify=args.skip_classify,
        only_clusters=only,
        merge_summary=args.merge_summary,
        only_failed=args.only_failed,
    )

    if args.source_dir:
        dir_path = Path(args.source_dir).expanduser()
        if not dir_path.is_absolute():
            dir_path = (PROJECT_ROOT / dir_path).resolve()
        jsonl_files = sorted(dir_path.glob("*.jsonl"))
        if args.max_jsonl_files:
            jsonl_files = jsonl_files[: args.max_jsonl_files]
        if not jsonl_files:
            raise SystemExit(f"no *.jsonl under {dir_path}")
        print(f"batch mode: {len(jsonl_files)} file(s) under {dir_path}")
        for i, jp in enumerate(jsonl_files, 1):
            print(f"\n{'='*60}\n[{i}/{len(jsonl_files)}] {jp.name}\n{'='*60}")
            run_jsonl_pipeline(
                source_jsonl=str(jp),
                work_id="",
                input_root=args.input_root,
                output_root=args.output_root,
                html_key=args.html_key,
                iteration_rounds=args.iteration_rounds,
                cluster_limit=args.cluster_limit,
                schema=schema,
                **extra_kw,
            )
    else:
        run_jsonl_pipeline(
            source_jsonl=args.source_jsonl,
            work_id=args.work_id,
            input_root=args.input_root,
            output_root=args.output_root,
            html_key=args.html_key,
            iteration_rounds=args.iteration_rounds,
            cluster_limit=args.cluster_limit,
            schema=schema,
            **extra_kw,
        )


if __name__ == "__main__":
    main()
