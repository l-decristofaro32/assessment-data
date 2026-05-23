# Task 3 — Knowledge Base Preparation for RAG

## Goal

The goal of this task is to prepare cleaned project, support interaction and FAQ data for semantic retrieval in a Retrieval-Augmented Generation (RAG) workflow.

The resulting output is designed to be compatible with vector databases such as:

- OpenSearch
- Pinecone
- pgvector
- Weaviate

---

## Run

From the repository root:

```bash
uv run expected_output/task3/prepare_knowledge_base.py
```

---

## Outputs

The script generates:

```text
expected_output/task3/knowledge_base.jsonl
expected_output/task3/retrieval_test_results.md
```

---

## Embedding strategy

The script supports two embedding modes:

### OpenAI embeddings

If `OPENAI_API_KEY` is configured, the pipeline uses:

```text
text-embedding-3-small
```

This model generates 1536-dimensional embeddings and provides a good trade-off between quality, latency and cost for semantic retrieval tasks.

### Fallback deterministic embeddings

If no API key is available, the script generates deterministic local placeholder embeddings.

This keeps the assignment:
- reproducible,
- runnable offline,
- independent from external services.

The fallback vectors are NOT intended for production semantic quality, but they allow the retrieval pipeline and JSONL format to be tested end-to-end.

---

## Chunking strategy

Different content types use different chunking approaches.

### Projects → record-based chunking

Each project becomes one chunk.

### Support interactions → ticket-based chunking

Each interaction becomes one chunk.

### FAQ → semantic QA chunking

FAQ content is chunked by question-answer pair.

---

## Metadata design

Each chunk contains metadata useful for filtering and retrieval routing.

Main metadata fields:

- source
- category
- workspace_id
- project_id
- interaction_id
- created_at
- language
- sensitivity
- chunking_strategy

---

## Multi-tenancy strategy

The system is designed with tenant-aware retrieval in mind.

workspace_id metadata allows retrieval filtering before returning semantic results.

---

## Retrieval test

A lightweight retrieval test is included in:

```text
retrieval_test_results.md
```

The test supports two modes:

- With OpenAI embeddings: query embeddings are generated and ranked with cosine similarity.
- Without an API key: a simple lexical fallback is used to keep the retrieval test reproducible offline.

The fallback mode is intended only to validate the end-to-end retrieval flow and metadata filtering, not to evaluate semantic retrieval quality.

---

## Production considerations

For a production deployment I would additionally introduce:

- hybrid retrieval (vector + BM25),
- reranking,
- incremental ingestion,
- ingestion lineage tracking,
- monitoring and retrieval evaluation.

## Tradeoffs and Design Decisions

### Why record-based chunking for projects?

Project records are already coherent business entities with strongly related fields (client, methodology, budget, status, dates). Splitting them further would risk fragmenting retrieval context.

### Why ticket-based chunking for interactions?

Support interactions are event-centric units. Preserving the entire interaction improves troubleshooting retrieval quality and avoids losing resolution context.

### Why not use LangChain?

For this assessment I preferred explicit Python pipelines and direct embedding generation to keep the implementation lightweight, transparent and dependency-minimal.

### Why include fallback retrieval?

The assignment should remain reproducible even without external API credentials. For this reason, the retrieval test supports a lightweight lexical fallback mode for offline execution.

### Why metadata filtering by workspace?

The platform is multi-tenant. Retrieval filtering by `workspace_id` reduces cross-tenant leakage risk and improves retrieval relevance.

### Why pseudonymization instead of deletion?

Pseudonymization preserves linkage and analytical utility while reducing direct exposure of sensitive identifiers.