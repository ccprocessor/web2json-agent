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
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

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
    parser.add_argument("--source-jsonl", required=True, help="源 jsonl 文件路径。")
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
    return parser.parse_args()


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return value or "run"


def load_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as fp:
        for line_no, line in enumerate(fp, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append((line_no, json.loads(line)))
            except json.JSONDecodeError as exc:
                print(f"skip invalid json line {line_no}: {exc}")
    return rows


def build_html_manifest(source_jsonl: Path, output_dir: Path, html_key: str) -> Path:
    rows = load_jsonl(source_jsonl)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.jsonl"

    with manifest_path.open("w", encoding="utf-8") as manifest_fp:
        for idx, (source_line, row) in enumerate(rows, start=1):
            html = row.get(html_key)
            if not isinstance(html, str) or not html.strip():
                continue

            filename = f"{idx:04d}.html"
            (output_dir / filename).write_text(html, encoding="utf-8")

            manifest_row = {
                "sample_no": idx,
                "source_line": source_line,
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


def run_jsonl_pipeline(
    source_jsonl: str,
    work_id: str = "",
    input_root: str = "input_html",
    output_root: str = "output",
    html_key: str = "html",
    iteration_rounds: int = 3,
    cluster_limit: int = 0,
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

    manifest_path = build_html_manifest(source_jsonl_path, html_dir, html_key)
    print(f"manifest: {manifest_path}")

    classify_config = Web2JsonConfig(
        name="classify",
        html_path=str(html_dir),
        output_path=str(pipeline_root),
        save=["report", "files"],
    )
    classify_result = classify_html_dir(classify_config)

    clusters_dir = pipeline_root / "classify" / "clusters"
    cluster_names = sorted(classify_result.clusters.keys())
    if cluster_limit:
        cluster_names = cluster_names[:cluster_limit]

    LLMClient.reset_usage()
    cluster_summaries: list[dict[str, Any]] = []

    for cluster_name in cluster_names:
        cluster_html_dir = clusters_dir / cluster_name
        cluster_files = classify_result.clusters[cluster_name]
        cluster_size = len(cluster_files)
        rounds = min(iteration_rounds, cluster_size)

        print(f"\n=== {cluster_name} ({cluster_size} files) ===")

        before_schema = LLMClient.get_total_usage()
        schema_result = extract_schema(
            Web2JsonConfig(
                name=f"{cluster_name}_schema",
                html_path=str(cluster_html_dir),
                output_path=str(pipeline_root),
                iteration_rounds=rounds,
                save=["schema"],
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
    summary = {
        "source_jsonl": str(source_jsonl_path),
        "manifest": str(manifest_path),
        "html_dir": str(html_dir),
        "pipeline_root": str(pipeline_root),
        "cluster_count": len(cluster_names),
        "clusters": cluster_summaries,
        "total_token_usage": total_usage,
    }

    summary_path = pipeline_root / "pipeline_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsummary: {summary_path}")
    print(json.dumps(total_usage, ensure_ascii=False, indent=2))

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
    run_jsonl_pipeline(
        source_jsonl=args.source_jsonl,
        work_id=args.work_id,
        input_root=args.input_root,
        output_root=args.output_root,
        html_key=args.html_key,
        iteration_rounds=args.iteration_rounds,
        cluster_limit=args.cluster_limit,
    )


if __name__ == "__main__":
    main()
