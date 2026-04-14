#!/usr/bin/env python3
"""
校验 source jsonl / manifest / html / result json 之间的一致性。

示例：
python scripts/verify_extract_alignment.py \
  --source-jsonl ToClassify/source.jsonl \
  --manifest input_html/npi_sample_2000/manifest.jsonl \
  --html-dir input_html/npi_category_detail_cluster_1 \
  --result-dir output/npi_category_detail_cluster_1_code/result \
  --output output/npi_category_detail_cluster_1_code/qa_report.json

或者直接使用 cluster manifest：
python scripts/verify_extract_alignment.py \
  --source-jsonl ToClassify/source.jsonl \
  --cluster-manifest output/npi_category_detail_cluster_1_code/cluster_manifest.json \
  --manifest input_html/npi_sample_2000/manifest.jsonl
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from bs4 import BeautifulSoup


@dataclass
class FileReport:
    filename: str
    source_line: int | None
    url: str | None
    track_id: str | None
    html_exists: bool
    result_exists: bool
    source_match: bool
    html_len_match: bool
    field_checks: dict[str, dict[str, Any]]
    ok: bool
    errors: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify alignment across source jsonl, manifest, html files, and result json."
    )
    parser.add_argument("--source-jsonl", required=True, help="原始 crawl jsonl 文件路径。")
    parser.add_argument("--manifest", required=True, help="完整 manifest.jsonl 文件路径。")
    parser.add_argument(
        "--cluster-manifest",
        default="",
        help="cluster_manifest.json 路径。提供后会从其中自动读取 html-dir / result-dir / 文件子集 / schema-path。",
    )
    parser.add_argument("--html-dir", default="", help="HTML 文件目录。")
    parser.add_argument("--result-dir", default="", help="解析结果 JSON 目录。")
    parser.add_argument("--schema-json", default="", help="cluster 对应的 schema.json 路径。")
    parser.add_argument("--output", default="", help="QA 报告输出路径（可选）。")
    parser.add_argument(
        "--fields",
        nargs="*",
        default=None,
        help="要校验是否出现在 HTML 中的结果字段。未提供时会优先从 schema 自动推断，否则回退到 title content。",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fp:
        for line_no, line in enumerate(fp, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path} line {line_no}: {exc}") from exc
    return rows


def load_target_files(
    manifest_rows: list[dict[str, Any]], cluster_manifest_path: Path | None
) -> tuple[list[dict[str, Any]], str, str, str]:
    if not cluster_manifest_path:
        return manifest_rows, "", "", ""

    cluster_manifest = json.loads(cluster_manifest_path.read_text(encoding="utf-8"))
    wanted = {item["filename"] for item in cluster_manifest.get("files", [])}
    filtered_rows = [row for row in manifest_rows if row.get("filename") in wanted]
    html_dir = cluster_manifest.get("input_dir", "")
    result_dir = cluster_manifest.get("result_dir", "")
    schema_path = cluster_manifest.get("schema_path", "")
    return filtered_rows, html_dir, result_dir, schema_path


def derive_fields_from_schema(schema_path: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    fields: list[str] = []
    for field_name, field_meta in schema.items():
        if not isinstance(field_meta, dict):
            continue
        if field_meta.get("type") == "string":
            fields.append(field_name)
    return fields


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return " ".join(value.split())


def check_field_in_html(field_value: Any, html_text: str) -> dict[str, Any]:
    normalized_value = normalize_text(field_value)
    normalized_html = normalize_text(html_text)
    normalized_text = normalize_text(BeautifulSoup(html_text, "html.parser").get_text(" ", strip=True))

    if not normalized_value:
        return {
            "value_present": False,
            "raw_html_match": False,
            "text_match": False,
            "substring_match": False,
            "value_len": 0,
        }

    return {
        "value_present": True,
        "raw_html_match": normalized_value in normalized_html,
        "text_match": normalized_value in normalized_text,
        "substring_match": normalized_value in normalized_html or normalized_value in normalized_text,
        "value_len": len(normalized_value),
    }


def main() -> None:
    args = parse_args()

    source_jsonl = Path(args.source_jsonl)
    manifest_path = Path(args.manifest)
    cluster_manifest_path = Path(args.cluster_manifest) if args.cluster_manifest else None
    output_path = Path(args.output) if args.output else None

    source_rows = load_jsonl(source_jsonl)
    manifest_rows = load_jsonl(manifest_path)
    target_rows, cluster_html_dir, cluster_result_dir, cluster_schema_path = load_target_files(
        manifest_rows, cluster_manifest_path
    )

    html_dir_str = args.html_dir or cluster_html_dir
    result_dir_str = args.result_dir or cluster_result_dir
    schema_json_str = args.schema_json or cluster_schema_path
    if not html_dir_str or not result_dir_str:
        raise ValueError("html-dir 和 result-dir 不能为空；可直接传参，或通过 cluster-manifest 提供。")

    html_dir = Path(html_dir_str)
    result_dir = Path(result_dir_str)
    schema_json_path = Path(schema_json_str) if schema_json_str else None

    if args.fields is not None:
        fields_to_check = args.fields
    elif schema_json_path and schema_json_path.exists():
        fields_to_check = derive_fields_from_schema(schema_json_path)
        if not fields_to_check:
            fields_to_check = ["title", "content"]
    else:
        fields_to_check = ["title", "content"]

    reports: list[FileReport] = []
    ok_count = 0

    for manifest_row in target_rows:
        filename = manifest_row["filename"]
        source_line = manifest_row.get("source_line")
        url = manifest_row.get("url")
        track_id = manifest_row.get("track_id")

        html_path = html_dir / filename
        result_path = result_dir / filename.replace(".html", ".json")

        errors: list[str] = []
        html_exists = html_path.exists()
        result_exists = result_path.exists()
        source_match = False
        html_len_match = False
        field_checks: dict[str, dict[str, Any]] = {}

        html_text = ""
        if html_exists:
            html_text = html_path.read_text(encoding="utf-8")
        else:
            errors.append(f"missing_html:{html_path}")

        result_data: dict[str, Any] = {}
        if result_exists:
            result_data = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            errors.append(f"missing_result:{result_path}")

        if source_line is not None and 1 <= source_line <= len(source_rows):
            source_row = source_rows[source_line - 1]
            source_match = (
                source_row.get("track_id") == track_id
                and source_row.get("url") == url
            )
            if not source_match:
                errors.append("source_manifest_mismatch")

            source_html = source_row.get("html", "")
            html_len_match = len(source_html) == manifest_row.get("html_len")
            if not html_len_match:
                errors.append("source_manifest_html_len_mismatch")

            if html_exists and len(html_text) != len(source_html):
                errors.append("source_html_file_len_mismatch")
            elif html_exists and html_text != source_html:
                errors.append("source_html_file_content_mismatch")
        else:
            errors.append("invalid_source_line")

        if html_exists and result_exists:
            for field in fields_to_check:
                field_checks[field] = check_field_in_html(result_data.get(field), html_text)
                if field_checks[field]["value_present"] and not field_checks[field]["substring_match"]:
                    errors.append(f"field_not_found_in_html:{field}")

        ok = not errors
        if ok:
            ok_count += 1

        reports.append(
            FileReport(
                filename=filename,
                source_line=source_line,
                url=url,
                track_id=track_id,
                html_exists=html_exists,
                result_exists=result_exists,
                source_match=source_match,
                html_len_match=html_len_match,
                field_checks=field_checks,
                ok=ok,
                errors=errors,
            )
        )

    summary = {
        "source_jsonl": str(source_jsonl),
        "manifest": str(manifest_path),
        "cluster_manifest": str(cluster_manifest_path) if cluster_manifest_path else "",
        "html_dir": str(html_dir),
        "result_dir": str(result_dir),
        "schema_json": str(schema_json_path) if schema_json_path else "",
        "fields_checked": fields_to_check,
        "total_files": len(reports),
        "ok_files": ok_count,
        "failed_files": len(reports) - ok_count,
        "reports": [asdict(report) for report in reports],
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"qa_report: {output_path}")

    print(f"total_files: {summary['total_files']}")
    print(f"ok_files: {summary['ok_files']}")
    print(f"failed_files: {summary['failed_files']}")

    for report in reports:
        status = "OK" if report.ok else "FAIL"
        print(f"{status} {report.filename}")
        if report.errors:
            print(f"  errors: {', '.join(report.errors)}")


if __name__ == "__main__":
    main()
