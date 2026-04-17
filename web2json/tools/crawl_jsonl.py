"""
Crawl JSONL helpers: cluster split & optional materialize to .html for legacy pipeline.

JSONL rows are expected to be JSON objects with at least a string field for HTML
(default key ``html``). Record identity defaults to ``track_id`` or ``line_{n}``.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_filename_part(s: str, max_len: int = 80) -> str:
    s = _SAFE_NAME.sub("_", s.strip())[:max_len]
    return s or "id"


def iter_crawl_jsonl_records(
    jsonl_path: Path,
    *,
    html_field: str = "html",
    id_field: Optional[str] = "track_id",
) -> Iterator[Tuple[int, str, Dict[str, Any], str]]:
    """
    Yield (line_index_1based, record_id, obj, html_string) for each line with usable html.

    Lines that are empty, non-JSON, or missing html are skipped (not yielded).
    """
    with jsonl_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            html = obj.get(html_field)
            if not isinstance(html, str) or not html.strip():
                continue
            if id_field and obj.get(id_field) is not None:
                rid = str(obj[id_field])
            else:
                rid = f"line_{i}"
            yield i, rid, obj, html


def materialize_jsonl_to_html_dir(
    jsonl_path: Path,
    dest_dir: Path,
    *,
    html_field: str = "html",
    id_field: Optional[str] = "track_id",
) -> List[str]:
    """
    Write one ``.html`` file per JSONL row (only rows with non-empty ``html_field``).

    Filenames: ``{line_index:06d}_{safe_id}.html`` to preserve order and avoid collisions.

    Returns sorted list of absolute paths to written HTML files.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    out: List[str] = []
    for line_no, rid, _obj, html in iter_crawl_jsonl_records(
        jsonl_path, html_field=html_field, id_field=id_field
    ):
        safe = _safe_filename_part(rid)
        name = f"{line_no:06d}_{safe}.html"
        p = dest_dir / name
        p.write_text(html, encoding="utf-8")
        out.append(str(p.resolve()))
    out.sort()
    return out


def discover_jsonl_files(directory: Path, *, recursive: bool = True) -> List[Path]:
    """Return sorted ``*.jsonl`` paths under ``directory`` (``rglob`` if ``recursive``)."""
    if not directory.is_dir():
        raise NotADirectoryError(f"不是目录: {directory}")
    if recursive:
        found = sorted(directory.rglob("*.jsonl"))
    else:
        found = sorted(directory.glob("*.jsonl"))
    return [p for p in found if p.is_file()]


def load_crawl_line_metas_for_file(
    jsonl_path: Path,
    *,
    html_field: str = "html",
    record_id_field: Optional[str] = "track_id",
) -> List[Dict[str, Any]]:
    """
    解析单个 crawl JSONL，每行一条 meta（与 ``classify_crawl_jsonl`` 规则一致）。

    每条 meta 含: ``line_no``, ``obj``, ``html`` (可 None), ``rid``, ``source_jsonl``, ``source_name``。
    """
    source_jsonl = str(jsonl_path.resolve())
    source_name = jsonl_path.name
    metas: List[Dict[str, Any]] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                metas.append(
                    {
                        "line_no": line_no,
                        "obj": {
                            "_classify_json_error": "json_decode_error",
                            "line": line_no,
                            "source_jsonl": source_jsonl,
                        },
                        "html": None,
                        "rid": f"{source_name}:{line_no}",
                        "source_jsonl": source_jsonl,
                        "source_name": source_name,
                    }
                )
                continue
            if not isinstance(obj, dict):
                metas.append(
                    {
                        "line_no": line_no,
                        "obj": {
                            "_classify_json_error": "not_a_json_object",
                            "line": line_no,
                            "source_jsonl": source_jsonl,
                        },
                        "html": None,
                        "rid": f"{source_name}:{line_no}",
                        "source_jsonl": source_jsonl,
                        "source_name": source_name,
                    }
                )
                continue
            html = obj.get(html_field)
            if not isinstance(html, str) or not html.strip():
                rid_local = (
                    str(obj[record_id_field])
                    if record_id_field and obj.get(record_id_field) is not None
                    else f"line_{line_no}"
                )
                metas.append(
                    {
                        "line_no": line_no,
                        "obj": obj,
                        "html": None,
                        "rid": rid_local,
                        "source_jsonl": source_jsonl,
                        "source_name": source_name,
                    }
                )
                continue
            rid_local = (
                str(obj[record_id_field])
                if record_id_field and obj.get(record_id_field) is not None
                else f"line_{line_no}"
            )
            metas.append(
                {
                    "line_no": line_no,
                    "obj": obj,
                    "html": html,
                    "rid": rid_local,
                    "source_jsonl": source_jsonl,
                    "source_name": source_name,
                }
            )
    return metas


def write_jsonl_lines(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def split_jsonl_by_cluster_labels(
    records: List[Dict[str, Any]],
    labels: List[int],
    *,
    out_dir: Path,
    stem: str,
) -> Dict[str, Path]:
    """
    Write ``{stem}_cluster_{k}.jsonl`` and ``{stem}_noise.jsonl`` for label -1.

    ``records`` and ``labels`` must have the same length.
    """
    if len(records) != len(labels):
        raise ValueError("records and labels length mismatch")

    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for rec, lab in zip(records, labels):
        key = "noise" if lab == -1 else f"cluster_{lab}"
        buckets.setdefault(key, []).append(rec)

    written: Dict[str, Path] = {}
    for key, rows in buckets.items():
        if key == "noise":
            path = out_dir / f"{stem}_noise.jsonl"
        else:
            path = out_dir / f"{stem}_{key}.jsonl"
        write_jsonl_lines(path, rows)
        written[key] = path
    return written
