# Design choices

## Goal
The schema separates the operational domain model from the AI retrieval layer. The assignment asks for at least 3NF, but the role is explicitly about building an LLM-queryable knowledge base, so the model also includes ingestion and chunk metadata tables.

## Normalization
The core entities are separated into `workspaces`, `clients`, `projects`, `methodologies`, `panelists`, `support_agents`, `interactions`, and `faq_documents`. Repeating values such as methodology names, clients and managers are modeled as entities rather than duplicated text fields. This avoids update anomalies and supports controlled vocabularies.

## Multi-tenancy
`workspace_id` is part of the key for tenant-owned entities and appears on every queryable domain table. In production I would enforce tenant isolation at multiple levels: application authorization, database row-level security, vector-store metadata filters, and tenant-scoped encryption keys where required.

## RAG-oriented layer
`document_chunks` and `embedding_metadata` deliberately sit outside the 3NF operational model. They are optimized for retrieval, not transaction processing. Each chunk stores source type, source id, workspace id, content hash and metadata, which allows incremental re-embedding and auditability.

## Query optimization
Indexes target likely agent questions: active projects by workspace/status, interactions by issue type/date/project, and chunks by workspace/source. The GIN index on `metadata` supports filterable retrieval if chunks are persisted in PostgreSQL before being pushed to a vector database.

## Data quality assumptions
Some records contain intentionally conflicting values. The ETL keeps the most complete canonical record for duplicates and records known quality issues, instead of silently hiding them. End dates before start dates are flagged because automatically correcting them would be unsafe.

## Tradeoffs and Design Decisions

### Why normalize the schema?

The schema was normalized to reduce duplication, improve consistency and simplify downstream analytics and retrieval workflows.

### Why separate projects, methodologies and interactions?

These entities have different lifecycles and update patterns. Separating them improves extensibility and avoids denormalized duplication.

### Why use workspace_id as tenant boundary?

The platform is designed as multi-tenant. Explicit tenant boundaries simplify governance, filtering and future semantic retrieval isolation.

### Why keep relational modeling even for RAG preparation?

Structured relational data remains useful for:
- governance,
- analytics,
- filtering,
- lineage,
- retrieval metadata enrichment.

The relational layer complements the semantic retrieval layer rather than replacing it.

### Why preserve invalid records instead of deleting them?

Potentially inconsistent records were retained and flagged to preserve traceability and avoid introducing unsupported assumptions during automated cleaning.