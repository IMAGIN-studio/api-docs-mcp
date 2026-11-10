"""Retrieval evaluation for search_docs.

Builds a throwaway index per variant from the locally cloned docs and scores
each variant against a fixed question set (eval/questions.json). Nothing here
ships in the package; it exists to compare search changes with numbers.

A question counts as answered at rank r when the r-th result comes from one of
its expected document paths. Metrics per variant:

- hit@1: the top result is from an expected page
- hit@k: any of the top k results is from an expected page
- MRR:   mean of 1/r for the first expected result (0 when none in top k)

Variants are the grid of exclusion set x chunk size x search mode x query
instruction, where mode is "vector", "hybrid" (vector + BM25, fused by
weighted RRF) or "fts" (BM25 only, for reference). Hybrid variants are further
swept over candidate depth, RRF k and keyword weight.

Usage (from the repo root, after the server has cloned the docs once):

    .venv/bin/python -m eval.run_eval
    .venv/bin/python -m eval.run_eval --sizes 8192 2000 --modes vector hybrid --misses
    .venv/bin/python -m eval.run_eval --modes hybrid --instruction on \
        --candidates 5 20 50 --rrf-k 60 20 --weights 0.5 1 2 --exclude none mcp summary both
"""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from src.config import (
    DOCS_DIR,
    EMBEDDING_QUERY_INSTRUCTION,
    HYBRID_CANDIDATES,
    HYBRID_KEYWORD_WEIGHT,
    MAX_CHUNK_CHARS,
    RRF_K,
)
from src.engine.embedder import Embedder
from src.engine.vector_store import VectorStore
from src.pipeline.chunker import chunk_document
from src.pipeline.markdown_parser import parse_all_documents
from src.pipeline.models import Chunk
from src.pipeline.openapi_parser import find_spec_file, load_openapi_spec, parse_openapi_spec


QUESTIONS_FILES = sorted(Path(__file__).parent.glob("questions*.json"))
MODES = ("vector", "hybrid", "fts")
EXCLUDE_SETS: dict[str, frozenset[str]] = {
    "none": frozenset(),
    "mcp": frozenset({"api-integration/manuals/mcp-api-documentation.md"}),
    "summary": frozenset({"SUMMARY.md"}),
    "both": frozenset({"api-integration/manuals/mcp-api-documentation.md", "SUMMARY.md"}),
}


@dataclass
class Score:
    """Accumulated metrics for one variant (overall or one category)."""

    n: int = 0
    hit1: int = 0
    hitk: int = 0
    rr: float = 0.0

    def add(self, rank: int | None) -> None:
        self.n += 1
        if rank is not None:
            self.hitk += 1
            self.rr += 1.0 / rank
            if rank == 1:
                self.hit1 += 1

    def row(self) -> str:
        if not self.n:
            return "n/a"
        return f"{self.hit1 / self.n:.2f} / {self.hitk / self.n:.2f} / {self.rr / self.n:.2f}"


@dataclass
class VariantResult:
    """Scores for one variant, plus the questions it missed."""

    name: str
    overall: Score = field(default_factory=Score)
    by_category: dict[str, Score] = field(default_factory=dict)
    misses: list[dict[str, object]] = field(default_factory=list)


def build_chunks(docs_dir: Path, max_chars: int, exclude: frozenset[str] = frozenset()) -> list[Chunk]:
    """Chunk the markdown docs (minus *exclude*) and the OpenAPI spec at *max_chars*."""
    chunks: list[Chunk] = []
    for doc in parse_all_documents(docs_dir, exclude):
        chunks.extend(chunk_document(doc, max_chars=max_chars))
    spec_path = find_spec_file(docs_dir)
    spec = load_openapi_spec(spec_path) if spec_path else None
    if spec:
        chunks.extend(parse_openapi_spec(spec, max_chars=max_chars))
    return chunks


def build_store(chunks: list[Chunk], embedder: Embedder, db_dir: Path) -> VectorStore:
    """Embed *chunks* and write them (with the FTS index) to a fresh store."""
    store = VectorStore(db_path=db_dir)
    store.upsert_chunks(
        chunk_ids=[c.chunk_id for c in chunks],
        document_paths=[c.document_path for c in chunks],
        heading_hierarchies=[" > ".join(c.heading_hierarchy) for c in chunks],
        contents=[c.content for c in chunks],
        urls=[c.url for c in chunks],
        vectors=embedder.embed_texts([c.content for c in chunks]),
    )
    return store


@dataclass(frozen=True)
class Fusion:
    """Hybrid fusion settings for one variant."""

    candidates: int
    rrf_k: int
    weight: float

    def label(self) -> str:
        return f"c{self.candidates} k{self.rrf_k} w{self.weight:g}"


