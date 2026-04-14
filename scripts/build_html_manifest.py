#!/usr/bin/env python3
"""
从 crawl jsonl 拆分出 HTML 文件，并生成 manifest.jsonl 索引。

示例：
python scripts/build_html_manifest.py \
  --source ToClassify/example.jsonl \
  --output-dir input_html/example_set
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a crawl jsonl into numbered HTML files plus manifest.jsonl."
    )
    parser.add_argument(
        "--source",
        required=True,
        help="源 jsonl 文件路径，每行应至少包含 html 字段。",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="输出目录，会写入 0001.html... 和 manifest.jsonl。",
    )
    parser.add_argument(
        "--html-key",
        default="html",
        help="HTML 内容字段名，默认 html。",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=1,
        help="输出编号起始值，默认 1。",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=4,
        help="输出文件编号宽度，默认 4，例如 0001.html。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="最多处理多少条记录，0 表示不限制。",
    )
    parser.add_argument(
        "--skip-empty-html",
        action="store_true",
        help="遇到缺失或空 html 时跳过该记录；默认直接报错。",
    )
    return parser.parse_args()


def ensure_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def main() -> None:
    args = parse_args()

    source = Path(args.source)
    output_dir = Path(args.output_dir)

    if not source.exists():
        raise FileNotFoundError(f"Source jsonl not found: {source}")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.jsonl"

    processed_count = 0
    skipped_count = 0
    current_index = args.start_index

    with source.open("r", encoding="utf-8") as src, manifest_path.open(
        "w", encoding="utf-8"
    ) as manifest_fp:
        for source_line, line in enumerate(src, start=1):
            if args.limit and processed_count >= args.limit:
                break

            line = line.strip()
            if not line:
                skipped_count += 1
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at line {source_line}: {exc}") from exc

            html = ensure_text(record.get(args.html_key))
            if not html.strip():
                if args.skip_empty_html:
                    skipped_count += 1
                    continue
                raise ValueError(
                    f"Missing or empty '{args.html_key}' at line {source_line}"
                )

            filename = f"{current_index:0{args.width}d}.html"
            html_path = output_dir / filename
            html_path.write_text(html, encoding="utf-8")

            manifest_record = {
                "sample_no": current_index,
                "source_line": source_line,
                "filename": filename,
                "track_id": record.get("track_id"),
                "url": record.get("url"),
                "status": record.get("status"),
                "html_len": len(html),
            }

            manifest_fp.write(json.dumps(manifest_record, ensure_ascii=False) + "\n")

            processed_count += 1
            current_index += 1

    print(f"source: {source}")
    print(f"output_dir: {output_dir}")
    print(f"manifest: {manifest_path}")
    print(f"processed: {processed_count}")
    print(f"skipped: {skipped_count}")


if __name__ == "__main__":
    main()
