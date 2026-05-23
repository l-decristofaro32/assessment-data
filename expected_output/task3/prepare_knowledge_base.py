#!/usr/bin/env python3
"""Prepare a vector-ready Knowledge Base for RAG."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
CLEANED_DIR = ROOT / "expected_output" / "task2" / "cleaned_data"
TASK3_DIR = ROOT / "expected_output" / "task3"

KB_PATH = TASK3_DIR / "knowledge_base.jsonl"
RETRIEVAL_REPORT_PATH = TASK3_DIR / "retrieval_test_results.md"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
FALLBACK_EMBEDDING_DIM = 64


def normalize_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def stable_id(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:16]


def fake_embedding(text: str, dim: int = FALLBACK_EMBEDDING_DIM) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [round((digest[i % len(digest)] / 255.0) * 2 - 1, 6) for i in range(dim)]


def get_client() -> Any | None:
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)


def embed(text: str, client: Any | None) -> list[float]:
    if client is None:
        return fake_embedding(text)

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_record(
    record_id: str,
    content: str,
    metadata: dict[str, Any],
    client: Any | None,
) -> dict[str, Any]:
    return {
        "id": record_id,
        "content": content,
        "embedding": embed(content, client),
        "metadata": metadata,
    }


def chunk_projects(projects: pd.DataFrame, client: Any | None) -> list[dict[str, Any]]:
    records = []

    for _, row in projects.iterrows():
        workspace_id = normalize_text(row.get("workspace_id")) or None
        project_id = normalize_text(row.get("project_id")) or None

        content = (
            f"Project {project_id}. "
            f"Name: {normalize_text(row.get('project_name'))}. "
            f"Client: {normalize_text(row.get('client_name'))}. "
            f"Methodology: {normalize_text(row.get('methodology'))}. "
            f"Status: {normalize_text(row.get('status'))}. "
            f"Budget EUR: {normalize_text(row.get('budget_eur'))}. "
            f"Start date: {normalize_text(row.get('start_date'))}. "
            f"End date: {normalize_text(row.get('end_date'))}. "
            f"Project manager: {normalize_text(row.get('project_manager'))}."
        )

        records.append(
            build_record(
                record_id=f"project-{workspace_id or 'unknown'}-{project_id or stable_id(content)}",
                content=content,
                metadata={
                    "source": "projects",
                    "category": "project",
                    "workspace_id": workspace_id,
                    "project_id": project_id,
                    "created_at": normalize_text(row.get("start_date")) or None,
                    "language": "it",
                    "sensitivity": "internal",
                    "chunking_strategy": "record_based",
                },
                client=client,
            )
        )

    return records


def chunk_interactions(interactions: pd.DataFrame, client: Any | None) -> list[dict[str, Any]]:
    records = []

    for _, row in interactions.iterrows():
        workspace_id = normalize_text(row.get("workspace_id")) or None
        project_id = normalize_text(row.get("project_id")) or None
        interaction_id = normalize_text(row.get("interaction_id")) or None

        content = (
            f"Support interaction {interaction_id}. "
            f"Channel: {normalize_text(row.get('channel'))}. "
            f"Issue type: {normalize_text(row.get('issue_type'))}. "
            f"Description: {normalize_text(row.get('issue_description'))}. "
            f"Resolution: {normalize_text(row.get('resolution'))}. "
            f"Resolved: {normalize_text(row.get('resolved'))}. "
            f"Resolution time hours: {normalize_text(row.get('resolution_time_hours'))}. "
            f"Satisfaction score: {normalize_text(row.get('satisfaction_score'))}."
        )

        records.append(
            build_record(
                record_id=f"interaction-{workspace_id or 'unknown'}-{interaction_id or stable_id(content)}",
                content=content,
                metadata={
                    "source": "interactions",
                    "category": "support",
                    "workspace_id": workspace_id,
                    "project_id": project_id,
                    "interaction_id": interaction_id,
                    "created_at": normalize_text(row.get("interaction_date")) or None,
                    "channel": normalize_text(row.get("channel")) or None,
                    "issue_type": normalize_text(row.get("issue_type")) or None,
                    "language": "it",
                    "sensitivity": "pseudonymized",
                    "chunking_strategy": "ticket_based",
                },
                client=client,
            )
        )

    return records


def parse_faq(text: str) -> list[tuple[str, str, str]]:
    current_category = "general"
    question = None
    answer_parts = []
    chunks = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("---") and line.endswith("---"):
            current_category = line.strip("- ").lower()
            continue

        if line.startswith("Q:"):
            if question and answer_parts:
                chunks.append((current_category, question, " ".join(answer_parts)))
            question = line[2:].strip()
            answer_parts = []
            continue

        if line.startswith("A:"):
            answer_parts.append(line[2:].strip())
            continue

        if question and answer_parts:
            answer_parts.append(line)

    if question and answer_parts:
        chunks.append((current_category, question, " ".join(answer_parts)))

    return chunks


def chunk_faq(client: Any | None) -> list[dict[str, Any]]:
    faq_text = (DATA_DIR / "research_faq.txt").read_text(
        encoding="utf-8",
        errors="replace",
    )

    records = []

    for category, question, answer in parse_faq(faq_text):
        content = f"{question}. {answer}"

        records.append(
            build_record(
                record_id=f"faq-{stable_id(category, question)}",
                content=content,
                metadata={
                    "source": "faq",
                    "category": category,
                    "subcategory": question,
                    "workspace_id": None,
                    "created_at": None,
                    "language": "it",
                    "sensitivity": "public_internal",
                    "chunking_strategy": "semantic_qa",
                },
                client=client,
            )
        )

    return records


def write_jsonl(records: list[dict[str, Any]]) -> None:
    TASK3_DIR.mkdir(parents=True, exist_ok=True)

    with KB_PATH.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

def lexical_score(query: str, content: str) -> float:
    query_terms = set(re.findall(r"\w+", query.lower()))
    content_terms = set(re.findall(r"\w+", content.lower()))

    if not query_terms:
        return 0.0

    return len(query_terms & content_terms) / len(query_terms)

def retrieve(
    query: str,
    records: list[dict[str, Any]],
    client: Any | None,
    top_k: int = 3,
    workspace_id: str | None = None,
    source: str | None = None,
) -> list[tuple[float, dict[str, Any]]]:
    candidates = records

    if workspace_id:
        candidates = [
            record
            for record in candidates
            if record["metadata"].get("workspace_id") in {workspace_id, None}
        ]

    if source:
        candidates = [
            record
            for record in candidates
            if record["metadata"].get("source") == source
        ]

    if client is None:
        scored = [
            (lexical_score(query, record["content"]), record)
            for record in candidates
        ]
    else:
        query_embedding = embed(query, client)
        scored = [
            (cosine_similarity(query_embedding, record["embedding"]), record)
            for record in candidates
        ]

    return sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]


def write_retrieval_test(records: list[dict[str, Any]], client: Any | None) -> None:
    queries = [
        {
            "query": "CATI metodologia interviste telefoniche",
            "workspace_id": None,
            "source": "projects",
        },
        {
            "query": "Technical Support accesso link errore sondaggio",
            "workspace_id": "WS-001",
            "source": "interactions",
        },
        {
            "query": "CATI",
            "workspace_id": None,
            "source": "projects",
        },
    ]

    lines = [
        "# Retrieval Test Results",
        "",
        f"- Embedding model: `{EMBEDDING_MODEL if client else f'fallback-{FALLBACK_EMBEDDING_DIM}d'}`",
        f"- Retrieval mode: `{'cosine similarity over OpenAI embeddings' if client else 'lexical fallback for offline test'}`",
        "- Top K: 2",
        "",
    ]

    for item in queries:
        lines.append(f"## Query: {item['query']}")
        lines.append("")
        if item["workspace_id"]:
            lines.append(f"Workspace filter: `{item['workspace_id']}`")
            lines.append("")

        results = retrieve(
            query=item["query"],
            records=records,
            client=client,
            top_k=3,
            workspace_id=item["workspace_id"],
            source=item["source"],
        )

        for rank, (score, record) in enumerate(results, start=1):
            metadata = record["metadata"]
            preview = record["content"][:240].replace("\n", " ")

            lines.extend(
                [
                    f"### Result {rank}",
                    "",
                    f"- Score: `{score:.4f}`",
                    f"- ID: `{record['id']}`",
                    f"- Source: `{metadata.get('source')}`",
                    f"- Category: `{metadata.get('category')}`",
                    f"- Workspace: `{metadata.get('workspace_id')}`",
                    f"- Preview: {preview}...",
                    "",
                ]
            )

    RETRIEVAL_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    client = get_client()

    if client:
        print(f"Using OpenAI embeddings: {EMBEDDING_MODEL}")
    else:
        print(f"OPENAI_API_KEY not found. Using fallback embeddings: {FALLBACK_EMBEDDING_DIM} dimensions")

    projects = pd.read_csv(CLEANED_DIR / "projects.csv")
    interactions = pd.read_csv(CLEANED_DIR / "interactions.csv")

    records = []
    records.extend(chunk_projects(projects, client))
    records.extend(chunk_interactions(interactions, client))
    records.extend(chunk_faq(client))

    write_jsonl(records)
    write_retrieval_test(records, client)

    print(f"Generated {len(records)} records")
    print(f"Knowledge base: {KB_PATH}")
    print(f"Retrieval test: {RETRIEVAL_REPORT_PATH}")


if __name__ == "__main__":
    main()