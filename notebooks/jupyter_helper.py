"""Utilities for running web2json-agent inside Jupyter notebooks."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def prepare_notebook(
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Path:
    """Prepare the notebook process for local package imports and env loading."""
    root = Path(project_root).expanduser().resolve() if project_root else PROJECT_ROOT

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    os.chdir(root)

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    if api_base:
        os.environ["OPENAI_API_BASE"] = api_base

    return root


def make_extract_config(
    name: str,
    html_path: str,
    output_path: str = "output",
    save: Optional[Sequence[str]] = ("schema", "code", "data"),
    schema: Optional[dict[str, Any]] = None,
    iteration_rounds: int = 3,
    enable_schema_edit: bool = False,
    remove_null_fields: bool = True,
    parser_code: Optional[str] = None,
):
    """Build a Web2JsonConfig with notebook-friendly path resolution."""
    prepare_notebook()

    from web2json import Web2JsonConfig

    html_target = _resolve_project_path(html_path)
    output_target = _resolve_project_path(output_path)

    return Web2JsonConfig(
        name=name,
        html_path=str(html_target),
        output_path=str(output_target),
        iteration_rounds=iteration_rounds,
        schema=schema,
        enable_schema_edit=enable_schema_edit,
        parser_code=parser_code,
        save=list(save) if save is not None else None,
        remove_null_fields=remove_null_fields,
    )


def preview_records(records: Sequence[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    """Return the first few parsed records so a notebook cell renders them directly."""
    return list(records[:limit])


def print_schema(schema: dict[str, Any]) -> None:
    """Pretty print schema content inside notebooks."""
    print(json.dumps(schema, ensure_ascii=False, indent=2))


def summarize_cluster_result(cluster_result: Any) -> dict[str, Any]:
    """Convert a cluster result into a compact notebook-friendly summary."""
    return {
        "cluster_count": cluster_result.cluster_count,
        "clusters": {name: len(files) for name, files in cluster_result.clusters.items()},
        "noise_files": len(cluster_result.noise_files),
    }


def run_jsonl_pipeline(
    source_jsonl: str,
    work_id: str = "",
    input_root: str = "input_html",
    output_root: str = "output",
    html_key: str = "html",
    iteration_rounds: int = 3,
    cluster_limit: int = 0,
):
    """Run the full JSONL pipeline from a notebook and return the structured summary."""
    prepare_notebook()

    from scripts.run_jsonl_web2json_pipeline import run_jsonl_pipeline as _run_jsonl_pipeline

    return _run_jsonl_pipeline(
        source_jsonl=str(_resolve_project_path(source_jsonl)),
        work_id=work_id,
        input_root=str(_resolve_project_path(input_root)),
        output_root=str(_resolve_project_path(output_root)),
        html_key=html_key,
        iteration_rounds=iteration_rounds,
        cluster_limit=cluster_limit,
    )


def summarize_pipeline_result(result: Any) -> dict[str, Any]:
    """Build a compact summary view for notebook display."""
    return {
        "source_jsonl": result.source_jsonl,
        "pipeline_root": result.pipeline_root,
        "cluster_count": result.cluster_count,
        "clusters": [
            {
                "cluster_name": cluster["cluster_name"],
                "cluster_size": cluster["cluster_size"],
                "parse_success_count": cluster["parse_success_count"],
                "parse_failed_count": cluster["parse_failed_count"],
            }
            for cluster in result.clusters
        ],
        "total_token_usage": result.total_token_usage,
        "summary_path": result.summary_path,
    }


def _resolve_project_path(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()