def ranked_paths(
    store: VectorStore,
    mode: str,
    query: str,
    vector: list[float],
    top_k: int,
    fusion: Fusion | None = None,
) -> list[str]:
    """Document paths of the top results, in rank order."""
    if mode == "fts":
        table = store._get_db().open_table(store._table_name)
        res = table.search(query, query_type="fts").limit(top_k).to_arrow()
        return [str(p) for p in res.column("document_path").to_pylist()]
    if mode == "vector":
        return [r.document_path for r in store.search(vector, top_k=top_k)]
    assert fusion is not None
    results = store.search(
        vector,
        top_k=top_k,
        query_text=query,
        candidates=fusion.candidates,
        rrf_k=fusion.rrf_k,
        keyword_weight=fusion.weight,
    )
    return [r.document_path for r in results]


def first_hit(paths: list[str], expected: set[str]) -> int | None:
    """1-based rank of the first expected path, or None."""
    for i, path in enumerate(paths, 1):
        if path in expected:
            return i
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--docs-dir", type=Path, default=DOCS_DIR)
    parser.add_argument("--questions", type=Path, nargs="+", default=QUESTIONS_FILES)
    parser.add_argument("--sizes", type=int, nargs="+", default=[MAX_CHUNK_CHARS])
    parser.add_argument("--modes", nargs="+", choices=MODES, default=list(MODES))
    parser.add_argument("--instruction", choices=("on", "off", "both"), default="both")
    parser.add_argument("--candidates", type=int, nargs="+", default=[HYBRID_CANDIDATES])
    parser.add_argument("--rrf-k", type=int, nargs="+", default=[RRF_K])
    parser.add_argument("--weights", type=float, nargs="+", default=[HYBRID_KEYWORD_WEIGHT])
    parser.add_argument("--exclude", nargs="+", choices=list(EXCLUDE_SETS), default=["none"])
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--misses", action="store_true", help="print missed questions")
    parser.add_argument("--json", type=Path, help="write all results to this file")
    args = parser.parse_args()

    questions = [q for f in args.questions for q in json.loads(f.read_text())["questions"]]
    categories = sorted({q["category"] for q in questions})
    embedder = Embedder()

    instructions = {"on": [EMBEDDING_QUERY_INSTRUCTION], "off": [""]}.get(
        args.instruction, ["", EMBEDDING_QUERY_INSTRUCTION]
    )
    query_vectors = {
        instr: {q["id"]: embedder.embed_query(q["query"], instruction=instr) for q in questions}
        for instr in instructions
    }
    fusions = [Fusion(c, k, w) for c in args.candidates for k in args.rrf_k for w in args.weights]

    results: list[VariantResult] = []
    for exclude_name in args.exclude:
        for size in args.sizes:
            chunks = build_chunks(args.docs_dir, size, EXCLUDE_SETS[exclude_name])
            longest = max(len(c.content) for c in chunks)
            print(f"exclude {exclude_name}, size {size}: {len(chunks)} chunks (longest {longest})")
            with tempfile.TemporaryDirectory() as tmp:
                store = build_store(chunks, embedder, Path(tmp))
                for mode in args.modes:
                    for instr in instructions:
                        if mode == "fts" and instr != instructions[0]:
                            continue  # the instruction only affects vectors
                        for fusion in fusions if mode == "hybrid" else [None]:
                            name = " ".join(
                                part
                                for part in (
                                    exclude_name,
                                    str(size),
                                    mode,
                                    "" if mode == "fts" else ("instr" if instr else "plain"),
                                    fusion.label() if fusion else "",
                                )
                                if part
                            )
                            vr = VariantResult(name, by_category={c: Score() for c in categories})
                            for q in questions:
                                paths = ranked_paths(
                                    store,
                                    mode,
                                    q["query"],
                                    query_vectors[instr][q["id"]],
                                    args.top_k,
                                    fusion,
                                )
                                rank = first_hit(paths, set(q["expected"]))
                                vr.overall.add(rank)
                                vr.by_category[q["category"]].add(rank)
                                if rank is None:
                                    vr.misses.append({"id": q["id"], "query": q["query"], "got": paths})
                            results.append(vr)

    width = max(len(vr.name) for vr in results)
    header = f"{'variant':<{width}} | {'overall':<16} | " + " | ".join(f"{c:<16}" for c in categories)
    print(f"\nhit@1 / hit@{args.top_k} / MRR over {len(questions)} questions\n")
    print(header)
    print("-" * len(header))
    for vr in results:
        cats = " | ".join(f"{vr.by_category[c].row():<16}" for c in categories)
        print(f"{vr.name:<{width}} | {vr.overall.row():<16} | {cats}")

    if args.misses:
        for vr in results:
            print(f"\n== misses: {vr.name} ({len(vr.misses)})")
            for m in vr.misses:
                print(f"  {m['id']}: {m['query']}")

    if args.json:
        args.json.write_text(
            json.dumps(
                [
                    {
                        "variant": vr.name,
                        "overall": vars(vr.overall),
                        "by_category": {c: vars(s) for c, s in vr.by_category.items()},
                        "misses": vr.misses,
                    }
                    for vr in results
                ],
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
