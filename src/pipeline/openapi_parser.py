"""Parse an OpenAPI spec into one searchable Chunk per endpoint.

The IMAGIN CDN image API is documented by a YAML spec committed inside the docs
repository (``.gitbook/assets/openapi (1).yaml``). Because that file rides the
existing git sync, a committed spec change is re-indexed automatically — there is
no HTTP fetch and no separate freshness mechanism.

Each operation (method + path) becomes one ``Chunk``, or several when its text is
longer than ``max_chars``. The embedding model only reads the first 512 tokens of
an input, so a long endpoint is split rather than truncated: every part after the
first starts with ``METHOD /path (continued)`` and keeps the same document path.
The text is high-signal-first (method/path/summary/description/required params
before optional ones). Local ``$ref`` pointers —
both ``components.parameters`` and ``components.schemas`` — are resolved so each
chunk carries real parameter names and descriptions rather than opaque refs.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import yaml

from src.config import DOCS_DIR, MAX_CHUNK_CHARS, OPENAPI_DOCS_URL, OPENAPI_SPEC_RELPATH
from src.pipeline.chunker import split_with_continuation
from src.pipeline.models import Chunk


logger = logging.getLogger(__name__)

_HTTP_METHODS = ("get", "put", "post", "patch", "delete", "head", "options", "trace")
_MAX_REF_DEPTH = 6


def find_spec_file(docs_dir: Path = DOCS_DIR) -> Path | None:
    """Locate the OpenAPI spec inside the cloned docs repo.

    Prefers the configured path; if that exact file is absent (e.g. a GitBook
    re-upload renamed the asset), falls back to the ``*.yaml``/``*.yml`` under
    ``.gitbook/assets`` declaring the most operations. Returns None if none found.
    """
    primary = docs_dir / OPENAPI_SPEC_RELPATH
    if primary.is_file():
        return primary

    assets = docs_dir / ".gitbook" / "assets"
    if not assets.is_dir():
        return None

    best: Path | None = None
    best_ops = 0
    for candidate in sorted(assets.glob("*.yaml")) + sorted(assets.glob("*.yml")):
        spec = load_openapi_spec(candidate)
        if spec is None:
            continue
        n_ops = _count_operations(spec)
        if n_ops > best_ops:
            best, best_ops = candidate, n_ops
    if best is not None:
        logger.info("Selected OpenAPI spec %s (%d operations)", best.name, best_ops)
    return best


def load_openapi_spec(path: Path) -> dict[str, Any] | None:
    """Load and parse a YAML/JSON OpenAPI spec. Returns None on any error."""
    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError):
        logger.warning("Could not read/parse OpenAPI spec at %s", path, exc_info=True)
        return None
    if not isinstance(data, dict):
        return None
    return data


def parse_openapi_spec(
    spec: dict[str, Any],
    docs_url: str = OPENAPI_DOCS_URL,
    max_chars: int = MAX_CHUNK_CHARS,
) -> list[Chunk]:
    """Convert an OpenAPI spec into one Chunk per operation.

    Malformed paths/operations are skipped rather than aborting the batch.
    """
    if not isinstance(spec, dict):
        return []
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return []

    server_url = _first_server_url(spec)
    chunks: list[Chunk] = []
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        raw_path_params = item.get("parameters")
        path_params = raw_path_params if isinstance(raw_path_params, list) else []
        for method, operation in item.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            chunks.extend(
                _build_operation_chunks(
                    method, path, operation, path_params, spec, server_url, docs_url, max_chars
                )
            )
    return chunks


def _count_operations(spec: dict[str, Any]) -> int:
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return 0
    count = 0
    for item in paths.values():
        if isinstance(item, dict):
            count += sum(1 for method in item if method.lower() in _HTTP_METHODS)
    return count


def _first_server_url(spec: dict[str, Any]) -> str:
    servers = spec.get("servers")
    if isinstance(servers, list) and servers and isinstance(servers[0], dict):
        url = servers[0].get("url")
        if isinstance(url, str):
            return url
    return ""


def _build_operation_chunks(
    method: str,
    path: str,
    operation: dict[str, Any],
    path_params: list[Any],
    root: dict[str, Any],
    server_url: str,
    docs_url: str,
    max_chars: int,
) -> list[Chunk]:
    method_upper = method.upper()
    document_path = f"openapi:{method_upper} {path}"

    tags = operation.get("tags")
    tag = tags[0] if isinstance(tags, list) and tags and isinstance(tags[0], str) else "API"

    lines: list[str] = [f"{method_upper} {path}"]
    summary = operation.get("summary")
    if isinstance(summary, str) and summary:
        lines.append(summary)
    lines.append(f"Tags: {tag}")
    if server_url:
        lines.append(f"Server: {server_url}")

    description = operation.get("description")
    if isinstance(description, str) and description:
        lines += ["", description]

    params = _collect_parameters(operation, path_params, root)
    if params:
        lines += ["", "Parameters:"]
        lines += [_format_param(p) for p in params]

    body = _format_request_body(operation, root)
    if body:
        lines += ["", body]

    responses = _format_responses(operation, root)
    if responses:
        lines += ["", *responses]

    content = "\n".join(lines).strip()
    parts = split_with_continuation(content, max_chars, f"{method_upper} {path} (continued)")

    return [
        Chunk(
            # Part 0 keeps the historical id; later parts get an index suffix.
            chunk_id=_operation_chunk_id(document_path if i == 0 else f"{document_path}#{i}"),
            document_path=document_path,
            heading_hierarchy=[tag],
            content=part,
            url=docs_url,
        )
        for i, part in enumerate(parts)
    ]


def _operation_chunk_id(key: str) -> str:
    """Deterministic chunk id for an operation (or one of its parts)."""
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _collect_parameters(
    operation: dict[str, Any], path_params: list[Any], root: dict[str, Any]
) -> list[dict[str, Any]]:
    """Resolve + merge path-level and operation-level parameters (deduped, required first)."""
    op_params = operation.get("parameters")
    raw = list(path_params) + (op_params if isinstance(op_params, list) else [])

    resolved: list[dict[str, Any]] = []
    seen: set[str] = set()
    for param in raw:
        r = _resolve_refs(param, root)
        if not isinstance(r, dict):
            continue
        name = r.get("name")
        key = name if isinstance(name, str) else str(r.get("$ref"))
        if key in seen:
            continue
        seen.add(key)
        resolved.append(r)

    required = [p for p in resolved if p.get("required")]
    optional = [p for p in resolved if not p.get("required")]
    return required + optional


def _format_param(param: dict[str, Any]) -> str:
    name = param.get("name")
    if not isinstance(name, str) or not name:
        return f"- (unresolved parameter: {param.get('$ref', 'unknown')})"
    location = param.get("in")
    loc_txt = f"{location}, " if isinstance(location, str) and location else ""
    required = "required" if param.get("required") else "optional"
    type_txt = _schema_type(param.get("schema"))
    description = param.get("description")
    desc_txt = f" — {description}" if isinstance(description, str) and description else ""
    return f"- {name} ({loc_txt}{required}): {type_txt}{desc_txt}"


def _format_request_body(operation: dict[str, Any], root: dict[str, Any]) -> str:
    request_body = operation.get("requestBody")
    if not isinstance(request_body, dict):
        return ""
    resolved = _resolve_refs(request_body, root)
    if not isinstance(resolved, dict):
        return ""
    content = resolved.get("content")
    required = " required" if resolved.get("required") else ""
    if not isinstance(content, dict) or not content:
        return f"Request body{required}."
    media, media_obj = next(iter(content.items()))
    schema = media_obj.get("schema") if isinstance(media_obj, dict) else None
    summary = _summarize_schema(schema)
    header = f"Request body ({media}{required}):"
    return f"{header}\n{summary}" if summary else header


def _format_responses(operation: dict[str, Any], root: dict[str, Any]) -> list[str]:
    responses = operation.get("responses")
    if not isinstance(responses, dict) or not responses:
        return []
    out = ["Responses:"]
    for status, response in responses.items():
        resolved = _resolve_refs(response, root)
        if not isinstance(resolved, dict):
            continue
        description = resolved.get("description")
        desc_txt = description if isinstance(description, str) else ""
        content = resolved.get("content")
        media = next(iter(content)) if isinstance(content, dict) and content else ""
        media_txt = f" [{media}]" if media else ""
        out.append(f"- {status} — {desc_txt}{media_txt}")
    return out


def _schema_type(schema: Any) -> str:
    if not isinstance(schema, dict):
        return "any"
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return "enum(" + ", ".join(str(v) for v in enum) + ")"
    type_name = schema.get("type")
    if isinstance(type_name, str):
        if type_name == "array":
            return f"array[{_schema_type(schema.get('items'))}]"
        return type_name
    return "any"


def _summarize_schema(schema: Any, depth: int = 0, max_depth: int = 4) -> str:
    if not isinstance(schema, dict) or depth > max_depth:
        return ""
    properties = schema.get("properties")
    if isinstance(properties, dict) and properties:
        required = schema.get("required")
        required_set = set(required) if isinstance(required, list) else set()
        indent = "  " * (depth + 1)
        lines = [
            f"{indent}{name}: {_schema_type(prop)}{' (required)' if name in required_set else ''}"
            for name, prop in properties.items()
        ]
        return "\n".join(lines)
    type_name = schema.get("type")
    return f"  {type_name}" if isinstance(type_name, str) else ""


def _resolve_refs(
    node: Any, root: dict[str, Any], seen: frozenset[str] = frozenset(), depth: int = 0
) -> Any:
    """Deep-resolve local ``#/...`` ``$ref`` pointers.

    Cycles (a ref already on the current resolution path) and over-deep nesting
    return a ``{"$ref": ...}`` placeholder instead of recursing forever. Missing
    and external refs are left as placeholders too. Never raises.
    """
    if depth > _MAX_REF_DEPTH:
        return node
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str):
            if ref in seen or not ref.startswith("#/"):
                return {"$ref": ref}
            target = _resolve_pointer(root, ref)
            if target is None:
                return {"$ref": ref}
            return _resolve_refs(target, root, seen | {ref}, depth + 1)
        return {key: _resolve_refs(value, root, seen, depth + 1) for key, value in node.items()}
    if isinstance(node, list):
        return [_resolve_refs(value, root, seen, depth + 1) for value in node]
    return node


def _resolve_pointer(root: dict[str, Any], ref: str) -> Any:
    """Resolve one JSON pointer like ``#/components/schemas/Foo`` against *root*."""
    current: Any = root
    for part in ref.lstrip("#/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current
